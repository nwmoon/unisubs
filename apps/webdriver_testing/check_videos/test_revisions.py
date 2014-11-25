import os
import string

from django.core import mail
from django.contrib.sites.models import Site

from utils.factories import *
from localeurl.templatetags.localeurl_tags import rmlocale
from webdriver_testing.webdriver_base import WebdriverTestCase
from webdriver_testing.pages.site_pages import video_page
from webdriver_testing.pages.site_pages import diffing_page
from webdriver_testing.pages.site_pages import video_language_page
from webdriver_testing import data_helpers


class TestCaseRevisionNotifications(WebdriverTestCase):
    NEW_BROWSER_PER_TEST_CASE = False

    @classmethod
    def setUpClass(cls):
        super(TestCaseRevisionNotifications, cls).setUpClass()
        cls.data_utils = data_helpers.DataHelpers()
        cls.user = UserFactory()
        cls.video_pg = video_page.VideoPage(cls)
        cls.diffing_pg = diffing_page.DiffingPage(cls)
        cls.video_language_pg = video_language_page.VideoLanguagePage(cls)
        cls.subs_path = os.path.dirname(os.path.abspath(__file__))


    def test_notify_contributor(self):
        """Subtitle contributor gets an email when new revision added.

        """
        video = self.data_utils.create_video()
        self.video_pg.open_video_page(video.video_id)

        self.video_pg.log_in(self.user.username, 'password')
        rev1 = os.path.join(self.subs_path, 'rev1.dfxp')
        self.video_pg.open_video_page(video.video_id)
        self.video_pg.upload_subtitles('English', rev1)
        sl = video.subtitle_language('en')
        v1 = sl.get_tip().id
        sl.clear_tip_cache()

        user2 = UserFactory()
        self.video_pg.log_in(user2.username, 'password')
        rev2 = os.path.join(self.subs_path, 'rev2.dfxp')
        self.video_pg.open_video_page(video.video_id)
        mail.outbox = []
        self.video_pg.upload_subtitles('English', rev2)
        email_to = mail.outbox[-1].to     
        msg = str(mail.outbox[-1].message())
        v2 = sl.get_tip().id
        diffing_page = ('videos/diffing/{0}/{1}/'.format(v2, v1))
        self.video_pg.open_page(diffing_page)
        self.assertIn(diffing_page, msg)
        self.assertIn(self.user.email, email_to)

    def test_notify_language_follower(self):
        """Language follower gets an email when new revision added.

        """
        video = self.data_utils.create_video()

        self.video_pg.open_video_page(video.video_id)
        self.video_pg.log_in(self.user.username, 'password')
        rev1 = os.path.join(self.subs_path, 'rev1.dfxp')
        self.video_pg.open_video_page(video.video_id)
        self.video_pg.upload_subtitles('English', rev1)

        follower = UserFactory()
        self.video_language_pg.open_video_lang_page(video.video_id, 'en')
        self.video_pg.log_in(follower.username, 'password')
        self.video_pg.page_refresh()
        self.video_pg.toggle_follow()
        mail.outbox = []
        self.video_pg.log_in(self.user.username, 'password')
        rev2 = os.path.join(self.subs_path, 'rev2.dfxp')
        self.video_pg.open_video_page(video.video_id)
        self.video_pg.upload_subtitles('English', rev2)

        email_to = mail.outbox[-1].to     
        msg = str(mail.outbox[-1].message())
        self.assertIn(follower.email, email_to)

        urlstart = 'http://' + Site.objects.get_current().domain
        lang = video.subtitle_language('en')
        # combine whitespace and replace it with " " for easier string
        # comparisons
        msg = ' '.join(msg.split())
        correct_message = string.Template(
            '<b><a href="${lang_url}">${lang_name} subtitles</a></b> '
            'to video <b><a href="${video_url}">${video_name}</a></b> '
            'were changed by <b><a href="${user_url}">${user_name}</a></b>. '
            'These changes went live immediately. 33% of the timing was '
            'changed.').substitute({
                'lang_url': urlstart + rmlocale(lang.get_absolute_url()),
                'lang_name': lang.get_language_code_display(),
                'video_url': urlstart + rmlocale(video.get_absolute_url()),
                'video_name': video.title_display(),
                'user_url': urlstart + rmlocale(self.user.get_absolute_url()),
                'user_name': self.user.username,
            })

        self.assertIn(follower.email, email_to)
        self.assertIn(urlstart + rmlocale(video.get_absolute_url()), msg)

    def test_notify_video_follower_revisions(self):
        """Video follower gets an email when new revision added.

        """
        video = self.data_utils.create_video()
        follower = UserFactory()
        self.video_pg.open_video_page(video.video_id)
        self.video_pg.log_in(follower.username, 'password')
        self.video_pg.page_refresh()
        self.video_pg.toggle_follow()
        mail.outbox = []

        self.video_pg.open_video_page(video.video_id)
        self.video_pg.log_in(self.user.username, 'password')
        self.video_pg.page_refresh()
        rev1 = os.path.join(self.subs_path, 'rev1.dfxp')
        self.video_pg.open_video_page(video.video_id)
        self.video_pg.upload_subtitles('English', rev1)

        rev2 = os.path.join(self.subs_path, 'rev2.dfxp')
        self.video_pg.open_video_page(video.video_id)
        self.video_pg.upload_subtitles('English', rev2)
        self.video_pg.page_refresh()

        email_to = mail.outbox[-1].to     
        msg = str(mail.outbox[-1].message())
        self.assertIn(follower.email, email_to)

    def test_notify_video_follower_initial(self):
        """Video follower gets an email when first revision of subtitles added.

        """
        self.skipTest('needs https://unisubs.sifterapp.com/issues/2220 fixed')
        video = self.data_utils.create_video()
        follower = UserFactory()
        self.video_pg.open_video_page(video.video_id)
        self.video_pg.log_in(follower.username, 'password')
        self.video_pg.page_refresh()
        self.video_pg.toggle_follow()
        self.assertEqual(self.FOLLOWING, self.video_pg.follow_text())
        mail.outbox = []

        self.video_pg.open_video_page(video.video_id)
        self.video_pg.log_in(self.user.username, 'password')
        self.video_pg.page_refresh()
        rev1 = os.path.join(self.subs_path, 'rev1.dfxp')
        self.video_pg.open_video_page(video.video_id)
        self.video_pg.upload_subtitles('English', rev1)
        self.assertEqual(1, len(mail.outbox))
        email_to = mail.outbox[-1].to     
        msg = str(mail.outbox[-1].message())
        self.assertIn(follower.email, email_to)


