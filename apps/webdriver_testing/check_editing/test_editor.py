#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from django.test import TestCase
from django.core import management
import time

from datetime import datetime as dt

from videos.models import Video
from utils.factories import *
from webdriver_testing.webdriver_base import WebdriverTestCase
from webdriver_testing import data_helpers
from webdriver_testing.pages.site_pages import video_page
from webdriver_testing.pages.site_pages import editor_page

class TestCaseEditing(WebdriverTestCase):

    NEW_BROWSER_PER_TEST_CASE = False

    @classmethod
    def setUpClass(cls):
        super(TestCaseEditing, cls).setUpClass()
        
        cls.editor_pg = editor_page.EditorPage(cls)
        cls.data_utils = data_helpers.DataHelpers()
        cls.video_pg = video_page.VideoPage(cls)
        cls.user = UserFactory.create()
        cls.video_pg.open_page('auth/login/')
        cls.video_pg.log_in(cls.user.username, 'password')
        data = { 'video_url': 'http://www.youtube.com/watch?v=5CKwCfLUwj4',
                 'title': 'Open Source Philosophy' }
        url_part = 'videos/'
        r = cls.data_utils.make_request(cls.user, 'post', url_part, **data)
        cls.video, _  = Video.get_or_create_for_url(
                    'http://www.youtube.com/watch?v=5CKwCfLUwj4')
        cls.data_utils.add_subs(video=cls.video) 
        langs = ['en', 'da', 'ar', 'tr', 'zh-cn', 'nl']
        for lc in langs:
            defaults = {
                        'video': cls.video,
                        'language_code': lc,
                        'complete': True,
                        'visibility': 'public',
                        'committer': cls.user,
                        'subtitles': ('apps/webdriver_testing/subtitle_data/'
                                     'Open Source Philosophy.%s.dfxp' % lc)
                   }
            cls.data_utils.add_subs(**defaults)

    def tearDown(self):
        #Exit editor when test ends
        try:
            self.editor_pg.exit()
        except:
            pass


    def test_reference_lang_original(self):
        """Default reference lang for transcription is the same lang. """

        self.editor_pg.open_editor_page(self.video.video_id, 'en')
        self.assertEqual('English', self.editor_pg.selected_ref_language())


    def test_reference_lang_translation(self):
        """Default reference lang for translation is primary_audio lang. """
        self.editor_pg.open_editor_page(self.video.video_id, 'da')
        self.assertEqual('English', self.editor_pg.selected_ref_language())


    def test_reference_text_displayed(self):
        """Reference language text updated when language and version changed.

        """
        self.editor_pg.open_editor_page(self.video.video_id, 'da')
        self.assertEqual('Tangible problems.', 
                         self.editor_pg.reference_text(1))
        self.editor_pg.select_ref_language('Danish')
        self.assertEqual('Konkrete problemer', 
                         self.editor_pg.reference_text(1))
        self.editor_pg.select_ref_language('Turkish')
        self.assertEqual(u'\xe7\xf6zmekte olan g\xfcc\xfcn\xfc hep hissettim.', 
                         self.editor_pg.reference_text(3))
        self.editor_pg.select_ref_version('Version 1')
        self.editor_pg.select_ref_language('Chinese, Simplified')
        self.logger.info(self.editor_pg.reference_text(3))
        self.assertEqual(u'可以来解决各种迫切的问题。', 
                         self.editor_pg.reference_text(3))


    def test_reference_private_versions(self):
        """Language not displayed if not visible to user

        """
        sl_tr = self.video.subtitle_language('tr').get_tip(full=True)
        sl_tr.visibility_override = 'private'
        sl_tr.save()
        self.editor_pg.open_editor_page(self.video.video_id, 'en')
        langs = self.editor_pg.reference_languages()
        self.logger.info(langs)
        self.assertNotIn('Turkish', langs)


    def test_selected_subs_on_video(self):
        """Clicking a working subs displays it on the video."""
        self.editor_pg.open_editor_page(self.video.video_id, 'en')
        sub_text, _ = self.editor_pg.click_working_sub_line(3)
        self.assertEqual(sub_text, self.editor_pg.sub_overlayed_text())


    def test_remove_active_subtitle(self):
        """Remove the selected subtitle line.
 
        from i2441
        """
        self.editor_pg.open_editor_page(self.video.video_id, 'en')
        subtext = self.editor_pg.working_text()
        removed_text = self.editor_pg.remove_active_subtitle(3)
        self.assertEqual(subtext[2], removed_text)
        subtext = self.editor_pg.working_text()
        self.assertNotEqual(subtext[2], removed_text)

        

    def test_working_language(self):
        self.editor_pg.open_editor_page(self.video.video_id, 'en')
        self.assertEqual(u'Editing English\u2026', self.editor_pg.working_language())
        self.editor_pg.open_editor_page(self.video.video_id, 'tr')
        self.assertEqual(u'Editing Turkish\u2026', self.editor_pg.working_language())


    def test_page_title(self):
        self.editor_pg.open_editor_page(self.video.video_id, 'en')
        self.assertEqual('Open Source Philosophy',
                         self.editor_pg.video_title())



    def test_info_tray(self):
        """Info tray displays start, stop, char count, chars/second."""
        self.editor_pg.open_editor_page(self.video.video_id, 'en')
        sub_info = (self.editor_pg.subtitle_info(4))
        self.assertEqual('0:09.24', sub_info['Start'], 
                         'start time is not expected value')
        self.assertEqual('0:12.84', sub_info['End'], 
                         'stop time is not expected value')
        self.assertEqual('71', sub_info['Characters'], 
                         'character count is not expected value')
        self.assertEqual('19.7', sub_info['Chars/sec'], 
                         'character rate is not expected value')


    def test_info_tray_multiline(self):
        """Info tray displays start, stop, char count, chars/second."""
        self.editor_pg.open_editor_page(self.video.video_id, 'en')
        self.editor_pg.click_working_sub_line(2)
        sub_info  = self.editor_pg.subtitle_info(2, True)
        self.logger.info(sub_info)
        self.assertEqual('36', sub_info['Line 1'], 
                         'Line 1 is not expected value')
        self.assertEqual('36', sub_info['Line 2'], 
                         'Line 2 is not expected value')
        self.assertEqual('72', sub_info['Characters'], 
                         'character count is not expected value')


    def test_info_tray_char_updates(self):
        """Info tray character counts updates dynamically"""
        self.editor_pg.open_editor_page(self.video.video_id, 'en')
        self.editor_pg.edit_sub_line('12345 chars', 1, enter=False)
        sub_info  = (self.editor_pg.subtitle_info(1, active=True))
        self.assertEqual('11', sub_info['Characters'], 
                         'character count is not expected value')



    def test_add_lines_to_end(self):
        """Add sub to the end of the subtitle list, enter adds new active sub."""
        self.logger.info(Video.objects.all())
        self.editor_pg.open_editor_page(self.video.video_id, 'nl')

        subs = ['third to last', 'pentulitmate subtitle', 'THE END']
        self.editor_pg.add_subs_to_the_end(subs)
        new_subs = self.editor_pg.working_text()[-3:]
        self.assertEqual(subs, new_subs)


    def test_one_version(self):
        """Video with only 1 version displays subs in working section.

        """
        self.logger.info('checking subs on en-original')
        self.editor_pg.open_editor_page(self.video.video_id, 'en')
        self.assertEqual(101, len(self.editor_pg.working_text()))
        self.assertEqual(101, len(self.editor_pg.reference_text()))

    def test_sync_subs(self):
        """Sync subtitles """
        self.editor_pg.open_editor_page(self.video.video_id, 'nl')
        self.editor_pg.start_sync()
        time.sleep(2)
        self.editor_pg.buffer_up_subs()
        self.editor_pg.toggle_playback()
        self.editor_pg.sync(8, 6)
        self.editor_pg.toggle_playback()
        self.editor_pg.save("Resume Editing")
        self.editor_pg.page_refresh()
        times = self.editor_pg.start_times()
        times = [x for x in times if x != '--']
        self.assertGreater(len(times), 2)
        diff = (dt.strptime(times[3], '%M:%S.%f') - 
                dt.strptime(times[2], '%M:%S.%f')) 
        self.assertGreater(diff.seconds, 2)


    def test_syncing_scroll(self):
        """Scroll sub list while syncing so sub text is always in view.

        """
        self.editor_pg.open_editor_page(self.video.video_id, 'tr')
        text = self.editor_pg.working_text()
        self.editor_pg.buffer_up_subs()
        self.editor_pg.toggle_playback()
        text_els = self.editor_pg.working_text_elements()[:25]
        for x in range(0, 20):
            el = self.editor_pg.working_text_elements()[x]
            self.assertTrue(el.is_displayed())
            self.editor_pg.sync(1, sub_length=1, sub_space=.05)


    def test_helper_syncing(self):
        """Sync helper stays in view while syncing subs.

        """
        self.editor_pg.open_editor_page(self.video.video_id, 'tr')
        time.sleep(3)
        self.editor_pg.buffer_up_subs()
        self.editor_pg.toggle_playback()
        self.editor_pg.sync(1, sub_length=2, sub_space=2)

        for x in range(0, 17):
            self.editor_pg.sync(1, sub_length=1, sub_space=.05)
            self.assertTrue(self.editor_pg.sync_help_displayed())


    def test_helper_scrolling(self):
        """Sync helper not in view after manually scrolling subs.

        """
        self.editor_pg.open_editor_page(self.video.video_id, 'tr')
        time.sleep(3)
        self.editor_pg.buffer_up_subs()
        self.editor_pg.toggle_playback()
        self.editor_pg.sync(1, sub_length=2, sub_space=2)
        for x in range(0, 3):
            self.editor_pg.sync(1, sub_length=1, sub_space=.05)
            self.assertTrue(self.editor_pg.sync_help_displayed())
        self.editor_pg.toggle_playback()
        self.browser.execute_script("window.location.hash='add-sub-at-end'")
        self.assertFalse(self.editor_pg.sync_help_displayed())



    def test_rtl(self):
        self.video_pg.open_video_page(self.video.video_id)
        self.editor_pg.open_editor_page(self.video.video_id, 'ar')
        expected_text = (u'\u0628\u0623\u0646\u0647 \u064a\u0645\u0643\u0646 '
                         u'\u0644\u0644\u0639\u0645\u0644 \u0623\u0646 '
                         u'\u064a\u062d\u0644 \u0645\u0634\u0627\u0643\u0644 '
                         u'\u0648\u0642\u0636\u0627\u064a\u0627 '
                         u'\u0636\u0627\u063a\u0637\u0629')
        sub_text, _ = self.editor_pg.click_working_sub_line(3)
        self.assertEqual(expected_text, sub_text)
        self.assertEqual(sub_text, self.editor_pg.sub_overlayed_text())
        self.assertEqual(expected_text, sub_text)
