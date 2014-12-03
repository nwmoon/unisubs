# -*- coding: utf-8 -*-
import os

from utils.factories import *
from subtitles import pipeline

from webdriver_testing.webdriver_base import WebdriverTestCase
from webdriver_testing.data_factories import TeamMemberFactory
from webdriver_testing import data_helpers
from webdriver_testing.pages.site_pages import video_page
from webdriver_testing.pages.site_pages import video_language_page
from webdriver_testing.pages.editor_pages import dialogs


class TestCasePublishedVideos(WebdriverTestCase):    
    NEW_BROWSER_PER_TEST_CASE = False

    @classmethod
    def setUpClass(cls):
        super(TestCasePublishedVideos, cls).setUpClass()
        cls.data_utils = data_helpers.DataHelpers()
        cls.video_pg = video_page.VideoPage(cls)
        cls.video_lang_pg = video_language_page.VideoLanguagePage(cls)
        cls.create_modal = dialogs.CreateLanguageSelection(cls)
        cls.user = UserFactory(is_partner=True)
        
        #Add a team with workflows, tasks and preferred languages
        cls.logger.info('setup: Create a team with tasks enabled')
        cls.admin = UserFactory()
        cls.manager = UserFactory()
        cls.member = UserFactory()
        cls.team = TeamFactory(admin=cls.admin,
                               manager=cls.manager,
                               member=cls.member,
                               workflow_enabled=True,
                               translate_policy=20,
                               subtitle_policy=20,
                              )
        cls.team_workflow = WorkflowFactory(team = cls.team,
                                            autocreate_subtitle=True,
                                            autocreate_translate=True,
                                            approve_allowed = 10,
                                            review_allowed = 10,
                                           )
        cls.nonmember = UserFactory()

        #Add video to team with published subtitles
        cls.logger.info('Setup: Add video to team with published subs.')
        cls.published = VideoFactory()
        pipeline.add_subtitles(cls.published, 'en', SubtitleSetFactory(),
                               action='publish')
        TeamVideoFactory(team=cls.team, video=cls.published)
        cls.video_pg.open_video_page(cls.published.video_id)


    def setUp(self):
        if self.team.subtitle_policy != 20:
            self.team.subtitle_policy=20
            self.team.save()
        if self.team.translate_policy != 20:
            self.team.translate_policy=20
            self.team.save()

    def test_video_add_subtitles(self):
        """No Add Subtitles option in the video view for moderated videos"""

        self.video_pg.open_video_page(self.published.video_id)
        self.assertFalse(self.video_pg.displays_add_subtitles())

    def test_video_upload_subtitles(self):
        """No Upload Subtitles option in the video view for moderated videos"""

        self.video_pg.open_video_page(self.published.video_id)
        self.assertFalse(self.video_pg.displays_upload_subtitles())

    def test_video_add_translation(self):
        """No Add Translation in the video view for moderated videos"""
        self.video_pg.open_video_page(self.published.video_id)
        self.assertFalse(self.video_pg.displays_add_subtitles())

    def test_published_guest_display(self):
        """Published version is visible to guests in subtitle view"""
        self.video_pg.open_video_page(self.published.video_id)
        self.video_lang_pg.open_video_lang_page(self.published.video_id, 'en')
        self.assertTrue(self.video_lang_pg.displays_subtitles())

    def test_published_nonmember_display(self):
        """Published version is visible to non-members in subtitle view"""
        self.video_pg.open_video_page(self.published.video_id)
        self.video_pg.log_in(self.nonmember.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.published.video_id, 'en')
        self.assertTrue(self.video_lang_pg.displays_subtitles())


