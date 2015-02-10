#!/usr/bin/python
# -*- coding: utf-8 -*-

import time

from django.core import management
from ted import tasks
from videos.models import Video
from subtitles.pipeline import add_subtitles

from utils.factories import *

from webdriver_testing.webdriver_base import WebdriverTestCase
from webdriver_testing import data_helpers
from webdriver_testing.data_factories import UserLangFactory
from webdriver_testing.data_factories import TeamLangPrefFactory

from webdriver_testing.pages.site_pages import watch_page
from webdriver_testing.pages.site_pages import video_page
from webdriver_testing.pages.site_pages import video_language_page
from webdriver_testing.pages.site_pages import edit_video_page
from webdriver_testing.pages.site_pages.teams.tasks_tab import TasksTab
from webdriver_testing.pages.site_pages.teams.activity_tab import ActivityTab
from webdriver_testing.pages.site_pages.teams.videos_tab import VideosTab
from webdriver_testing.pages.site_pages.teams.dashboard_tab import DashboardTab
from webdriver_testing.pages.site_pages.profiles import profile_dash_page


class TestCaseActivity(WebdriverTestCase):
    """Test suite for team activity tab"""
    NEW_BROWSER_PER_TEST_CASE = False

    @classmethod
    def setUpClass(cls):
        super(TestCaseActivity, cls).setUpClass()
        cls.data_utils = data_helpers.DataHelpers()
        cls.activity_tab = ActivityTab(cls)
        cls.admin = UserFactory()
        cls.manager = UserFactory()
        cls.member = UserFactory()
        cls.team = TeamFactory(
                               admin=cls.admin,
                               manager=cls.manager,
                               member=cls.member,
                               slug = 'ted',
                               workflow_enabled=True,
                               name = 'TED')
        cls.team_member = TeamMemberFactory(team=cls.team)
        WorkflowFactory(team = cls.team,
                        autocreate_subtitle=True,
                        autocreate_translate=True,
                        approve_allowed = 20,
                        review_allowed = 10,
                        )
                      
        cls.ted_project = ProjectFactory.create(
                           team=cls.team,
                           name='TedTalks',
                           slug='tedtalks')

        lang_list = ['en', 'ru', 'pt-br', 'de', 'sv']
        for language in lang_list:
            TeamLangPrefFactory.create(team=cls.team, language_code=language,
                                       preferred=True)

        entries = [ { 
                   'ted_talkid': 1806,
                   'ted_duration': '00:09:03',
                   'summary': 'Stuff about the video',
                   'ted_speakername': 'Jinsop Lee',
                   'title': 'TestVideo1',
                   'links': [  {
                                'rel': 'enclosure',
                                'href': 'http://unisubs.example.com/video1806.mp4',
                                'hreflang': 'en',
                               }
                            ], 
                   'updated_parsed': time.localtime(10000)
                  },
                  { 
                     'ted_talkid': 1801,
                     'ted_duration': '00:12:17',
                     'summary': 'Stuff about the video',
                     'title': 'NoSpeakerVideo',
                     'links': [  {
                                'rel': 'enclosure',
                                'href': 'http://unisubs.example.com/video1801.mp4',
                                'hreflang': 'en',
                               }
                              ], 
                     'updated_parsed': time.localtime(10000)
                  }
                ]
        for entry in entries:
            tasks._parse_entry(cls.team, entry, 
                               cls.team_member, cls.ted_project)


        cls.speaker_video, _ = Video.get_or_create_for_url(
                            'http://unisubs.example.com/video1806.mp4')
        cls.nospeaker_video, _ = Video.get_or_create_for_url(
                            'http://unisubs.example.com/video1801.mp4')

        #Add approved 'en' subs speaker name
        speaker_data =  { 'speaker-name': 'Santa' } 
        cls._create_subs(cls.speaker_video, 'en', complete=True, metadata=speaker_data) 
        cls.data_utils.complete_review_task(cls.speaker_video.get_team_video(),
                                            20, cls.admin)
        cls.data_utils.complete_approve_task(cls.speaker_video.get_team_video(),
                                            20, cls.admin)

        #Add approved 'sv' translation with speaker name
        speaker_data = { 'speaker-name': 'TomTom' }
        cls._create_subs(cls.speaker_video, 'sv', True, metadata=speaker_data, title='sv subs title')
        cls.data_utils.complete_review_task(cls.speaker_video.get_team_video(),
                                            20, cls.admin)
        sv = cls.speaker_video.subtitle_language('sv').get_tip()
        sv.update_metadata( { 'speaker-name': 'Jultomten'} ) 
        cls.data_utils.complete_approve_task(cls.speaker_video.get_team_video(),
                                            20, cls.admin)


        #Add draft 'de' subs reviewed with speaker name
        speaker_data = { 'speaker-name': 'Klaus' }
        cls._create_subs(cls.speaker_video, 'de', True, metadata=speaker_data, title='de subs title')
        cls.data_utils.complete_review_task(cls.speaker_video.get_team_video(),
                                            20, cls.admin)
        #Add ru draft, no speaker name
        cls._create_subs(cls.speaker_video, 'ru')
        management.call_command('update_index', interactive=False)
        cls.activity_tab.open_activity_tab(cls.speaker_video.video_id)


    @classmethod
    def _add_speakername(cls, speaker):
        url_part = 'videos/%s/' % cls.speaker_video.video_id
        new_data = {
                    'metadata' : { 'speaker-name': speaker }
                  }
        self.data_utils.make_request(self.user, 'put', 
                                     url_part, **new_data)
        
    @classmethod
    def _create_subs(cls, video, lc, complete=False, metadata=None, title=None):
        subtitles_1 = [
            (0, 1000, 'Hello there'),
        ]
        subtitles_2 = [
            (0, 1000, 'Hello there'),
            (1000, 2000, 'Hello there'),
        ]
        add_subtitles(cls.speaker_video, lc, subtitles_1, visibility='private')
        add_subtitles(cls.speaker_video, lc, subtitles_2, 
                      author=cls.admin, 
                      committer=cls.admin, 
                      complete=complete,
                      metadata=metadata,
                      title=title, 
                      visibility='private')

    def test_add_version_filter(self):
        self.activity_tab.log_in(self.admin.username, 'password')
        self.activity_tab.open_activity_tab(self.team.slug)
        self.activity_tab.activity_type_filter('add version')
        self.activity_tab.update_filters()
        actions = self.activity_tab.activity_list()
        self.logger.info(self.activity_tab.activity_list())
        self.assertIn('{0} {1} edited Russian subtitles'.format(
                          self.admin.first_name, 
                          self.admin.last_name),
                      actions[0])

    def test_video_lang_filter(self):
        self.activity_tab.log_in(self.admin.username, 'password')
        self.activity_tab.open_activity_tab(self.team.slug)
        self.activity_tab.activity_type_filter('add version')
        self.activity_tab.primary_audio_filter('English')
        self.activity_tab.update_filters()
        actions = self.activity_tab.activity_list()
        self.logger.info(self.activity_tab.activity_list())
        self.assertIn('{0} {1} edited Russian subtitles'.format(
                          self.admin.first_name, 
                          self.admin.last_name),
                      actions[0])
