import collections
import functools
import json
import os
import urlparse

from celery.task import Task
from django.conf import settings
from django.core.cache import cache
from nose.plugins import Plugin
from nose.tools import assert_equal
from xvfbwrapper import Xvfb
import mock
import mock
import requests
import utils.youtube

import optionalapps

def reload_obj(model_obj):
    return model_obj.__class__.objects.get(pk=model_obj.pk)

REQUEST_CALLBACKS = []

class Response(dict):
    status = 200
    content = ""

    def __getitem__(self, key):
        return getattr(self, key)

def reset_requests():
    global REQUEST_CALLBACKS
    REQUEST_CALLBACKS = []

def store_request_call(url, **kwargs):
    method = kwargs.pop('method', None)
    data = urlparse.parse_qs(kwargs.pop("body", ""))
    for k,v in data.items():
        data[k] = v[0]
    global REQUEST_CALLBACKS
    if not '/solr' in url:
        REQUEST_CALLBACKS.append([url, method, data])
    return Response(), ""

class TestCaseMessagesMixin(object):
    def _getMessagesCount(self, response, level=None):
        messages =  response.context['messages']
        if level:
            actual_num = len([x for x in messages if x.level==level])
        else:
            actual_num = len(messages)

        return actual_num

    def assertMessageCount(self, response, expect_num, level=None):
        """
        Asserts that exactly the given number of messages have been sent.
        """
        actual_num = self._getMessagesCount(response, level=level)
        if actual_num != expect_num:
            self.fail('Message count was %d, expected %d' %
                    (actual_num, expect_num)
                )

    def assertMessageEqual(self, response, text):
        """
        Asserts that the response includes the message text.
        """

        messages = [m.message for m in response.context['messages']]

        if text not in messages:
            self.fail(
                'No message with text "%s", messages were: %s' % 
                    (text, messages)
                )

    def assertMessageNotEqual(self, response, text):
        """
        Asserts that the response does not include the message text.
        """

        messages = [m.message for m in response.context['messages']]

        if text in messages:
            self.fail(
                'Message with text "%s" found, messages were: %s' % 
                    (text, messages)
                )

save_thumbnail_in_s3 = mock.Mock()
update_team_video = mock.Mock()
update_search_index = mock.Mock()

test_video_info = utils.youtube.VideoInfo(
    'test-channel-id', 'test-title', 'test-description', 60,
    'http://example.com/youtube-thumb.png')
youtube_get_video_info = mock.Mock(return_value=test_video_info)
youtube_get_user_info = mock.Mock(return_value=test_video_info)
youtube_get_new_access_token = mock.Mock(return_value='test-access-token')
youtube_revoke_auth_token = mock.Mock()
youtube_update_video_description = mock.Mock()
url_exists = mock.Mock(return_value=True)

current_locks = set()
acquire_lock = mock.Mock(
    side_effect=lambda c, name: current_locks.add(name))
release_lock = mock.Mock(
    side_effect=lambda c, name: current_locks.remove(name))
invalidate_widget_video_cache = mock.Mock()
update_subtitles = mock.Mock()
delete_subtitles = mock.Mock()
update_all_subtitles = mock.Mock()
fetch_subs_task = mock.Mock()
import_videos_from_feed = mock.Mock()
get_language_facet_counts = mock.Mock(return_value=([], []))

