# -*- coding: utf-8 -*-

import datetime
import os

from subtitles import pipeline
from django.core import management
from utils.factories import *
from webdriver_testing.webdriver_base import WebdriverTestCase
from webdriver_testing import data_helpers
from webdriver_testing.pages.site_pages import editor_page
from webdriver_testing.pages.site_pages import site_modals 
from webdriver_testing.pages.site_pages.teams import dashboard_tab
from webdriver_testing.pages.site_pages.teams import tasks_tab 
from webdriver_testing.data_factories import TeamLangPrefFactory
from webdriver_testing.data_factories import UserLangFactory

class TestCaseTaskFreeDashboard(WebdriverTestCase):
    """Test suite for display of Team dashboard when there are no tasks.  """
    NEW_BROWSER_PER_TEST_CASE = False

    @classmethod
    def setUpClass(cls):
        super(TestCaseTaskFreeDashboard, cls).setUpClass()

        cls.data_utils = data_helpers.DataHelpers()
        cls.dashboard_tab = dashboard_tab.DashboardTab(cls)
        cls.admin = UserFactory()
        cls.manager = UserFactory()
        cls.member = UserFactory()
        cls.team = TeamFactory(admin=cls.admin,
                               manager=cls.manager,
                               member=cls.member)

        cls.en_video = VideoFactory(primary_audio_language_code='en')
        TeamVideoFactory(team=cls.team, video=cls.en_video)
        cls.fr_video = VideoFactory(primary_audio_language_code='fr')
        TeamVideoFactory(team=cls.team, video=cls.fr_video)
        cls.video = TeamVideoFactory(team=cls.team).video
        pipeline.add_subtitles(cls.en_video, 'en', SubtitleSetFactory(),
                               complete=True)
        pipeline.add_subtitles(cls.fr_video, 'fr', SubtitleSetFactory(),
                               complete=True)
        cls.polly_glott = TeamMemberFactory(
                team = cls.team,
                ).user

        polly_speaks = ['en', 'cs', 'ru', 'ar']
        for lang in polly_speaks:
            UserLangFactory(user = cls.polly_glott,
                            language = lang)

    def setUp(self):
        self.dashboard_tab.open_team_page(self.team.slug)

    def test_members_generic_create_subs(self):
        """Dashboard displays generic create subs message when no orig lang specified.

        """
        #Create a user that's a member of a team with language preferences set.

        #Login user and go to team dashboard page
        self.dashboard_tab.log_in(self.member.username, 'password')

        #Verify expected videos are displayed.
        self.dashboard_tab.open_team_page(self.team.slug)
        langs = self.dashboard_tab.languages_needed(self.video.title)
        self.assertEqual(['Create Subtitles'], langs)

    def test_members_no_languages(self):
        """Dashboard displays Create Subtitles when member has no langs specified.

        """
        #Create a user that's a member of a team with language preferences set.
        #Login user and go to team dashboard page
        self.dashboard_tab.log_in(self.member.username, 'password')

        #Verify expected videos are displayed.
        self.dashboard_tab.open_team_page(self.team.slug)
        langs = self.dashboard_tab.languages_needed(self.en_video.title)
        self.assertEqual(['Create Subtitles'], langs)



    def test_members_specific_langs_needed(self):
        """Dashboard displays videos matching members language preferences.     

        """
        #Login user and go to team dashboard page
        self.dashboard_tab.log_in(self.polly_glott.username, 'password')

        #Verify expected videos are displayed.
        expected_lang_list = ['Create Czech Subtitles',
                              'Create Russian Subtitles',
                              'Create Arabic Subtitles']
        self.dashboard_tab.open_team_page(self.team.slug)
        langs = self.dashboard_tab.languages_needed(self.en_video.title)
        self.assertEqual(sorted(langs), sorted(expected_lang_list))

    def test_add_suggestion_displayed(self):
        """Add videos link displays for user with permissions, when no videos found.

        """
        
        test_team = TeamFactory(admin = self.admin,
                                video_policy=2)
        self.dashboard_tab.log_in(self.admin.username, 'password')
        self.dashboard_tab.open_team_page(test_team.slug)
        self.assertTrue(self.dashboard_tab.suggestion_present(suggestion_type='add'))

    def test_add_suggestion_not_displayed(self):
        """Add videos link not displayed for user with no permissions, when no videos
          found.

        """

        test_team = TeamFactory(admin = self.admin,
                                member = self.member,
                                video_policy=2)
        self.dashboard_tab.log_in(self.member.username, 'password')
        self.dashboard_tab.open_team_page(test_team.slug)
        self.assertFalse(self.dashboard_tab.suggestion_present(suggestion_type='add'))

    def test_lang_suggestion_displayed(self):
        """Update preferred languages displayed, when no videos found.

        """
        
        test_team = TeamFactory(admin = self.admin,
                                member = self.member)
        self.dashboard_tab.log_in(self.member.username, 'password')
        self.dashboard_tab.open_team_page(test_team.slug)
        self.assertTrue(self.dashboard_tab.suggestion_present(
                             suggestion_type='language'))

    def test_browse_suggestion_displayed(self):
        """Browse videos link displayed, when no videos found.

        """
        test_team = TeamFactory(admin = self.admin,
                                member = self.member)
        self.dashboard_tab.log_in(self.member.username, 'password')
        self.dashboard_tab.open_team_page(test_team.slug)
        self.assertTrue(self.dashboard_tab.suggestion_present(
                             suggestion_type='browse'))

    def test_no_create_nonmember(self):
        """Non-members see dashboard videos without the option to create subtitles.

        """
        non_member = UserFactory()
        self.dashboard_tab.log_in(non_member.username, 'password')
        self.dashboard_tab.open_team_page(self.team.slug)
        langs = self.dashboard_tab.languages_needed(self.en_video.title)
        self.assertEqual(langs, None)

    def test_no_create_guest(self):
        """Guests see dashboard videos without the option to create subtitles.

        """
        self.dashboard_tab.log_out()
        self.dashboard_tab.open_team_page(self.team.slug)
        langs = self.dashboard_tab.languages_needed(self.en_video.title)
        self.assertEqual(langs, None)


