#!/usr/bin/python
# -*- coding: utf-8 -*-

from webdriver_testing.webdriver_base import WebdriverTestCase
from webdriver_testing import data_helpers
from webdriver_testing.pages.site_pages import video_page
from webdriver_testing.pages.site_pages import editor_page
from webdriver_testing.pages.site_pages import site_modals
from webdriver_testing.pages.editor_pages import subtitle_editor 
from webdriver_testing.data_factories import UserFactory
import os
import sys
import time


#@unittest.skip('slow')
class TestCaseTranscribing(WebdriverTestCase):
    """Tests for the Subtitle Transcription editor page.
        
    """
    NEW_BROWSER_PER_TEST_CASE = True

    def setUp(self):
        super(TestCaseTranscribing, self).setUp()
        self.data_utils = data_helpers.DataHelpers()
        self.modal = site_modals.SiteModals(self)
        self.editor_pg = editor_page.EditorPage(self)
        td = {'video_url': ('http://qa.pculture.org/amara_tests/'
                            'Birds_short.webmsd.webm')
             }
        self.test_video = self.data_utils.create_video(**td)
        self.video_pg = video_page.VideoPage(self)
        self.user = UserFactory.create()
        self.video_pg.open_video_page(self.test_video.video_id)
        self.video_pg.log_in(self.user.username, 'password')
        self.sub_editor = subtitle_editor.SubtitleEditor(self)
        self.video_pg.log_in(self.user.username, 'password')
        self.video_pg.add_subtitles()
        self.modal.add_language('English', 'English')
        self.editor_pg.legacy_editor()
        self.typed_subs = self.sub_editor.type_subs()

    def tearDown(self):
        super(TestCaseTranscribing, self).tearDown()

    def test_display_normal(self):
        """Manually entered unsynced subs display in editor.

        """
        self.assertEqual(self.typed_subs, self.sub_editor.subtitles_list())


    def test_save(self):
        """Manually entered unsynced subs are saved upon save and exit.
        
        """
        curr_url = self.sub_editor.current_url()
        self.sub_editor.save_and_exit()
        self.sub_editor.open_page(curr_url)
        self.assertEqual(self.typed_subs, self.sub_editor.subtitles_list())

        
    def test_download(self):
        """Manually entered unsynced subs can be download from check page.

        """
        EXPECTED_UNSYNCED_TEXT = u"""1
99:59:59,999 --> 99:59:59,999
I'd like to be Under the sea

2
99:59:59,999 --> 99:59:59,999
In an octopus' garden in the shade.

3
99:59:59,999 --> 99:59:59,999
He'd let me in Knows where we've been

4
99:59:59,999 --> 99:59:59,999
In his octopus' garden in the shade.
"""
        
        self.sub_editor.continue_to_next_step()
        #Past Sync
        self.sub_editor.continue_to_next_step()
        #Past Description
        self.sub_editor.continue_to_next_step()
        #In Check Step - download subtitles
        saved_subs = self.sub_editor.download_subtitles()
        self.assertEqual (saved_subs, EXPECTED_UNSYNCED_TEXT)









