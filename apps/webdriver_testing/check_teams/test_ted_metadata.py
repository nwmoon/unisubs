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

  

class TestCaseTranscribe(WebdriverTestCase):
    """Test suite for speaker-name related action on the Transcribe team."""
    NEW_BROWSER_PER_TEST_CASE = False

    @classmethod
    def setUpClass(cls):
        super(TestCaseTranscribe, cls).setUpClass()
        cls.data_utils = data_helpers.DataHelpers()
        cls.video_pg = video_page.VideoPage(cls)
        cls.admin_video_pg = edit_video_page.EditVideoPage(cls)
        cls.tasks_tab = TasksTab(cls)
        cls.superuser = UserFactory(is_staff=True, is_superuser=True)
        cls.admin = UserFactory()
        cls.manager = UserFactory()
        cls.member = UserFactory()
        cls.transcribe_team = TeamFactory(
                               admin=cls.admin,
                               manager=cls.manager,
                               member=cls.member,
                               slug = 'ted-transcribe',
                               workflow_enabled=True,
                               name = 'TED Transcribe')
        cls.transcribe_project = ProjectFactory(
                           team=cls.transcribe_team,
                           name='TedTalks',
                           slug='tedtalks')

        WorkflowFactory(team = cls.transcribe_team,
                        autocreate_subtitle=True,
                        autocreate_translate=False,
                        approve_allowed = 20,
                        review_allowed = 10,
                        )

        cls.team_member = TeamMemberFactory(team=cls.transcribe_team)
        entries = [ { 
                     'ted_talkid': 1800,
                     'ted_duration': '00:14:17',
                     'summary': 'Stuff about the video',
                     'ted_speakername': 'Eleanor Longden',
                     'title': 'The voices in my head',
                     'links': [  {
                                'rel': 'enclosure',
                                'href': 'http://unisubs.example.com/video1800.mp4',
                                'hreflang': 'en',
                               }
                              ], 
                     'updated_parsed': time.localtime(10000),
                     },
                   { 
                     'ted_talkid': 1801,
                     'ted_duration': '00:12:17',
                     'summary': 'Stuff about the video',
                     'title': 'No speaker name',
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
            tasks._parse_entry(cls.transcribe_team, entry, 
                               cls.team_member, cls.transcribe_project)

        cls.video, _ = Video.get_or_create_for_url(
                       'http://unisubs.example.com/video1800.mp4')
        cls.video_pg.open_video_page(cls.video.video_id)
        cls.video_pg.log_in(cls.admin.username, 'password')


    def test_speakername_draft(self):
        """English draft version created on feed import with speaker name.

        """
        en = self.video.subtitle_language('en').get_tip(full=True)
        self.assertEquals({'speaker-name': 'Eleanor Longden'}, 
                          en.get_metadata())

    def test_speakername_tasks_display(self):
        self.tasks_tab.log_in(self.admin.username, 'password')

        self.tasks_tab.open_tasks_tab(self.transcribe_team.slug)
        self.assertTrue(self.tasks_tab.task_present('Transcribe English Subtitles', 
                        self.video.title))

    def test_speakername_admin_edit(self):
        v, _ = Video.get_or_create_for_url(
                       'http://unisubs.example.com/video1801.mp4')
        self.admin_video_pg.log_in(self.superuser.username, 'password')
        self.admin_video_pg.open_edit_video_page(v.id)
        self.admin_video_pg.add_speaker_name('Jerry Garcia')
        v.clear_language_cache()
        v, _ = Video.get_or_create_for_url(
                       'http://unisubs.example.com/video1801.mp4')

        self.assertEquals({u'speaker-name': u'Jerry Garcia'}, v.get_metadata())


class TestCaseTED(WebdriverTestCase):
    """Test suite for speakername behavior on the TED team."""
    NEW_BROWSER_PER_TEST_CASE = False

    @classmethod
    def setUpClass(cls):
        super(TestCaseTED, cls).setUpClass()
        cls.data_utils = data_helpers.DataHelpers()
        cls.video_pg = video_page.VideoPage(cls)
        cls.video_lang_pg = video_language_page.VideoLanguagePage(cls)
        cls.profile_dash_pg = profile_dash_page.ProfileDashPage(cls)

        cls.activity_tab = ActivityTab(cls)
        cls.tasks_tab = TasksTab(cls)
        cls.dashboard_tab = DashboardTab(cls)
        cls.videos_tab = VideosTab(cls)

        cls.watch_pg = watch_page.WatchPage(cls)

        cls.logger.info("Create TED teams")
        cls.admin = UserFactory()
        cls.manager = UserFactory()
        cls.member = UserFactory()
        cls.ted_team = TeamFactory(
                               admin=cls.admin,
                               manager=cls.manager,
                               member=cls.member,
                               slug = 'ted',
                               workflow_enabled=True,
                               name = 'TED')
        cls.team_member = TeamMemberFactory(team=cls.ted_team)
        WorkflowFactory(team = cls.ted_team,
                        autocreate_subtitle=True,
                        autocreate_translate=True,
                        approve_allowed = 20,
                        review_allowed = 10,
                        )
                      
        cls.ted_project = ProjectFactory.create(
                           team=cls.ted_team,
                           name='TedTalks',
                           slug='tedtalks')

        lang_list = ['en', 'ru', 'pt-br', 'de', 'sv']
        for language in lang_list:
            TeamLangPrefFactory.create(team=cls.ted_team, language_code=language,
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
            tasks._parse_entry(cls.ted_team, entry, 
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
        cls.video_pg.open_video_page(cls.speaker_video.video_id)


    def tearDown(self):
        self.browser.get_screenshot_as_file("%s.png" % self.id())

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

    def test_ted_api_speakername_published(self):
        """TED api returns translated speaker name from published version."""

        url_part = '%sapi2/ted/videos/1806/languages/sv' % self.base_url
        resp = self.data_utils.make_request(self.admin, 'get', url_part)
        r = resp.json
        self.assertEqual(r['metadata']['speaker-name'], 'Jultomten')

    def test_ted_api_title_published(self):
        """TED api returns translated title from published version."""
        url_part = '%sapi2/ted/videos/1806/languages/sv' % self.base_url
        r = self.data_utils.make_request(self.admin, 'get', url_part)
        response = r.json
        self.assertEqual(response['title'], 'sv subs title')

    def test_ted_api_speaker_draft(self):
        """TED api returns translated speaker name from draft version."""
        url_part = '%sapi2/ted/videos/1806/languages/de' % self.base_url
        r = self.data_utils.make_request(self.admin, 'get', url_part)
        response = r.json
        self.assertEqual(response['metadata']['speaker-name'], 'Klaus')

    def test_ted_api_title_draft(self):
        """TED api returns translated speaker name from draft version."""
        url_part = '%sapi2/ted/videos/1806/languages/de' % self.base_url
        r = self.data_utils.make_request(self.admin, 'get', url_part)
        response = r.json
        self.assertEqual(response['title'], 'de subs title')


    def test_ted_api_nospeaker(self):
        """TED api returns '' when no translated speaker name. """
        url_part = '%sapi2/ted/videos/1806/languages/ru' % self.base_url
        r = self.data_utils.make_request(self.admin, 'get', url_part)
        response = r.json
        self.assertEqual(response['metadata']['speaker-name'], '')


    def test_amara_api_published(self):
        """Amara api returns translated speaker name for published version. """
        url_part = 'videos/%s/languages/sv' % self.speaker_video.video_id
        resp = self.data_utils.make_request(self.admin, 'get', url_part)
        r = resp.json
        self.assertEqual(r['metadata']['speaker-name'], 'Jultomten')


    def test_amara_api_draft(self):
        """Amara api returns '' when only draft version. """
        url_part = 'videos/%s/languages/de' % self.speaker_video.video_id
        r = self.data_utils.make_request(self.admin, 'get', url_part)
        response = r.json

        self.assertEqual(response['metadata']['speaker-name'], '')

    def test_amara_api_nospeaker(self):
        """Amara api returns '' when no speaker name translated. """
        url_part = 'videos/%s/languages/ru' % self.speaker_video.video_id
        r = self.data_utils.make_request(self.admin, 'get', url_part)
        response = r.json
        self.assertEqual(response['metadata']['speaker-name'], '')

    def test_site_search_video_speakername(self):
        """Site search for video speaker name has results. """
        speaker = 'Jinsop Lee'
        self.watch_pg.open_watch_page()
        results_pg = self.watch_pg.basic_search(speaker)
        self.assertTrue(results_pg.search_has_results())

    def test_site_search_transcribed_speakername(self):
        """Site search for transcribed speakername has results."""
        speaker = 'Santa'
        self.watch_pg.open_watch_page()
        results_pg = self.watch_pg.basic_search(speaker)
        self.assertTrue(results_pg.search_has_results())

    def test_site_search_translated_speakername(self):
        """Site search for translated speaker name has results. """
        speaker = 'Jultomten'
        self.watch_pg.open_watch_page()
        results_pg = self.watch_pg.basic_search(speaker)
        self.assertTrue(results_pg.search_has_results())

    def test_site_search_draft_speakername(self):
        """Site search for draft speakername has No results."""
        speaker = 'Klaus'
        self.watch_pg.open_watch_page()
        results_pg = self.watch_pg.basic_search(speaker)
        self.assertTrue(results_pg.search_has_no_results())


    def test_dashboard_display_speaker(self):
        """Speaker name displays with title on dashboard. """
        self.dashboard_tab.log_out()
        for lang in ['en', 'ru', 'sv']:
            UserLangFactory(user = self.admin,
                            language = lang)

        self.dashboard_tab.log_in(self.admin.username, 'password')
        self.dashboard_tab.open_team_page(self.ted_team.slug)
        self.assertTrue(self.dashboard_tab.dash_task_present(
                            task_type='Create Russian subtitles',
                            title='Jinsop Lee: TestVideo1'))

    def test_dashboard_display_nospeaker(self):
        """Title only when no speaker name for video on dashboard. """
        self.dashboard_tab.open_team_page(self.ted_team.slug)
        self.dashboard_tab.log_in(self.admin.username, 'password')
        self.dashboard_tab.open_team_page(self.ted_team.slug)
        self.assertTrue(self.dashboard_tab.video_present('NoSpeakerVideo'))

    def test_tasks_tab_display_speaker(self):
        """Speaker name displays with title on tasks tab. """
        self.tasks_tab.log_in(self.admin.username, 'password')
        self.tasks_tab.open_page('teams/%s/tasks/?assignee=anyone'
                                 % self.ted_team.slug)
        self.assertTrue(self.tasks_tab.task_present('Approve German Subtitles',
                        'Jinsop Lee: TestVideo1'))

    def test_tasks_tab_search_speaker(self):
        """Tasks tab search on speaker name returns search results . """
        self.tasks_tab.log_in(self.admin.username, 'password')
        self.tasks_tab.open_page('teams/%s/tasks/?project=any&assignee=anyone&q=Jinsop'
                                 % self.ted_team.slug)
        self.assertTrue(self.tasks_tab.task_present('Approve German Subtitles',
                        'Jinsop Lee: TestVideo1'))


    def test_tasks_tab_display_nospeaker(self):
        """Title only when no speaker name for video on tasks tab. """
        self.tasks_tab.log_in(self.admin.username, 'password')
        self.tasks_tab.open_page('teams/%s/tasks/?assignee=anyone'
                                 % self.ted_team.slug)
        self.assertTrue(self.tasks_tab.task_present('Transcribe English Subtitles',
                        'NoSpeakerVideo'))

    def test_videos_tab_display_speaker(self):
        """Speaker name displays with title on videos tab. """
        self.videos_tab.log_in(self.admin.username, 'password')
        self.videos_tab.open_videos_tab(self.ted_team.slug)
        self.assertTrue(self.videos_tab.is_text_present('h4 a', 
                                                        'Santa: TestVideo1'))

    def test_videos_tab_search_speaker(self):
        """Videos tab search on speaker name returns search results . """
        self.videos_tab.log_in(self.admin.username, 'password')
        self.videos_tab.open_page('/teams/%s/videos/?assignee=&project=&lang=&q=Jinsop'
                                 % self.ted_team.slug)
        self.assertTrue(self.videos_tab.is_text_present('h4 a', 
                                                        'Jinsop Lee: TestVideo1'))

    def test_videos_tab_display_nospeaker(self):
        """Title only when no speaker name for video on videos tab. """
        self.videos_tab.log_in(self.admin.username, 'password')
        self.videos_tab.open_videos_tab(self.ted_team.slug)
        self.assertTrue(self.videos_tab.video_present('NoSpeakerVideo'))

    def test_video_lang_pg_approved_speakername(self):
        self.video_pg.open_page('/videos/%s/sv' % self.speaker_video.video_id)
        time.sleep(2)
        self.assertIn('Jultomten: sv subs title', 
                         self.video_pg.video_title())

    def test_video_lang_pg_draft_speakername(self):
        self.video_pg.open_page('/videos/%s/de' % self.speaker_video.video_id)
        self.assertIn('Klaus: de subs title', 
                       self.video_pg.video_title())

    def test_video_pg_no_speakername(self):
        self.video_pg.open_page('/videos/%s' % self.nospeaker_video.video_id)
        self.assertEqual('NoSpeakerVideo', 
                       self.video_pg.video_title())

    def test_video_activity_speakername(self):
        self.video_pg.open_video_activity(self.speaker_video.video_id)
        video_activities = self.video_pg.activity_list()
        for activity in video_activities:
            if 'Jinsop Lee: ' in activity:
                break
        else:
            self.fail('speaker name not found in any activities, %s' % video_activities)

    def test_user_dash_speakername(self):
        self.profile_dash_pg.log_in(self.admin.username, 'password')
        self.profile_dash_pg.open_profile_dashboard()
        user_tasks = self.profile_dash_pg.current_tasks()
        for t in user_tasks:
            if 'Jinsop Lee: TestVideo1' in t:
                break
        else:
            self.fail('speaker name not found in any tasks, %s' % user_tasks)


    def test_activity_tab(self):
        self.activity_tab.log_in(self.admin.username, 'password')
        self.activity_tab.open_activity_tab(self.ted_team.slug)
