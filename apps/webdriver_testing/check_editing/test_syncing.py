#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest
from webdriver_testing.webdriver_base import WebdriverTestCase
from webdriver_testing import data_helpers
from webdriver_testing.pages.site_pages import video_page
from webdriver_testing.pages.site_pages import video_language_page
from webdriver_testing.pages.editor_pages import subtitle_editor 
from webdriver_testing.pages.site_pages import editor_page
from webdriver_testing.pages.site_pages import site_modals
from webdriver_testing.data_factories import UserFactory
import os
import time

@unittest.skip('slow')
class TestCasePartialSync(WebdriverTestCase):
    """Tests for the Legacy Editor Subtitle Syncing editor page.
        
    """
    NEW_BROWSER_PER_TEST_CASE = False

    @classmethod
    def setUpClass(cls):
        super(TestCasePartialSync, cls).setUpClass()
        cls.data_utils = data_helpers.DataHelpers()
        cls.user = UserFactory.create(username = 'user')
        cls.modal = site_modals.SiteModals(cls)
        cls.editor_pg = editor_page.EditorPage(cls)
        cls.sub_editor = subtitle_editor.SubtitleEditor(cls)
        cls.video_pg = video_page.VideoPage(cls)
        cls.video_language_pg = video_language_page.VideoLanguagePage(cls)

        td = {'video_url': ('http://www.youtube.com/watch?v=WqJineyEszo')
             }
        cls.test_video = cls.data_utils.create_video(**td)
        cls.video_pg.open_video_page(cls.test_video.video_id)
        cls.video_pg.log_in(cls.user.username, 'password')
        cls.video_pg.set_skiphowto()
        #Open the video page and sync the first 3 subs
        cls.video_pg.add_subtitles()
        cls.modal.add_language('English', 'English')
        cls.editor_pg.legacy_editor()
        cls.typed_subs = cls.sub_editor.type_subs()
        cls.sub_editor.save_and_exit()

                        
    def setUp(self):
        super(TestCasePartialSync, self).setUp()
        self.video_language_pg.open_video_lang_page(
                self.test_video.video_id, 'en')
        self.video_language_pg.edit_subtitles()
        self.editor_pg.legacy_editor()
        self.sub_editor.continue_to_next_step()
        num_synced_subs = 3
        self.sub_editor.sync_subs(num_synced_subs)

    def tearDown(self):
        super(TestCasePartialSync, self).tearDown()
        self.video_pg.open_video_page(self.test_video.video_id)
        try:
            self.sub_editor.incomplete_alert_text()
        except:
            pass
        
    def test_display__normal(self):
        """Manually entered partially subs display in editor.

        """

        timing_list = self.sub_editor.sub_timings()
        self.logger.info( timing_list)
        #Verify synced subs are increasing
        try:
            self.assertGreater(float(timing_list[1]), float(timing_list[0]))
        except ValueError as e:
            self.fail(e)
        #Verify last sub is blank
        self.assertEqual(timing_list[-1], '')

       
    def test_save(self):
        """Manually entered partially subs are saved upon save and exit.
        
        """
        timing_list = self.sub_editor.sub_timings()
        curr_url = self.sub_editor.current_url()
        self.sub_editor.save_and_exit()
        self.sub_editor.open_page(curr_url)
        self.sub_editor.continue_to_next_step()
        #Verify sub timings are same as pre-save timings 
        self.assertEqual(timing_list, self.sub_editor.sub_timings())


    def test_download(self):
        """Manually entered partially synced subs can be download from check page.

        """
        timing_list = self.sub_editor.sub_timings()
        self.logger.info( timing_list)
        #Past Sync
        self.sub_editor.continue_to_next_step()
        #Past Description
        self.sub_editor.continue_to_next_step()
        #In Check Step - download subtitles
        saved_subs = self.sub_editor.download_subtitles()
        self.logger.info( saved_subs)
        #Verify timings are in the saved list
        time_check = timing_list[1].replace('.', ',')
        self.logger.info( time_check)
        self.assertIn(time_check, saved_subs)
            
