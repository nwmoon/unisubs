import os
import time

from django.core import mail
from localeurl.templatetags.localeurl_tags import rmlocale
from caching.tests.utils import assert_invalidates_model_cache

from messages import tasks
from webdriver_testing.webdriver_base import WebdriverTestCase
from webdriver_testing.pages.site_pages import video_page
from webdriver_testing.pages.site_pages import create_page
from webdriver_testing.pages.site_pages import video_language_page
from webdriver_testing import data_helpers
from webdriver_testing.data_factories import UserFactory


class TestCaseComments(WebdriverTestCase):
    """TestSuite for video comments. """
    NEW_BROWSER_PER_TEST_CASE = False

    @classmethod
    def setUpClass(cls):
        super(TestCaseComments, cls).setUpClass()
        cls.data_utils = data_helpers.DataHelpers()
        cls.user = UserFactory.create()
        cls.user2 = UserFactory.create()
        cls.video_pg = video_page.VideoPage(cls)
        cls.video_language_pg = video_language_page.VideoLanguagePage(cls)
        cls.video = cls.data_utils.create_video_with_subs(cls.user)

        cls.video_pg.open_video_page(cls.video.video_id)
        cls.video_pg.log_in(cls.user2.username, 'password')
        cls.video_pg.open_video_page(cls.video.video_id)
        cls.video_pg.toggle_follow()


    def test_video_comment_message(self):
        """Message sent on video comment to followers has link to comments tab.

        """
        mail.outbox = []
        self.video_pg.log_in(self.user.username, 'password')
        self.video_pg.open_comments()
        with assert_invalidates_model_cache(self.video):
            self.video_pg.add_comment('This is a great video')
        tasks.send_video_comment_notification.apply()
        msg = str(mail.outbox[-1].message())
        self.assertIn('This is a great video',
                      msg)
        
        self.assertIn('<a href="{0}{1}?tab=comments">'.format(
                self.base_url[:-1], 
                self.video.get_absolute_url()), msg)


    def test_video_lang_comment_message(self):
        """Message sent on video comment to followers has link to comments tab.

        """
        mail.outbox = []
        self.video_pg.log_in(self.user.username, 'password')
        self.video_language_pg.open_video_lang_page(self.video.video_id, 'en')
        self.video_pg.open_comments()
        self.video_pg.add_comment('These are great English subtitles')
        tasks.send_video_comment_notification.apply()
        time.sleep(4)
        self.video_pg.log_in(self.user2.username, 'password')
        self.video_language_pg.open_video_lang_page(self.video.video_id, 'en')
        msg = str(mail.outbox[-1].message())
        self.assertIn('These are great English subtitles',
                      msg)
        self.assertIn('<a href="{0}{1}?tab=comments">'.format(
                self.base_url[:-1], 
                rmlocale(self.video.subtitle_language('en').get_absolute_url())), msg)