class TestCaseRevisionEdits(WebdriverTestCase):
    NEW_BROWSER_PER_TEST_CASE = False

    @classmethod
    def setUpClass(cls):
        super(TestCaseRevisionEdits, cls).setUpClass()
        cls.data_utils = data_helpers.DataHelpers()
        cls.video_lang_pg = video_language_page.VideoLanguagePage(cls)
        cls.video_pg = video_page.VideoPage(cls)
        cls.user1 = UserFactory()
        cls.user2 = UserFactory()
        cls.subs_dir = os.path.join(os.getcwd(), 'apps', 'webdriver_testing', 
                                    'subtitle_data')  

    def _add_video(self):
        video = self.data_utils.create_video()
        return video

    def _upload_en_draft(self, video, subs, user, complete=False):
        data = {'language_code': 'en',
                     'video': video.pk,
                     'primary_audio_language_code': 'en',
                     'draft': open(subs),
                     'complete': int(complete),
                     'is_complete': complete,
                    }
        self.data_utils.upload_subs(user, **data)

    def _create_two_incomplete(self, video, user):
        rev1 = os.path.join(self.subs_dir, 'Timed_text.en.srt')
        rev2 = os.path.join(self.subs_dir, 'Timed_text.rev2.en.srt')

        self._upload_en_draft(video, rev1, user)
        en = video.subtitle_language('en')
        en_v1 = en.get_tip()
        self._upload_en_draft(video, rev2, user)
        en_v2 = en.get_tip()
        return en_v1, en_v2

    def _create_complete_rev(self, video, user):
        rev1 = os.path.join(self.subs_dir, 'Timed_text.en.srt')
        rev2 = os.path.join(self.subs_dir, 'Timed_text.rev2.en.srt')

        self._upload_en_draft(video, rev1, user)
        en = video.subtitle_language('en')
        en_v1 = en.get_tip()
        en.clear_tip_cache() 
        self._upload_en_draft(video, rev2, user, complete=True)
        en_v2 = en.get_tip()
        en.clear_tip_cache() 
        return en_v1, en_v2

    def test_rollback(self):
        """Rollback completed rev to incomplete, lang is complete.

        """
        video = self._add_video()
        v1, _ = self._create_complete_rev(video, self.user1)

        self.video_lang_pg.open_video_lang_page(video.video_id, 'en')
        self.video_lang_pg.log_in(self.user1.username, 'password')

        self.video_lang_pg.open_page(v1.get_absolute_url())
        self.assertTrue(self.video_lang_pg.rollback())
        en = video.subtitle_language('en')
        en.clear_tip_cache() 
        en_v3 = en.get_tip()
        
        self.video_lang_pg.open_page(en_v3.get_absolute_url())
        self.assertIn('Revision 3', self.video_lang_pg.view_notice())

    def test_diffing_page_rollback(self):
        """Rollback completed rev to incomplete, lang is complete.

        """
        video = self._add_video()
        v1, v2 = self._create_complete_rev(video, self.user1)

        self.video_lang_pg.open_video_lang_page(video.video_id, 'en')
        self.video_lang_pg.log_in(self.user1.username, 'password')

        self.video_lang_pg.open_page(v1.get_absolute_url())
        self.assertTrue(self.video_lang_pg.rollback())
        en = video.subtitle_language('en')
        en.clear_tip_cache() 
        en_v3 = en.get_tip()
 
        self.video_lang_pg.open_page(en_v3.get_absolute_url())
        self.assertIn('Revision 3', self.video_lang_pg.view_notice())


    def test_rollback_incomplete(self):
        """Rollback incomplete version to incomplete, remains incomplete.

        """
        video = self._add_video()
        v1, _ = self._create_two_incomplete(video, self.user1)

        self.video_lang_pg.open_video_lang_page(video.video_id, 'en')
        self.video_lang_pg.log_in(self.user1.username, 'password')

        self.video_lang_pg.open_page(v1.get_absolute_url())
        self.assertTrue(self.video_lang_pg.rollback())
        en = video.subtitle_language('en')
        en.clear_tip_cache() 
        en_v3 = en.get_tip()
        
        self.video_lang_pg.open_page(en_v3.get_absolute_url())
        self.assertIn('Revision 3', self.video_lang_pg.view_notice())


    def test_rollback_2nd_user(self):
        """User can rollback videos created by another user.

        """
        video = self._add_video()
        v1, _ = self._create_two_incomplete(video, self.user1)

        self.video_lang_pg.open_video_lang_page(video.video_id, 'en')
        self.video_lang_pg.log_in(self.user2.username, 'password')

        self.video_lang_pg.open_page(v1.get_absolute_url())
        self.assertTrue(self.video_lang_pg.rollback())
        en = video.subtitle_language('en')
        en.clear_tip_cache() 
        en_v3 = en.get_tip()
        
        self.video_lang_pg.open_page(en_v3.get_absolute_url())
        self.assertIn('Revision 3', self.video_lang_pg.view_notice())



    def test_edit_incomplete_2nd_user(self):
        """User can edit incomplete subtitles created by another user.

        """
        video = self._add_video()
        v1, v2 = self._create_two_incomplete(video, self.user1)

        self.video_lang_pg.open_video_lang_page(video.video_id, 'en')
        self.video_lang_pg.log_in(self.user2.username, 'password')

        self.video_lang_pg.open_page(v2.get_absolute_url())
        self.assertEqual('active', self.video_lang_pg.edit_subtitles_active())

    def test_edit_complete_2nd_user(self):
        """User can edit complete subtitles created by another user.

        """
        video = self._add_video()
        _, v2 = self._create_complete_rev(video, self.user1)

        self.video_lang_pg.open_video_lang_page(video.video_id, 'en')
        self.video_lang_pg.log_in(self.user2.username, 'password')

        self.video_lang_pg.open_page(v2.get_absolute_url())
        self.assertEqual('active', self.video_lang_pg.edit_subtitles_active())

    def test_edit_subtitles(self):
        """User sees edit subtitles button on language rev pages.
        """
        video = self._add_video()
        v1, v2 = self._create_complete_rev(video, self.user1)

        self.video_lang_pg.open_video_lang_page(video.video_id, 'en')
        self.video_lang_pg.log_in(self.user1.username, 'password')

        self.video_lang_pg.open_page(v2.get_absolute_url())
        self.assertEqual('active', self.video_lang_pg.edit_subtitles_active())
        self.video_lang_pg.open_page(v1.get_absolute_url())
        self.assertEqual('active', self.video_lang_pg.edit_subtitles_active())