class TestCaseDraftVideos(WebdriverTestCase):    
    NEW_BROWSER_PER_TEST_CASE = False

    @classmethod
    def setUpClass(cls):
        super(TestCaseDraftVideos, cls).setUpClass()
        cls.data_utils = data_helpers.DataHelpers()
        cls.video_pg = video_page.VideoPage(cls)
        cls.video_lang_pg = video_language_page.VideoLanguagePage(cls)
        cls.create_modal = dialogs.CreateLanguageSelection(cls)
        cls.user = UserFactory(username = 'user', is_partner=True)
        #Add a team with workflows, tasks and preferred languages
        cls.logger.info('setup: Create a team with tasks enabled')
        cls.admin = UserFactory()
        cls.manager = UserFactory()
        cls.member = UserFactory()
        cls.team = TeamFactory(admin=cls.admin,
                               manager=cls.manager,
                               member=cls.member,
                               workflow_enabled=True,
                               translate_policy=20,
                               subtitle_policy=20,
                              )
        cls.team_workflow = WorkflowFactory(team = cls.team,
                                            autocreate_subtitle=True,
                                            autocreate_translate=True,
                                            approve_allowed = 10,
                                            review_allowed = 10,
                                           )
        cls.nonmember = UserFactory()

        #Add video to team with draft subtitles
        cls.logger.info('Setup: Add video to team with draft subs.')
        cls.draft = TeamVideoFactory.create(
                team=cls.team, 
                video=cls.data_utils.create_video(),
                added_by=cls.user).video
        data = { 'visibility': 'private', 
                 'video': cls.draft,
                 'committer': cls.user }
        cls.data_utils.add_subs(**data)
        cls.video_pg.open_video_page(cls.draft.video_id)

    def setUp(self):
        self.team.translate_policy=20
        self.team.save()
        self.video_pg.open_video_page(self.draft.video_id)

    def test_video_add_subtitles(self):
        """No Add Subtitles option in the video view for moderated videos"""

        self.assertFalse(self.video_pg.displays_add_subtitles())

    def test_video_upload_subtitles(self):
        """No Upload Subtitles option in the video view for moderated videos"""

        self.assertFalse(self.video_pg.displays_upload_subtitles())

    def test_draft_guest_display(self):
        """Draft is not visible to guests in subtitle view."""
        self.video_lang_pg.open_video_lang_page(self.draft.video_id, 'en')
        self.assertIn('waiting to be moderated', self.video_lang_pg.displays_subtitles())

    def test_draft_nonmember_display(self):
        """Draft is not visible to non-members in subtitle view."""
        self.video_pg.log_in(self.nonmember.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.draft.video_id, 'en')
        self.assertIn('waiting to be moderated', self.video_lang_pg.displays_subtitles())

    def test_draft_member_display(self):
        """Draft is visible to members in subtitle view."""
        self.video_pg.log_in(self.member.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.draft.video_id, 'en')
        self.assertTrue(self.video_lang_pg.displays_subtitles())

