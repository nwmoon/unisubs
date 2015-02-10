#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from django.test import TestCase
from django.core import management

from webdriver_testing.webdriver_base import WebdriverTestCase
from webdriver_testing import data_helpers
from webdriver_testing.pages.site_pages import video_page
from webdriver_testing.pages.site_pages import video_language_page
from webdriver_testing.pages.site_pages import editor_page
from webdriver_testing.pages.editor_pages import subtitle_editor 
from webdriver_testing.data_factories import UserFactory
from webdriver_testing.data_factories import TaskFactory
from webdriver_testing.data_factories import WorkflowFactory


class TestCaseEntryExit(WebdriverTestCase):
    """Entry and Exit points to New Editor. """
    NEW_BROWSER_PER_TEST_CASE = False

    @classmethod
    def setUpClass(cls):
        super(TestCaseEntryExit, cls).setUpClass()
        cls.sub_editor = subtitle_editor.SubtitleEditor(cls)
        cls.editor_pg = editor_page.EditorPage(cls)
        cls.video_pg = video_page.VideoPage(cls)
        cls.video_lang_pg = video_language_page.VideoLanguagePage(cls)
        cls.data_utils = data_helpers.DataHelpers()
        cls.user = UserFactory.create()
        cls.video_pg.open_page('auth/login/')
        cls.user = UserFactory.create()
        cls.video_pg.log_in(cls.user.username, 'password')

    def test_exit_to_legacy(self):
        """Open legacy editor from new.

        """

        data = {'video_url': 'http://www.youtube.com/watch?v=WqJineyEszo',
                'title': ('X Factor Audition - Stop Looking At My '
                          'Mom Rap - Brian Bradley'),
               }
        video = self.data_utils.create_video(**data)
        self.data_utils.add_subs(video=video)

        self.video_lang_pg.open_video_lang_page(video.video_id, 'en')
        self.video_lang_pg.edit_subtitles()
        self.assertEqual('English', self.editor_pg.selected_ref_language())
        self.assertEqual(u'Editing English\u2026', 
                          self.editor_pg.working_language())
        self.editor_pg.legacy_editor()
        self.assertEqual('Typing', self.sub_editor.dialog_title())

