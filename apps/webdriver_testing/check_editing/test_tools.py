#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import time 
from django.test import TestCase
from django.core import management
from webdriver_testing.pages.site_pages import site_modals
from webdriver_testing.webdriver_base import WebdriverTestCase
from webdriver_testing import data_helpers
from webdriver_testing.pages.site_pages import video_page
from webdriver_testing.pages.site_pages import editor_page
from webdriver_testing.data_factories import UserFactory

class TestCaseTools(WebdriverTestCase):

    NEW_BROWSER_PER_TEST_CASE = False

    @classmethod
    def setUpClass(cls):
        super(TestCaseTools, cls).setUpClass()
        cls.modal = site_modals.SiteModals(cls)
        cls.editor_pg = editor_page.EditorPage(cls)
        cls.video_pg = video_page.VideoPage(cls)
        cls.user = UserFactory.create()
        cls.video_pg.open_page('auth/login/', alert_check=True)
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
        management.call_command('update_index', interactive=False) 

    def tearDown(self):
        try:
            self.editor_pg.exit()
        except:
            pass

    def test_timings_present_for_new_translation(self):
        """New translation starts with lines and times. """

        self.video_pg.open_video_page(self.video.video_id)
        self.video_pg.add_subtitles()
        self.modal.add_language('Polish', audio='English')
        working_times = self.editor_pg.start_times()
        ref_times = self.editor_pg.reference_times()
        self.assertEqual(ref_times[:5], working_times[:5]) 
        self.assertEqual(len(ref_times), len(working_times))


    def test_copy_timings_to_untimed_text(self):
        """Copy timings to untimed text. """
        self.editor_pg.open_editor_page(self.video.video_id, 'nl')
        self.editor_pg.copy_timings()
        working_times = self.editor_pg.start_times()
        ref_times = self.editor_pg.reference_times()
        self.assertEqual(ref_times[:5], working_times[:5]) 


    def test_copy_timings_change_reference(self):
        """Change reference lang then copy timings. """
        self.editor_pg.open_editor_page(self.video.video_id, 'nl')
        self.editor_pg.select_ref_language('Danish')
        self.editor_pg.copy_timings()
        working_times = self.editor_pg.start_times()
        ref_times = self.editor_pg.reference_times()
        self.assertEqual(ref_times[:5], working_times[:5]) 

    def test_copy_timings_reference_unsynced(self):
        """No copy in menu if reference subs are unsynced. """
        self.editor_pg.open_ed_with_base(self.video.video_id, 'sv', 'nl')
        self.editor_pg.select_ref_language('Dutch')
        time.sleep(3)
        self.assertEqual("Element not displayed", self.editor_pg.copy_timings())

    def test_copy_timings_reference_private(self):
        """No copy in menu if reference subs are draft (private). """
        sl_tr = self.video.subtitle_language('tr').get_tip(full=True)
        sl_tr.visibility_override = 'private'
        sl_tr.save()

        self.editor_pg.open_editor_page(self.video.video_id, 'en')
        self.editor_pg.select_ref_language('Turkish')
        self.assertEqual("Element not displayed", self.editor_pg.copy_timings())
