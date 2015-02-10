import codecs
import os
from utils.factories import *
from webdriver_testing.webdriver_base import WebdriverTestCase
from webdriver_testing.pages.site_pages import video_page
from webdriver_testing.pages.site_pages import video_language_page
from webdriver_testing import data_helpers
from webdriver_testing.pages.editor_pages import subtitle_editor


class TestCaseViewSubtitles(WebdriverTestCase):
    """TestSuite for download subtitles from the video's lanugage page   """
    NEW_BROWSER_PER_TEST_CASE = False

    @classmethod
    def setUpClass(cls):
        super(TestCaseViewSubtitles, cls).setUpClass()
        cls.data_utils = data_helpers.DataHelpers()
        cls.user = UserFactory()
        cls.video_pg = video_page.VideoPage(cls)
        cls.video_language_pg = video_language_page.VideoLanguagePage(cls)
        cls.subs_dir = os.path.join(os.getcwd(), 'apps', 
            'webdriver_testing', 'subtitle_data')
        cls.video = VideoFactory()
        #Upload original language de
        complete = True
        data = {'language_code': 'de',
                'video': cls.video.pk,
                'primary_audio_language_code': 'de',
                'draft': open(os.path.join(cls.subs_dir, 'Timed_text.en.srt')), 
                'complete': int(complete)
                }
        cls.data_utils.upload_subs(cls.user, **data)
       
        #Upload sv, translated from de, complete
        data = {'language_code': 'sv',
                'video': cls.video.pk,
                'translated_from': 'de',
                'draft': open(os.path.join(cls.subs_dir, 'Timed_text.sv.dfxp')),
                'is_complete': complete,
                'complete': int(complete)
                }
        cls.data_utils.upload_subs(cls.user, **data)
        complete = False
        #Upload ar, translated from de, incomplete
        data = {'language_code': 'ar',
                'video': cls.video.pk,
                'draft': open(os.path.join(cls.subs_dir, 'Timed_text.ar.xml')),
                'is_complete': complete,
                'complete': int(complete)
                }
        cls.data_utils.upload_subs(cls.user, **data)
        #Upload hu, translated from sv, incomplete
        data = {'language_code': 'hu',
                'video': cls.video.pk,
                'translated_from': 'sv',
                'draft': open(os.path.join(cls.subs_dir, 'Timed_text.hu.ssa')),
                'is_complete': complete,
                'complete': int(complete)
                }
        cls.data_utils.upload_subs(cls.user, **data)
        cls.video_pg.open_video_page(cls.video.video_id)
        

    def setUp(self):
        self.video_pg.open_video_page(self.video.video_id)


    def test_labeled_original(self):
        """Subtitles matching primary audio lang value tagged as original.

        """
        de_tag, _ = self.video_pg.language_status('German')
        self.assertEqual('original', de_tag)

    def test_labeled_incomplete__translation(self):
        """"Translation, with incomplete subtitles displays incomplete tag.

        """
        hu_tag, _ = self.video_pg.language_status('Hungarian')
        self.assertEqual('incomplete', hu_tag)

    def test_labeled_incomplete__forked(self):
        """Forked, incomplete subtitles display incomplete tag.

        """
        ar_tag, _ = self.video_pg.language_status('Arabic')
        self.assertEqual('incomplete', ar_tag)

    def test_status_img__original_complete(self):
        """Orignal lang complete, shows complete status button.

        """
        _, de_status = self.video_pg.language_status('German')
        self.assertIn('status-complete', de_status)

    def test_status_img__translation_complete(self):
        """Translation lang complete, shows complete status button.

        """
        _, sv_status = self.video_pg.language_status('Swedish')
        self.assertIn('status-complete', sv_status)


    def test_status_img__forked_incomplete(self):
        """Forked, incomplete subs display incomplete status button.

        """
        _, ar_status = self.video_pg.language_status('Arabic')
        self.assertIn('status-incomplete', ar_status)


    def test_no_primary_audio_lang(self):
        """Language list displays when no subs for primary audio lang exists.

        """
        vid = VideoFactory()

        #Upload en, primary audio = de
        complete = True
        data = {'language_code': 'en',
                'video': vid.pk,
                'primary_audio_language_code': 'de',
                'draft': open(os.path.join(self.subs_dir, 'Timed_text.en.srt')), 
                'is_complete': complete,
                'complete': int(complete)
                }
        self.data_utils.upload_subs(self.user, **data)
        #Upload sv, forked
        data = {'language_code': 'sv',
                'video': vid.pk,
                'draft': open(os.path.join(self.subs_dir, 'Timed_text.sv.dfxp')),
                'is_complete': complete,
                'complete': int(complete)
                }
        self.data_utils.upload_subs(self.user, **data)
        self.video_pg.open_video_page(vid.video_id)
        _, en_status = self.video_pg.language_status('English')
        self.assertIn('status-complete', en_status, 
            'ref: https://unisubs.sifterapp.com/issues/2350')


