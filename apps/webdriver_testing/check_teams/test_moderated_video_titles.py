# -*- coding: utf-8 -*-
import os
import time

from caching.tests.utils import assert_invalidates_model_cache
from ted import tasks
from videos.models import Video
from utils.factories import *
from subtitles.pipeline import add_subtitles
from webdriver_testing.webdriver_base import WebdriverTestCase
from webdriver_testing.pages.site_pages.teams_dir_page import TeamsDirPage
from webdriver_testing.pages.site_pages.teams.tasks_tab import TasksTab
from webdriver_testing.pages.site_pages.teams.videos_tab import VideosTab
#from webdriver_testing.data_factories import *
from webdriver_testing.pages.editor_pages import subtitle_editor
from webdriver_testing import data_helpers
from webdriver_testing.pages.site_pages import video_page
from webdriver_testing.pages.site_pages import video_language_page
from webdriver_testing.pages.site_pages import editor_page
from webdriver_testing.pages.site_pages import site_modals
from webdriver_testing.pages.site_pages import edit_video_page

class TestCaseModeratedVideoTitles(WebdriverTestCase):    
    NEW_BROWSER_PER_TEST_CASE = False

    @classmethod
    def setUpClass(cls):
        super(TestCaseModeratedVideoTitles, cls).setUpClass()
        cls.data_utils = data_helpers.DataHelpers()
        cls.admin_video_pg = edit_video_page.EditVideoPage(cls)
        cls.tasks_tab = TasksTab(cls)
        cls.videos_tab = VideosTab(cls)
        cls.video_pg = video_page.VideoPage(cls)

        cls.modal = site_modals.SiteModals(cls)
        cls.editor_pg = editor_page.EditorPage(cls)
        cls.video_lang_pg = video_language_page.VideoLanguagePage(cls)

        cls.staff = UserFactory(is_staff=True, is_superuser=True)
        cls.admin = UserFactory()
        cls.manager = UserFactory()
        cls.member = UserFactory()
        cls.team = TeamFactory(admin=cls.admin,
                               manager=cls.manager,
                               member=cls.member,
                               workflow_type='O',
                               workflow_enabled=True
                              )

        cls.workflow = WorkflowFactory(
            team = cls.team,
            autocreate_subtitle = True,
            autocreate_translate = False,
            review_allowed = 10,
            approve_allowed = 20)
        #Create a member of the team
        cls.subs_file = os.path.join(os.getcwd(), 'apps','webdriver_testing',
                                    'subtitle_data', 'basic_subs.dfxp')

    def setUp(self):
        self.tasks_tab.open_team_page(self.team.slug)
        self.tasks_tab.handle_js_alert('accept')

    def tearDown(self):
        self.browser.get_screenshot_as_file("%s.png" % self.id())

    @classmethod
    def _create_subs(cls, video, lc, user, complete=False):
        subtitles_1 = [
            (0500,2000, 'Hello there'),
        ]
        subtitles_2 = [
            (0500, 2000, 'Hello there'),
            (3000, 5000, 'Hello there'),
        ]
        add_subtitles(video, lc, subtitles_1)
        add_subtitles(video, lc, subtitles_2,
                      author=user,
                      committer=user,
                      complete=complete,
                      )


    def perform_task(self, task_type, video, action, title=None, edit=None):
        self.tasks_tab.perform_task("%s English Subtitles" % task_type,
                                    video.title)
        if edit == 'upload':
            self.editor_pg.upload_subtitles(self.subs_file)
        if edit == 'type':
            self.editor_pg.edit_sub_line('edit', 1)
        if title:
            self.editor_pg.edit_title(title)
        if action == "approve":
            self.editor_pg.collab_action('Approve')
        elif action == "sendback":
            self.editor_pg.collab_action('Send Back')
        elif action == "draft": 
            self.editor_pg.save('Exit')
        else:
            self.editor_pg.endorse_subs()


    def test_speakername_edit_in_task(self):
        video = TeamVideoFactory(team=self.team,
                                 video__primary_audio_language_code='en'
                                ).video
        self.video_pg.open_video_page(video.video_id)
        self.admin_video_pg.log_in(self.staff.username, 'password')
        self.admin_video_pg.open_edit_video_page(video.id)
        self.admin_video_pg.add_speaker_name('Jerry Garcia')
        self.video_pg.open_video_page(video.video_id)
        self._create_subs(video, 'en', self.member, complete=True)
        self.data_utils.complete_review_task(video.get_team_video(),
                                            20, self.manager)
        self.video_pg.open_video_page(video.video_id)
        self.assertEqual(video.title, self.video_pg.video_title())
        self.data_utils.complete_approve_task(video.get_team_video(),
                                            20, self.manager)

    def test_post_publish_edit(self):
        """Edit title in approve, video title updated after publish """
        video = TeamVideoFactory(team=self.team,
                                 video__primary_audio_language_code='en',
                                ).video
        self._create_subs(video, 'en', self.member, complete=True)
        orig_title = video.title
        self.logger.info(video.title)
        new_title = 'this is a new title'
        self.tasks_tab.log_in(self.manager.username, 'password')
        self.data_utils.complete_review_task(video.get_team_video(), 20, self.manager)
        self.data_utils.complete_approve_task(video.get_team_video(), 20, self.manager)
        self.tasks_tab.log_in(self.admin.username, 'password')
        self.video_lang_pg.open_video_lang_page(video.video_id, 'en')
        self.video_lang_pg.edit_subtitles() 
        self.editor_pg.edit_title(new_title)
        with assert_invalidates_model_cache(video):
            self.editor_pg.collab_action('publish')
        self.assertEqual(new_title, self.video_pg.video_title())


    def test_approve_edit_title(self):
        """Edit title in approve, video title updated after publish """
        video = TeamVideoFactory(team=self.team,
                                 video__primary_audio_language_code='en'
                                ).video
        self._create_subs(video, 'en', self.member, complete=True)
        orig_title = video.title
        new_title = 'this is a new title'
        self.tasks_tab.log_in(self.manager.username, 'password')
        self.tasks_tab.open_tasks_tab(self.team.slug)
        self.data_utils.complete_review_task(video.get_team_video(), 20, self.manager)
        self.tasks_tab.log_in(self.admin.username, 'password')
        self.tasks_tab.open_tasks_tab(self.team.slug)
        self.perform_task("Approve Original", video, "approve", title=new_title)
        self.assertEqual(new_title, self.video_pg.video_title())

    def test_review_edit_title(self):
        """Edit title in review, video title updated after publish """
        video = TeamVideoFactory(team=self.team,
                                 video__primary_audio_language_code='en'
                                ).video
        self._create_subs(video, 'en', self.member, complete=True)
        orig_title = video.title
        new_title = 'this is a new title'
        self.tasks_tab.log_in(self.manager.username, 'password')
        self.tasks_tab.open_tasks_tab(self.team.slug)
        self.perform_task("Review Original", video, "approve", title=new_title)
        self.assertEqual(video.title, self.video_pg.video_title())
        self.tasks_tab.log_in(self.admin.username, 'password')
        self.tasks_tab.open_tasks_tab(self.team.slug)
        self.perform_task("Approve Original", video, "approve", title=new_title)
        self.video_pg.open_video_page(video.video_id)
        self.assertEqual(new_title, self.video_pg.video_title())

    def test_review_edit_title_reject(self):
        """Edit title in review, video title updated after publish """
        video = TeamVideoFactory(team=self.team,
                                 video__primary_audio_language_code='en'
                                ).video
        self._create_subs(video, 'en', self.member, complete=True)
        orig_title = video.title
        new_title = 'this is a new title'
        self.tasks_tab.log_in(self.manager.username, 'password')
        self.tasks_tab.open_tasks_tab(self.team.slug)
        self.perform_task("Review Original", video, "sendback", title=new_title, edit='type')
        self.tasks_tab.log_in(self.member.username, 'password')
        self.tasks_tab.open_page('teams/%s/tasks/?assignee=me&/'
                                 % self.team.slug)
        self.perform_task("Transcribe", video, "endorse", edit='upload', title=None)
        self.data_utils.complete_review_task(video.get_team_video(), 20, self.manager)
        self.data_utils.complete_approve_task(video.get_team_video(), 20, self.admin)
        self.video_pg.open_video_page(video.video_id)
        self.assertEqual(new_title, self.video_pg.video_title())



    def test_transcribe_edit_title_save_draft(self):
        """Edit title in transcribe, and save a draft """
        video = TeamVideoFactory(team=self.team,
                                 video__primary_audio_language_code='en',
                                 video__title = 'test title'
                                ).video
        new_title = "subtitler edited the title"
        self.tasks_tab.log_in(self.member.username, 'password')
        self.tasks_tab.open_tasks_tab(self.team.slug)
        self.perform_task("Transcribe", video, "draft", title=new_title, edit='upload')
        self.assertEqual(video.title, self.video_pg.video_title())


    def test_youtube_edit_title_save_draft(self):
        """Edit title in transcribe, and save a draft """
        video = YouTubeVideoFactory(title='Youtube video test',
                                     primary_audio_language_code='en')

        TeamVideoFactory(team=self.team,
                         video=video)
        new_title = "subtitler edited the title"
        self.tasks_tab.log_in(self.member.username, 'password')
        self.tasks_tab.open_tasks_tab(self.team.slug)
        self.perform_task("Transcribe", video, "draft", title=new_title, edit='upload')
        self.assertEqual(video.title, self.video_pg.video_title())

    def test_transcribe_edit_title(self):
        """Edit title in transcribe, video title updated after publish """
        video = TeamVideoFactory(team=self.team,
                                 video__primary_audio_language_code='en',
                                 video__title = 'test title'
                                ).video
        new_title = "subtitler edited the title"
        self.tasks_tab.log_in(self.member.username, 'password')
        self.tasks_tab.open_tasks_tab(self.team.slug)
        self.perform_task("Transcribe", video, "endorse", title=new_title, edit='upload')
        self.assertEqual(video.title, self.video_pg.video_title())
        self.data_utils.complete_review_task(video.get_team_video(), 20, self.manager)
        self.tasks_tab.log_in(self.admin.username, 'password')
        self.tasks_tab.open_tasks_tab(self.team.slug)
        self.perform_task("Approve Original", video, "approve", title=new_title)
        self.video_pg.open_video_page(video.video_id)
        self.assertEqual(new_title, self.video_pg.video_title())

    def test_transcribe_edit_title_reviewer_subs(self):
        """Edit title in transcribe, video title updated after publish """
        video = TeamVideoFactory(team=self.team,
                                 video__primary_audio_language_code='en',
                                ).video
        video.title = 'test'
        video.save()
        new_title = "subtitler edited the title"
        self.tasks_tab.log_in(self.member.username, 'password')
        self.tasks_tab.open_tasks_tab(self.team.slug)
        self.perform_task("Transcribe", video, "endorse", title=new_title, edit='upload')
        self.assertEqual(video.title, self.video_pg.video_title())
        self.tasks_tab.log_in(self.manager.username, 'password')
        self.tasks_tab.open_tasks_tab(self.team.slug)
        self.perform_task("Review Original", video, "approve", title=None, edit='upload')
        self.tasks_tab.log_in(self.admin.username, 'password')
        self.tasks_tab.open_tasks_tab(self.team.slug)
        self.perform_task("Approve Original", video, "approve", title=new_title)
        self.video_pg.open_video_page(video.video_id)
        self.assertEqual(new_title, self.video_pg.video_title())

