import os

from caching.tests.utils import assert_invalidates_model_cache
from webdriver_testing.webdriver_base import WebdriverTestCase
from webdriver_testing.pages.site_pages import video_page
from webdriver_testing.pages.site_pages import create_page
from webdriver_testing.pages.site_pages import video_language_page
from webdriver_testing import data_helpers
from utils.factories import *


class TestCaseFollowing(WebdriverTestCase):
    """TestSuite for video following settings.  """
    NEW_BROWSER_PER_TEST_CASE = False
    FOLLOWING = u'\u2713 Following'
    NOT_FOLLOWING = 'Not Following'


    @classmethod
    def setUpClass(cls):
        super(TestCaseFollowing, cls).setUpClass()
        cls.data_utils = data_helpers.DataHelpers()
        cls.user = UserFactory()
        cls.video_pg = video_page.VideoPage(cls)
        cls.video_language_pg = video_language_page.VideoLanguagePage(cls)
        cls.create_pg = create_page.CreatePage(cls)
        cls.create_pg.open_create_page()
        cls.video = cls.data_utils.create_video_with_subs(cls.user)
        cls.subs_data_dir = os.path.join(os.getcwd(), 'apps', 
            'webdriver_testing', 'subtitle_data')
        cls.create_pg.open_create_page()


    def test_default_submitter_following_video(self):
        """Video submitter is following video by default.

        """
        self.create_pg.log_in(self.user.username, 'password')
        self.create_pg.open_create_page()
        url = 'http://www.youtube.com/watch?v=WqJineyEszo'
        self.create_pg.submit_video(url)
        self.assertEqual(self.FOLLOWING, self.video_pg.follow_text())


    def test_default_subtitler_following_language(self):
        """Subtitler is set to following for language contributed.

        """
        self.video_pg.log_in(self.user.username, 'password')
        tv = self.data_utils.create_video()
        sub_file = os.path.join(self.subs_data_dir, 'Untimed_text.dfxp')
        self.video_pg.open_video_page(tv.video_id)
        self.video_pg.upload_subtitles('English', sub_file)
        self.video_language_pg.open_video_lang_page(tv.video_id, 'en')
        self.assertEqual(self.FOLLOWING, self.video_language_pg.follow_text())


    def test_default_subtitler_not_following_video(self):
        """Not following is setting for Video after contribution subtitles.

        """
        self.video_pg.log_in(self.user.username, 'password')
        tv = self.data_utils.create_video()
        sub_file = os.path.join(self.subs_data_dir, 'Untimed_text.dfxp')
        self.video_pg.open_video_page(tv.video_id)
        self.video_pg.upload_subtitles('English', sub_file)
        self.video_pg.open_video_page(tv.video_id)
        self.assertEqual(self.NOT_FOLLOWING, self.video_pg.follow_text())


    def test_default_not_following_video(self):
        """Non-contributor is not following video by default.

        """
        self.video_pg.log_in(self.user.username, 'password')
        self.video_pg.open_video_page(self.video.video_id)
        self.assertEqual(self.NOT_FOLLOWING, self.video_pg.follow_text())

    def test_default_not_following_language(self):
        """Non-contributor is not following language by default.

        """
        self.video_language_pg.log_in(self.user.username, 'password')
        self.video_language_pg.open_video_lang_page(self.video.video_id, 'en')
        self.assertEqual(self.NOT_FOLLOWING, self.video_pg.follow_text())

    def test_toggle_following_video(self):
        """Turn on and off following for a video
        """
        follower = UserFactory()
        self.video_pg.log_in(follower.username, 'password')
        self.video_pg.open_video_page(self.video.video_id)
        with assert_invalidates_model_cache(self.video): 
            self.video_pg.toggle_follow()
        self.assertEqual(self.FOLLOWING, self.video_pg.follow_text())
        with assert_invalidates_model_cache(self.video):
            self.video_pg.toggle_follow()
        self.assertEqual(self.NOT_FOLLOWING, self.video_pg.follow_text())

    def test_toggle_following_language(self):
        """Turn on / off following for a language.

        """
        user = UserFactory()
        self.video_pg.log_in(user.username, 'password')
        self.video_language_pg.open_video_lang_page(self.video.video_id, 'en')
        self.video_pg.toggle_follow(lang=True)
        self.assertEqual(self.FOLLOWING, self.video_language_pg.follow_text())
        self.video_pg.toggle_follow(lang=True)
        self.assertEqual(self.NOT_FOLLOWING, self.video_language_pg.follow_text())

    def test_follow_video_follows_language(self):
        """Turn on following for a video, follows the languages.

        """
        follower = UserFactory()
        self.video_pg.log_in(follower.username, 'password')
        self.video_pg.open_video_page(self.video.video_id)
        self.video_pg.toggle_follow()
        self.assertEqual(self.FOLLOWING, self.video_pg.follow_text())
        self.video_language_pg.open_video_lang_page(self.video.video_id, 'en')
        self.assertEqual(self.FOLLOWING, self.video_language_pg.follow_text())

    def test_toggle_lang_video_unchanged(self):
        """Turn on / off following for a language does not change video setting.

        """
        user = UserFactory()
        self.video_pg.log_in(user.username, 'password')
        self.video_language_pg.open_video_lang_page(self.video.video_id, 'en')
        self.video_pg.toggle_follow(lang=True)
        self.assertEqual(self.FOLLOWING, self.video_language_pg.follow_text())
        self.video_pg.open_video_page(self.video.video_id)
        self.assertEqual(self.NOT_FOLLOWING, self.video_language_pg.follow_text())