class MonkeyPatcher(object):
    """Replace a functions with mock objects for the tests.
    """
    def patch_functions(self):
        # list of (function, mock object tuples)
        patch_info = [
            ('videos.tasks.save_thumbnail_in_s3', save_thumbnail_in_s3),
            ('teams.tasks.update_one_team_video', update_team_video),
            ('utils.celery_search_index.update_search_index',
             update_search_index),
            ('utils.youtube.get_video_info', youtube_get_video_info),
            ('utils.youtube.get_user_info', youtube_get_user_info),
            ('utils.youtube.get_new_access_token',
             youtube_get_new_access_token),
            ('utils.youtube.revoke_auth_token', youtube_revoke_auth_token),
            ('utils.youtube.update_video_description',
             youtube_update_video_description),
            ('utils.applock.acquire_lock', acquire_lock),
            ('utils.applock.release_lock', release_lock),
            ('utils.http.url_exists', url_exists),
            ('widget.video_cache.invalidate_cache',
             invalidate_widget_video_cache),
            ('externalsites.tasks.update_subtitles', update_subtitles),
            ('externalsites.tasks.delete_subtitles', delete_subtitles),
            ('externalsites.tasks.update_all_subtitles', update_all_subtitles),
            ('externalsites.tasks.fetch_subs', fetch_subs_task),
            ('videos.tasks.import_videos_from_feed', import_videos_from_feed),
            ('search.forms._get_language_facet_counts',
             get_language_facet_counts)
        ]
        self.patches = []
        self.initial_side_effects = {}
        for func_name, mock_obj in patch_info:
            self.start_patch(func_name, mock_obj)

    def start_patch(self, func_name, mock_obj):
        patch = mock.patch(func_name, mock_obj)
        mock_obj = patch.start()
        self.setup_run_original(mock_obj, patch)
        self.initial_side_effects[mock_obj] = mock_obj.side_effect
        self.patches.append(patch)

    def setup_run_original(self, mock_obj, patch):
        mock_obj.original_func = patch.temp_original
        mock_obj.run_original = functools.partial(self.run_original,
                                                  mock_obj)
        mock_obj.run_original_for_test = functools.partial(
            self.run_original_for_test, mock_obj)

    def run_original(self, mock_obj):
        rv = [mock_obj.original_func(*args, **kwargs)
                for args, kwargs in mock_obj.call_args_list]
        if isinstance(mock_obj.original_func, Task):
            # for celery tasks, also run the delay() and apply() methods
            rv.extend(mock_obj.original_func.delay(*args, **kwargs)
                      for args, kwargs in mock_obj.delay.call_args_list)
            rv.extend(mock_obj.original_func.apply(*args, **kwargs)
                      for args, kwargs in mock_obj.apply.call_args_list)

        return rv

    def run_original_for_test(self, mock_obj):
        # set side_effect to be the original function.  We will undo this when
        # reset_mocks() is called at the end of the test
        mock_obj.side_effect = mock_obj.original_func

    def unpatch_functions(self):
        for patch in self.patches:
            patch.stop()

    def reset_mocks(self):
        for mock_obj, side_effect in self.initial_side_effects.items():
            mock_obj.reset_mock()
            # reset_mock doesn't reset the side effect, and we wouldn't want
            # it to anyways since we only want to reset side effects that the
            # unittests set.  So we save side_effect right after we create the
            # mock and restore it here
            mock_obj.side_effect = side_effect


_xvfb = None
def start_xvfb():
    global _xvfb
    if _xvfb is None:
        _xvfb = Xvfb(width=1920, height=1080)
        _xvfb.start()

def stop_xvfb():
    global _xvfb
    if _xvfb is not None:
        _xvfb.stop()
        _xvfb = None

class UnisubsTestPlugin(Plugin):
    name = 'Amara Test Plugin'

    def __init__(self):
        Plugin.__init__(self)
        self.patcher = MonkeyPatcher()
        self.directories_to_skip = set([
            os.path.join(settings.PROJECT_ROOT, 'libs'),
        ])
        self.vdisplay = None
        self.include_webdriver_tests = False

    def options(self, parser, env=os.environ):
        parser.add_option("--with-webdriver",
                          action="store_true", dest="webdriver",
                          default=False, help="Enable webdriver tests")

    def configure(self, options, conf):
        # force enabled to always be True.  This only gets loaded because we
        # manually specify the plugin in the dev_settings_test.py file.  So
        # it's pretty safe to assume the user wants us enabled.
        self.enabled = True
        self.include_webdriver_tests = options.webdriver

    def begin(self):
        self.patcher.patch_functions()

    def finalize(self, result):
        self.patcher.unpatch_functions()
        stop_xvfb()

    def afterTest(self, test):
        self.patcher.reset_mocks()
        cache.clear()

    def wantDirectory(self, dirname):
        if dirname in self.directories_to_skip:
            return False
        if not self.include_webdriver_tests and 'webdriver' in dirname:
            return False
        if dirname == os.path.join(settings.PROJECT_ROOT, 'apps'):
            # force the tests from the apps directory to be loaded, even
            # though it's not a package
            return True
        if dirname in optionalapps.get_repository_paths():
            # same thing for optional app repos
            return True
        return None