class TestCaseViewSubtitles(WebdriverTestCase):    
    NEW_BROWSER_PER_TEST_CASE = False

    @classmethod
    def setUpClass(cls):
        super(TestCaseViewSubtitles, cls).setUpClass()
        cls.data_utils = data_helpers.DataHelpers()
        cls.video_pg = video_page.VideoPage(cls)
        cls.user = UserFactory()
        cls.basic_team = TeamFactory.create(workflow_enabled=False,
                                            translate_policy=20, #any team
                                            subtitle_policy=20, #any team
                                            admin = cls.user,
                                            )

        cls.admin = UserFactory()
        cls.manager = UserFactory()
        cls.member = UserFactory()
        cls.team = TeamFactory(admin=cls.admin,
                               manager=cls.manager,
                               member=cls.member,
                               workflow_enabled=True,
                               translate_policy=20,
                               subtitle_policy=20,
                              )
        cls.workflow = WorkflowFactory(team = cls.team,
                                       autocreate_subtitle=True,
                                       autocreate_translate=True,
                                       approve_allowed = 10, # manager
                                       review_allowed = 10, # peer
                                       )

        #Create en source language 2 revisions - approved.
        cls.video, cls.tv = cls._add_team_video()
        cls._upload_subtitles(cls.video, 'en', cls.member, 
                              complete=False)
        cls._upload_subtitles(cls.video, 'en', cls.member)
        cls.data_utils.complete_review_task(cls.tv, 20, cls.admin)
        cls.data_utils.complete_approve_task(cls.tv, 20, cls.admin)
       
        #Add sv translation, reviewed
        cls._upload_translation(cls.video, 'sv', cls.member)
        cls.data_utils.complete_review_task(cls.tv, 20, cls.admin)

        #Add de translation complete waiting review
        cls._upload_translation(cls.video, 'de', cls.member)

        #Add ru translation, incomplete.
        cls._upload_translation(cls.video, 'ru', cls.member, 
                                complete=False)



    @classmethod
    def _upload_subtitles(cls, video, lc, user, complete=True):
        data = {
                    'language_code': lc,
                    'committer': user,
                    'video': video,
                    'complete': None,
                }
        if complete == True:
            data['action'] = 'complete'

        cls.data_utils.add_subs(**data)

    @classmethod
    def _upload_translation(cls, video, lc, user, complete=True):
        data = {
                    'language_code': lc,
                    'committer': user,
                    'video': video,
                    'complete': None
                }
        if complete == True:
            data['action'] = 'complete'

        cls.data_utils.add_subs(**data)

    @classmethod
    def _add_team_video(cls):
        video = VideoFactory(primary_audio_language_code='en')
        tv = TeamVideoFactory(team=cls.team, video=video)
        return video, tv

    def setUp(self):
        self.video_pg.open_video_page(self.video.video_id)


    def test_status_img_original_complete(self):
        """Orignal lang complete, shows complete status button.

        """
        _, en_status = self.video_pg.language_status('English')
        self.assertIn('status-complete', en_status)

    def test_tags_original(self):
        """Orignal lang has original tag.

        """
        en_tag, _ = self.video_pg.language_status('English')
        self.assertEqual('original', en_tag)

    def test_tags_needs_approval(self):
        """Language awaiting approval, shows needs approval tag.

        """
        sv_tag, _ = self.video_pg.language_status('Swedish')
        self.assertEqual('needs approval', sv_tag)

    def test_tags_needs_review(self):
        """Language awaiting review, shows needs review tag.

        """
        de_tag, _ = self.video_pg.language_status('German')
        self.assertEqual('needs review', de_tag)

    def test_tags_incomplete(self):
        """Incomplete language, shows incomplete tag.

        """
        ru_tag, _ = self.video_pg.language_status('Russian')
        self.assertEqual('incomplete', ru_tag)

    def test_status_img_translation_review(self):
        """Translation lang complete, shows needs review status button.

        """
        _, sv_status = self.video_pg.language_status('Swedish')
        self.assertIn('status-needs-review', sv_status)


    def test_status_img_incomplete(self):
        """Incomplete translation displays incomplete status button.

        """
        _, ru_status = self.video_pg.language_status('Russian')
        self.assertIn('status-incomplete', ru_status)

    def test_tags_original_review(self):
        """Tag display for original language needs review."""

        vid, tv = self._add_team_video()
        self._upload_subtitles(vid, 'en', self.member, 
                              complete=True)
        self.video_pg.open_video_page(vid.video_id)
        en_tag, _ = self.video_pg.language_status('English')
        self.assertEqual('original | needs review', en_tag)

    def test_tags_original_approve(self):
        """Tag display for original language needs approval."""
        vid, tv = self._add_team_video()
        self._upload_subtitles(vid, 'en', self.member, 
                              complete=True)
        self.data_utils.complete_review_task(tv, 20, self.admin)

        self.video_pg.open_video_page(vid.video_id)
        en_tag, _ = self.video_pg.language_status('English')
        self.assertEqual('original | needs approval', en_tag)

    def test_tags_original_incomplete(self):
        vid, tv = self._add_team_video()
        self._upload_subtitles(vid, 'en', self.member, 
                              complete=False)
        self.video_pg.open_video_page(vid.video_id)
        en_tag, _ = self.video_pg.language_status('English')
        self.assertEqual('original | incomplete', en_tag)