class TestCaseTasksEnabledDashboard(WebdriverTestCase):
    """Verify team dashboard displays for teams with tasks enabled.

    """
    NEW_BROWSER_PER_TEST_CASE = False

    @classmethod
    def setUpClass(cls):
        super(TestCaseTasksEnabledDashboard, cls).setUpClass()
        cls.data_utils = data_helpers.DataHelpers()
        cls.editor_pg = editor_page.EditorPage(cls)
        cls.modal = site_modals.SiteModals(cls)
        cls.dashboard_tab = dashboard_tab.DashboardTab(cls)
        cls.tasks_tab = tasks_tab.TasksTab(cls)

        cls.admin = UserFactory()
        cls.manager = UserFactory()
        cls.member = UserFactory()
        cls.team = TeamFactory(admin=cls.admin,
                               manager=cls.manager,
                               member=cls.member,
                               workflow_enabled=True)
        cls.team_workflow = WorkflowFactory(team = cls.team,
                                            autocreate_subtitle=True,
                                            autocreate_translate=True,
                                            review_allowed = 10)

        langs = ['en', 'ru', 'pt-br', 'fr', 'de', 'es']
        for lc in langs:
            TeamLangPrefFactory(team = cls.team,
                                language_code = lc,
                                preferred = True)


        cls.en_video = VideoFactory(primary_audio_language_code='en')
        TeamVideoFactory(team=cls.team, video=cls.en_video)
        cls.video = TeamVideoFactory(team=cls.team).video
        cls.polly_glott = TeamMemberFactory(
                team = cls.team,
                ).user

        polly_speaks = ['en', 'cs', 'ru', 'ar']
        for lang in polly_speaks:
            UserLangFactory(user = cls.polly_glott,
                            language = lang)

    def setUp(self):
        super(TestCaseTasksEnabledDashboard, self).setUp()
        self.dashboard_tab.open_team_page(self.team.slug)

    def test_members_assigned_tasks(self):
        """Members see “Videos you're working on” with  assigned languages.
 
        """
        fr_video = VideoFactory(primary_audio_language_code='fr')
        tv = TeamVideoFactory(team=self.team, video=fr_video)
        task = list(tv.task_set.incomplete_subtitle().filter(language='fr'))[0]
        task.assignee = self.polly_glott
        task.save()
        #Login user and go to team dashboard page
        self.dashboard_tab.log_in(self.polly_glott.username, 'password')

        #Verify expected videos are displayed.
        self.dashboard_tab.open_team_page(self.team.slug)
        self.assertTrue(self.dashboard_tab.dash_task_present(
                            task_type='Create French subtitles',
                            title=fr_video.title))

    def test_manage_your_tasks_link(self):
        """manage your tasks link opens with correct filter defaults. """ 
        ar_video = VideoFactory(primary_audio_language_code='ar')
        tv = TeamVideoFactory(team=self.team, video=ar_video)
        task = list(tv.task_set.incomplete_subtitle().filter(language='ar'))[0]
        task.assignee = self.polly_glott
        task.save()
        self.dashboard_tab.log_in(self.polly_glott.username, 'password')
        #Verify expected videos are displayed.
        self.dashboard_tab.open_team_page(self.team.slug)
        self.dashboard_tab.manage_tasks()
        self.assertIn("?assignee=me&lang=all", self.tasks_tab.current_url())
        self.assertTrue(self.tasks_tab.task_present('Transcribe Arabic Subtitles',
                                                     ar_video.title))

    def test_members_available_tasks(self):
        """Members see “Videos that need your help” with the relevant tasks.
 
        """
        #Login user and go to team dashboard page
        self.dashboard_tab.log_out()
        video = VideoFactory(primary_audio_language_code='en')
        tv = TeamVideoFactory(team=self.team, video=video)
        self.dashboard_tab.log_in(self.polly_glott.username, 'password')

        #Verify expected videos are displayed.
        self.dashboard_tab.open_team_page(self.team.slug)
        expected_lang_list = ['Create English subtitles'] 
        langs = self.dashboard_tab.languages_needed(video.title)
        self.assertEqual(sorted(langs), sorted(expected_lang_list))

    def test_no_langs_available_tasks(self):
        """Members with no lang prefs the list of available tasks in English.

        """
        video = VideoFactory(primary_audio_language_code='en')
        tv = TeamVideoFactory(team=self.team, video=video)
        #Login user and go to team dashboard page
        self.dashboard_tab.log_in(self.member.username, 'password')
        self.dashboard_tab.open_team_page(self.team.slug)
        expected_lang_list = ['Create English subtitles'] 
        langs = self.dashboard_tab.languages_needed(video.title)
        self.assertEqual(sorted(langs), sorted(expected_lang_list))



    def test_start_translation_multi(self):
        """Translation starts from dropdown lines and times from reference lang.

        """
        self.logger.info('setup: Setting task policy to all team members')
        self.team.task_assign_policy=20
        self.team.video_policy=1
        self.team.save()
        en_video = VideoFactory(primary_audio_language_code='en')
        pipeline.add_subtitles(en_video, 'en', 
                               SubtitleSetFactory(), complete=True)
        tv = TeamVideoFactory(team=self.team, video=en_video)
        #Login user and go to team dashboard page
        self.dashboard_tab.log_in(self.polly_glott.username, 'password')
        self.dashboard_tab.open_team_page(self.team.slug)
        self.dashboard_tab.click_lang_task(en_video.title, 
                                           'Create Russian subtitles')
        self.assertEqual(u'Editing Russian\u2026', self.editor_pg.working_language())
        self.assertEqual('English (original)', self.editor_pg.selected_ref_language())
        self.assertEqual(self.editor_pg.start_times(), 
                         self.editor_pg.reference_times())
        self.editor_pg.exit()


    def test_start_subtitles_audio_known(self):
        """Start subtitles when primary audio lang known.

        """
        #Login user and go to team dashboard page
        video = VideoFactory(primary_audio_language_code='cs')
        tv = TeamVideoFactory(team=self.team, video=video)
        self.dashboard_tab.log_in(self.polly_glott.username, 'password')
        self.dashboard_tab.open_team_page(self.team.slug)
        self.dashboard_tab.click_lang_task(video.title, 
                                           'Create Czech subtitles')
        self.assertEqual(u'Editing Czech\u2026', self.editor_pg.working_language())
        self.editor_pg.exit()

    def test_start_subtitles_audio_unknown(self):
        """Start subtitles when primary audio not set.

        """
        #Login user and go to team dashboard page
        video = TeamVideoFactory(team=self.team).video
        self.dashboard_tab.log_in(self.polly_glott.username, 'password')
        self.dashboard_tab.open_team_page(self.team.slug)
        self.dashboard_tab.click_lang_task(video.title, 
                                           'Create subtitles')
        self.modal.add_language('French', 'French') 
        self.assertEqual(u'Editing French\u2026', self.editor_pg.working_language())
        self.editor_pg.exit()

    def test_start_review(self):
        """Member starts review from any task in “Videos that need your help”.

        """
        self.team_workflow.review_allowed = 10
        self.team_workflow.save()
        self.team.task_assign_policy=20
        self.team.video_policy=1
        self.team.save()

        video = VideoFactory(primary_audio_language_code='en')
        tv = TeamVideoFactory(team=self.team, video=video)
        pipeline.add_subtitles(video, 'en', SubtitleSetFactory(), 
                               complete=True, committer=self.polly_glott)
        #Login as reviewer and start the review task.
        self.dashboard_tab.log_in(self.admin.username, 'password')
        self.dashboard_tab.open_team_page(self.team.slug)
        self.logger.info("Clicking the Review English subtitles task")
        self.dashboard_tab.click_lang_task(video.title, 'Review English subtitles')
        self.assertTrue(self.editor_pg.collab_panel_displayed())
        self.dashboard_tab.open_team_page(self.team.slug)
        self.dashboard_tab.handle_js_alert("accept")

    def test_member_language_suggestion(self):
        """Members with no lang pref see the prompt to set language preference.

        """
        self.dashboard_tab.open_team_page(self.team.slug)
        self.dashboard_tab.log_in(self.member.username, 'password')
        self.dashboard_tab.open_team_page(self.team.slug)
        self.assertTrue(self.dashboard_tab.suggestion_present(
                             suggestion_type='authed_language'))