def patch_for_test(spec):
    """Use mock to patch a function for the test case.

    Use this to decorate a TestCase test or setUp method.  It will call
    TestCase.addCleanup() so that the the patch will stop at the once the test
    is complete.  It will pass in the mock object used for the patch to the
    function.

    Example:

    class FooTest(TestCase):
        @patch_for_test('foo.bar')
        def setUp(self, mock_foo):
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            mock_obj = mock.Mock()
            patcher = mock.patch(spec, mock_obj)
            patcher.start()
            self.addCleanup(patcher.stop)
            return func(self, mock_obj, *args, **kwargs)
        return wrapper
    return decorator
patch_for_test.__test__ = False

ExpectedRequest = collections.namedtuple(
    "ExpectedRequest", "method url params data headers body status_code")

class RequestsMocker(object):
    """Mock code that uses the requests module

    This object patches the various network functions of the requests module
    (get, post, put, delete) with mock functions.  You tell it what requests
    you expect, and what responses to return.

    Example:

    mocker = RequestsMocker()
    mocker.expect_request('get', 'http://example.com/', body="foo")
    mocker.expect_request('post', 'http://example.com/form',
        data={'foo': 'bar'}, body="Form OK")
    with mocker:
        function_to_test()
    """

    def __init__(self):
        self.expected_requests = []

    def expect_request(self, method, url, params=None, data=None,
                       headers=None, body='', status_code=200):
        self.expected_requests.append(
            ExpectedRequest(method, url, params, data, headers, body,
                            status_code))

    def __enter__(self):
        self.setup_patchers()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.unpatch()
        if exc_type is None:
            self.check_no_more_expected_calls()

    def setup_patchers(self):
        self.patchers = []
        for method in ('get', 'post', 'put', 'delete', 'request'):
            mock_obj = mock.Mock()
            mock_obj.side_effect = getattr(self, 'mock_%s' % method)
            patcher = mock.patch('requests.%s' % method, mock_obj)
            patcher.start()
            self.patchers.append(patcher)

    def unpatch(self):
        for patcher in self.patchers:
            patcher.stop()
        self.patchers = []

    def mock_get(self, url, params=None, data=None, headers=None):
        return self.check_request('get', url, params, data, headers)

    def mock_post(self, url, params=None, data=None, headers=None):
        return self.check_request('post', url, params, data, headers)

    def mock_put(self, url, params=None, data=None, headers=None):
        return self.check_request('put', url, params, data, headers)

    def mock_delete(self, url, params=None, data=None, headers=None):
        return self.check_request('delete', url, params, data, headers)

    def mock_request(self, method, url, params=None, data=None, headers=None):
        return self.check_request(method.lower(), url, params, data, headers)

    def check_request(self, method, url, params, data, headers):
        try:
            expected = self.expected_requests.pop(0)
        except IndexError:
            raise AssertionError("RequestsMocker: No more calls expected, "
                                 "but got %s %s %s %s" % 
                                 (method, url, params, data, headers))

        assert_equal(method, expected.method)
        assert_equal(url, expected.url)
        assert_equal(params, expected.params)
        if (expected.headers is not None and
            expected.headers.get('content-type') == 'application/json'):
            assert_equal(json.loads(data), json.loads(expected.data))
        else:
            assert_equal(data, expected.data)
        assert_equal(headers, expected.headers)
        request = requests.Request(method=method, url=url, params=params,
                                   data=data, headers=headers)
        return self.make_response(request, expected.status_code, expected.body)

    def make_response(self, request, status_code, body):
        response = requests.Response()
        response._content = body
        response.status_code = status_code
        response.request = request
        return response

    def check_no_more_expected_calls(self):
        if self.expected_requests:
            raise AssertionError(
                "leftover expected calls:\n" +
                "\n".join('%s %s %s' % (er.method, er.url, er.params)
                          for er in self.expected_requests))
