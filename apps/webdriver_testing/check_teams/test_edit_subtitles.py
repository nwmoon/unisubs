import os
import time
from utils.factories import *
from teams.models import TeamMember

from webdriver_testing.webdriver_base import WebdriverTestCase
from webdriver_testing import data_helpers
from webdriver_testing.pages.site_pages import video_language_page
from webdriver_testing.pages.site_pages import video_page
from webdriver_testing.data_factories import TeamManagerLanguageFactory
from webdriver_testing.data_factories import TeamLangPrefFactory

class TestCaseApprovalWorkflow(WebdriverTestCase):
    """TestSuite for display of Edit Subtitles button on a revision. """
    NEW_BROWSER_PER_TEST_CASE = False

    @classmethod
    def setUpClass(cls):
        super(TestCaseApprovalWorkflow, cls).setUpClass()
        cls.data_utils = data_helpers.DataHelpers()
        cls.video_lang_pg = video_language_page.VideoLanguagePage(cls)
        cls.video_pg = video_page.VideoPage(cls)
        cls.admin = UserFactory()
        cls.manager = UserFactory()
        cls.member = UserFactory()
        cls.team = TeamFactory(admin=cls.admin,
                               manager=cls.manager,
                               member=cls.member,
                               workflow_enabled=True,
                               translate_policy=20,
                               subtitle_policy=20,
                               task_assign_policy=10)
        cls.workflow = WorkflowFactory(team = cls.team,
                                       autocreate_subtitle=True,
                                       autocreate_translate=True,
                                       approve_allowed = 10, # manager
                                       review_allowed = 10, # peer
                                       )
        lang_list = ['en', 'ru', 'pt-br', 'de', 'sv']
        for language in lang_list:
            TeamLangPrefFactory.create(team=cls.team, language_code=language,
                                       preferred=True)

        cls.subs_dir = os.path.join(os.getcwd(), 'apps', 'webdriver_testing', 
                                    'subtitle_data') 


    def _upload_en_draft(self, video, subs, user, complete=False):
        data = {'language_code': 'en',
                     'video': video.pk,
                     'primary_audio_language_code': 'en',
                     'draft': open(subs),
                     'complete': int(complete),
                     'is_complete': complete,
                    }
        self.data_utils.upload_subs(user, **data)

    def _add_team_video(self):
        video = self.data_utils.create_video()
        tv = TeamVideoFactory(team=self.team, added_by=self.admin, video=video)
        return video, tv

    def _review_and_approve(self, tv):
        """Review and approve version.

        """
        if self.workflow.review_enabled:
            self.data_utils.complete_review_task(tv, 20, self.admin)
        if self.workflow.approve_enabled:
            self.data_utils.complete_approve_task(tv, 20, self.admin)

    def test_draft_task_assignee(self):
        """Task assignee must Edit Subtitles via task.

        """
        video, tv = self._add_team_video()
        subs = os.path.join(self.subs_dir, 'Timed_text.en.srt')
        self._upload_en_draft(video, subs, user=self.member)
        self.video_lang_pg.open_video_lang_page(video.video_id, 'en')
        self.video_lang_pg.log_in(self.member.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertEqual(self.video_lang_pg.EDIT_VIA_TASK_TEXT,
                         self.video_lang_pg.edit_subtitles_active())


    def test_reviewer_sent_back_assignee(self):
        """Assignee must Edit Subtitles via task after transcript fails review.

        """
        video, tv = self._add_team_video()
        subs = os.path.join(self.subs_dir, 'Timed_text.en.srt')
        self._upload_en_draft(video, subs, user=self.member, complete=True)
        #Reject transcript in review phase
        self.data_utils.complete_review_task(tv, 30, self.admin)
        self.video_lang_pg.open_video_lang_page(video.video_id, 'en')
        self.video_lang_pg.log_in(self.member.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertEqual(self.video_lang_pg.EDIT_VIA_TASK_TEXT,
                         self.video_lang_pg.edit_subtitles_active())


    def test_approver_sent_back_assignee(self):
        """Edit Subtitles NOT active for transcriber when transcript fails approve.

        """
        video, tv = self._add_team_video()
        subs = os.path.join(self.subs_dir, 'Timed_text.en.srt')
        self._upload_en_draft(video, subs, user=self.member, complete=True)
        #Accept transcript in review phase
        self.data_utils.complete_review_task(tv, 20, self.admin)
        #Reject transcript in the approve phase
        self.data_utils.complete_approve_task(tv, 30, self.admin)

        self.video_lang_pg.open_video_lang_page(video.video_id, 'en')
        self.video_lang_pg.log_in(self.member.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertEqual(self.video_lang_pg.EDIT_INACTIVE_TEXT, 
                         self.video_lang_pg.edit_subtitles_active())

    def test_review_not_started_transcriber(self):
        """Transcriber can not edit subtitles when waiting review.

        """
        video, tv = self._add_team_video()
        subs = os.path.join(self.subs_dir, 'Timed_text.en.srt')
        self._upload_en_draft(video, subs, user=self.member, complete=True)

        self.video_lang_pg.open_video_lang_page(video.video_id, 'en')
        self.video_lang_pg.log_in(self.member.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertEqual(self.video_lang_pg.EDIT_INACTIVE_TEXT,
                         self.video_lang_pg.edit_subtitles_active())


    def test_approver_sent_back_reviewer(self):
        """Reviewer must Edit Subtitles via task after fails approve.

        """
        reviewer = TeamMemberFactory(role=TeamMember.ROLE_CONTRIBUTOR,
                                     team=self.team).user

        video, tv = self._add_team_video()
        subs = os.path.join(self.subs_dir, 'Timed_text.en.srt')
        self._upload_en_draft(video, subs, user=self.member, complete=True)
        #Accept transcript in review phase
        self.data_utils.complete_review_task(tv, 20, reviewer)
        #Reject transcript in the approve phase
        self.data_utils.complete_approve_task(tv, 30, self.admin)

        self.video_lang_pg.open_video_lang_page(video.video_id, 'en')
        self.video_lang_pg.log_in(reviewer.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertEqual(self.video_lang_pg.EDIT_VIA_TASK_TEXT,
                         self.video_lang_pg.edit_subtitles_active())


    def test_draft_not_task_assignee(self):
        """Edit Subtitles not active for member not assigned with task.

        """
        member2 = TeamMemberFactory(role=TeamMember.ROLE_CONTRIBUTOR,
                                     team=self.team).user

        video, tv = self._add_team_video()
        subs = os.path.join(self.subs_dir, 'Timed_text.en.srt')
        self._upload_en_draft(video, subs, user=self.member)
        self.video_lang_pg.open_video_lang_page(video.video_id, 'en')
        self.video_lang_pg.log_in(member2.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertEqual(self.video_lang_pg.EDIT_INACTIVE_TEXT, 
                         self.video_lang_pg.edit_subtitles_active())

    def test_draft_team_admin(self):
        """Edit Subtitles not active for admin when task started by member.

        """
        video, tv = self._add_team_video()
        subs = os.path.join(self.subs_dir, 'Timed_text.en.srt')
        self._upload_en_draft(video, subs, user=self.member)
        self.video_lang_pg.open_video_lang_page(video.video_id, 'en')
        self.video_lang_pg.log_in(self.admin.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertEqual(self.video_lang_pg.EDIT_INACTIVE_TEXT,  
                         self.video_lang_pg.edit_subtitles_active())

    def test_non_member_sees_no_button(self):
        """Edit Subtitles not visible for non-member.
        """
        siteuser = UserFactory.create()
        video, tv = self._add_team_video()
        subs = os.path.join(self.subs_dir, 'Timed_text.en.srt')
        self._upload_en_draft(video, subs, user=self.member)
        self.video_lang_pg.open_video_lang_page(video.video_id, 'en')
        self.video_lang_pg.log_in(siteuser.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists())

    def test_guest_sees_no_button(self):
        """Edit Subtitles not visible for guest.
        """
        video, tv = self._add_team_video()
        subs = os.path.join(self.subs_dir, 'Timed_text.en.srt')
        self._upload_en_draft(video, subs, user=self.member)
        self.video_lang_pg.open_video_lang_page(video.video_id, 'en')
        self.video_lang_pg.log_out()
        self.video_lang_pg.page_refresh()
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists())



class TestCaseApprovalWorkflowPostEdit(WebdriverTestCase):
    """TestSuite for display of Edit Subtitles button on a revision. """
    NEW_BROWSER_PER_TEST_CASE = False

    @classmethod
    def setUpClass(cls):
        super(TestCaseApprovalWorkflowPostEdit, cls).setUpClass()
        cls.data_utils = data_helpers.DataHelpers()
        cls.video_lang_pg = video_language_page.VideoLanguagePage(cls)
        cls.video_pg = video_page.VideoPage(cls)

        cls.admin = UserFactory()
        cls.manager = UserFactory()
        cls.member = UserFactory()
        cls.team = TeamFactory(admin=cls.admin,
                               manager=cls.manager,
                               member=cls.member,
                               workflow_enabled=True,
                               translate_policy=20,
                               subtitle_policy=20,
                               task_assign_policy=10)
        
        cls.workflow = WorkflowFactory(team = cls.team,
                                       autocreate_subtitle=True,
                                       autocreate_translate=True,
                                       approve_allowed = 10, # manager
                                       review_allowed = 10, # peer
                                       )
        lang_list = ['en', 'ru', 'pt-br', 'de', 'sv']
        for language in lang_list:
            TeamLangPrefFactory.create(team=cls.team, language_code=language,
                                       preferred=True)

        cls.en_lc = TeamMemberFactory(role=TeamMember.ROLE_MANAGER,
                                      team=cls.team)
        TeamManagerLanguageFactory(member = cls.en_lc,
                                   language = 'en')
        cls.de_lc = TeamMemberFactory(role=TeamMember.ROLE_MANAGER,
                                             team=cls.team)
        TeamManagerLanguageFactory(member = cls.de_lc,
                                   language = 'de')

        cls.nonmember = UserFactory.create()
        cls.subs_dir = os.path.join(os.getcwd(), 'apps', 'webdriver_testing', 
                                    'subtitle_data') 
        cls.video, cls.tv = cls._add_team_video()
        subs = os.path.join(cls.subs_dir, 'Timed_text.en.srt')
        cls._upload_subs(cls.video, 'en', user=cls.member)
        cls._review_and_approve(cls.tv)
        cls._upload_subs(cls.video, 'de', user=cls.member)
        cls._review_and_approve(cls.tv)

        cls.video_lang_pg.open_video_lang_page(cls.video.video_id, 'en')


    @classmethod
    def _upload_subs(cls, video, lc, user):
        data = {'language_code': lc,
                     'video': video.pk,
                     'primary_audio_language_code': 'en',
                     'draft': open('apps/webdriver_testing/subtitle_data/Timed_text.en.srt'),
                     'complete': 1,
                     'is_complete': True,
                    }
        if lc != 'en':
            data['from_language_code'] = 'en'
        cls.data_utils.upload_subs(user, **data)

    @classmethod
    def _add_team_video(cls):
        video = cls.data_utils.create_video()
        tv = TeamVideoFactory(team=cls.team, added_by=cls.admin, video=video)
        return video, tv

    @classmethod
    def _review_and_approve(cls, tv):
        """Review and approve version.

        """
        if cls.workflow.review_enabled:
            cls.data_utils.complete_review_task(tv, 20, cls.admin)
        if cls.workflow.approve_enabled:
            cls.data_utils.complete_approve_task(tv, 20, cls.admin)

    def test_admin_approve_permissions(self):
        """Edit Subtitles inactive for below admin approval permissions.

        """
        self.workflow.approve_allowed = 20
        self.workflow.save()
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')

        #team admin
        self.video_lang_pg.log_in(self.admin.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertEqual('active',  
                         self.video_lang_pg.edit_subtitles_active(),
                         'team admin check failed')
 
        #team manager
        self.video_lang_pg.log_in(self.manager.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')
        self.assertEqual(self.video_lang_pg.EDIT_INACTIVE_TEXT,
                         self.video_lang_pg.edit_subtitles_active(), 
                         'team manager check failed')

        #en lang coordinator
        self.video_lang_pg.log_in(self.en_lc.user.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')
        self.assertEqual(self.video_lang_pg.EDIT_INACTIVE_TEXT,
                         self.video_lang_pg.edit_subtitles_active(), 
                         'same-lang lc check failed')

        #de lang coordinator
        self.video_lang_pg.log_in(self.de_lc.user.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')
        self.assertEqual(self.video_lang_pg.EDIT_INACTIVE_TEXT,
                         self.video_lang_pg.edit_subtitles_active(), 
                         'other lang lc check failed')

        #team member
        self.video_lang_pg.log_in(self.member.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')
        self.assertEqual(self.video_lang_pg.EDIT_INACTIVE_TEXT,
                         self.video_lang_pg.edit_subtitles_active(), 
                         'team member check failed')
      
        #non-member has no button
        self.video_lang_pg.log_in(self.nonmember.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'non-member check failed')

        # Guest user has no button
        self.video_lang_pg.log_out()
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'Guest user check failed')

    def test_manager_approve_permissions(self):
        """Edit Subtitles inactive for below admin approval permissions.

        """
        self.workflow.approve_allowed = 10
        self.workflow.save()
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')

        #team admin
        self.video_lang_pg.log_in(self.admin.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertEqual('active',  
                         self.video_lang_pg.edit_subtitles_active(),
                         'team admin check failed')
 
        #team manager
        self.video_lang_pg.log_in(self.manager.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')
        self.assertEqual('active',  
                         self.video_lang_pg.edit_subtitles_active(),
                         'team manager check failed')

        #team member
        self.video_lang_pg.log_in(self.member.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')
        self.assertEqual(self.video_lang_pg.EDIT_INACTIVE_TEXT,
                         self.video_lang_pg.edit_subtitles_active(), 
                         'team member check failed')
      
        #non-member has no button
        self.video_lang_pg.log_in(self.nonmember.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'non-member check failed')

        # Guest user has no button
        self.video_lang_pg.log_out()
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'Guest user check failed')

        #de lang coordinator
        self.video_lang_pg.log_in(self.de_lc.user.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')
        self.assertEqual(self.video_lang_pg.EDIT_INACTIVE_TEXT,
                         self.video_lang_pg.edit_subtitles_active(), 
                         'lc as contributor check failed')

        #de lang coordinator german subs
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'de')
        self.assertEqual('active',  
                         self.video_lang_pg.edit_subtitles_active(),
                         'de lc on de subs check failed')

        #en lang coordinator
        self.video_lang_pg.log_in(self.en_lc.user.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')
        self.assertEqual('active',  
                         self.video_lang_pg.edit_subtitles_active(),
                         'en lc on en subs lc check failed')


class TestCaseNoReviews(WebdriverTestCase):
    """TestSuite for display of Edit Subtitles button on a revision. """
    NEW_BROWSER_PER_TEST_CASE = False

    @classmethod
    def setUpClass(cls):
        super(TestCaseNoReviews, cls).setUpClass()
        cls.data_utils = data_helpers.DataHelpers()
        cls.video_lang_pg = video_language_page.VideoLanguagePage(cls)
        cls.video_pg = video_page.VideoPage(cls)

        cls.admin = UserFactory()
        cls.manager = UserFactory()
        cls.member = UserFactory()
        cls.team = TeamFactory(admin=cls.admin,
                               manager=cls.manager,
                               member=cls.member,
                               workflow_enabled=True,
                               translate_policy=20,
                               subtitle_policy=20,
                               task_assign_policy=10)
        cls.workflow = WorkflowFactory(team = cls.team,
                                       autocreate_subtitle=True,
                                       autocreate_translate=True,
                                       )
        lang_list = ['en', 'ru', 'pt-br', 'de', 'sv']
        for language in lang_list:
            TeamLangPrefFactory.create(team=cls.team, language_code=language,
                                       preferred=True)

        cls.subs_dir = os.path.join(os.getcwd(), 'apps', 'webdriver_testing', 
                                    'subtitle_data') 


    def _upload_en_draft(self, video, subs, user, complete=False):
        data = {'language_code': 'en',
                     'video': video.pk,
                     'primary_audio_language_code': 'en',
                     'draft': open(subs),
                     'complete': int(complete),
                     'is_complete': complete,
                    }
        self.data_utils.upload_subs(user, **data)

    def _add_team_video(self):
        video = self.data_utils.create_video()
        tv = TeamVideoFactory(team=self.team, added_by=self.admin, video=video)
        return video, tv

    def tearDown(self):
        if self.team.task_assign_policy > 10: #reset to default start value
            self.team.task_assign_policy = 10
            self.team.save()
        if self.team.subtitle_policy > 20:
            self.team.subtitle_policy = 20
            self.team.save()
        

    def test_draft_task_assignee(self):
        """Edit Subtitles inactive for task assignee, edit via tasks panel.

        """
        video, tv = self._add_team_video()
        subs = os.path.join(self.subs_dir, 'Timed_text.en.srt')
        self._upload_en_draft(video, subs, user=self.member)
        self.video_lang_pg.open_video_lang_page(video.video_id, 'en')
        self.video_lang_pg.log_in(self.member.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertEqual(self.video_lang_pg.EDIT_VIA_TASK_TEXT,
                         self.video_lang_pg.edit_subtitles_active())


    def test_draft_task_unassigned(self):
        """Edit Subtitles inactive for unassigned task, edit via tasks panel.

        """
        member2 = TeamMemberFactory(role=TeamMember.ROLE_CONTRIBUTOR,
                                    team=self.team).user

        video, tv = self._add_team_video()
        subs = os.path.join(self.subs_dir, 'Timed_text.en.srt')
        self._upload_en_draft(video, subs, user=self.member)
        task = list(tv.task_set.incomplete_subtitle().filter(language='en'))[0]
        task.assignee = None
        task.save()
        self.video_lang_pg.open_video_lang_page(video.video_id, 'en')
        self.video_lang_pg.log_in(member2.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertEqual(self.video_lang_pg.EDIT_VIA_TASK_TEXT, 
                         self.video_lang_pg.edit_subtitles_active())


    def test_draft_not_task_assignee(self):
        """Edit Subtitles inactive for member not assigned task, no permission.

        """
        member2 = TeamMemberFactory(role=TeamMember.ROLE_CONTRIBUTOR,
                                    team=self.team).user
        video, tv = self._add_team_video()
        subs = os.path.join(self.subs_dir, 'Timed_text.en.srt')
        self._upload_en_draft(video, subs, user=self.member)
        self.video_lang_pg.open_video_lang_page(video.video_id, 'en')
        self.video_lang_pg.log_in(member2.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertEqual(self.video_lang_pg.EDIT_INACTIVE_TEXT, 
                         self.video_lang_pg.edit_subtitles_active())


    def test_public_non_member(self):
        """Guest user will not see Edit Subtitles for published version.

        """
        siteuser = UserFactory.create()
        video, tv = self._add_team_video()
        subs = os.path.join(self.subs_dir, 'Timed_text.en.srt')
        self._upload_en_draft(video, subs, user=self.member, complete=True)
        self.video_lang_pg.open_video_lang_page(video.video_id, 'en')
        self.video_lang_pg.log_in(siteuser.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists())


class TestCaseNoReviewsPostEdit(WebdriverTestCase):
    """TestSuite for post-edit permissions, no workflow team. 

        Changed with gh-483 using subtitle permission to determine post edits.
    """
    NEW_BROWSER_PER_TEST_CASE = False

    @classmethod
    def setUpClass(cls):
        super(TestCaseNoReviewsPostEdit, cls).setUpClass()
        cls.data_utils = data_helpers.DataHelpers()
        cls.video_lang_pg = video_language_page.VideoLanguagePage(cls)
        cls.video_pg = video_page.VideoPage(cls)
        cls.nonmember = UserFactory.create()
        cls.admin = UserFactory()
        cls.manager = UserFactory()
        cls.member = UserFactory()
        cls.team = TeamFactory(admin=cls.admin,
                               manager=cls.manager,
                               member=cls.member,
                               workflow_enabled=False,
                              )

        lang_list = ['en', 'de', 'fr']
        for language in lang_list:
            TeamLangPrefFactory.create(team=cls.team, language_code=language,
                                       preferred=True)

        cls.member2 = TeamMemberFactory(team=cls.team, 
                                        role=TeamMember.ROLE_CONTRIBUTOR).user

        cls.video = VideoFactory()
        cls.tv = TeamVideoFactory(team=cls.team, 
                                  video=cls.video)
        cls._upload_subs(cls.video, 'en', user=cls.member)
        cls._upload_subs(cls.video, 'fr', user=cls.member)
        cls.video_lang_pg.open_video_lang_page(cls.video.video_id, 'en')


    @classmethod
    def _upload_subs(cls, video, lc, user):
        data = {'language_code': lc,
                     'video': cls.video.pk,
                     'primary_audio_language_code': 'en',
                     'draft': open('apps/webdriver_testing/subtitle_data'
                                   '/Timed_text.en.srt'),
                     'complete': 1,
                     'is_complete': True
                    }
        cls.data_utils.upload_subs(user, **data)

    def test_admin_edit_permissions(self):
        """Edit Subtitles inactive for below admin permissions.

        """
        self.team.subtitle_policy = 40
        self.team.translate_policy = 40

        self.team.save()

        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')

        #team admin
        self.video_lang_pg.log_in(self.admin.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertEqual('active',  
                         self.video_lang_pg.edit_subtitles_active(),
                         'team admin check failed')
 
        #team manager
        self.video_lang_pg.log_in(self.manager.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'team member check failed')
 
        #team member
        self.video_lang_pg.log_in(self.member.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'team member check failed')
      
        #non-member has no button
        self.video_lang_pg.log_in(self.nonmember.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'non-member check failed')

        # Guest user has no button
        self.video_lang_pg.log_out()
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'Guest user check failed')


    def test_admin_translate_permissions(self):
        """Edit Subtitles inactive for below admin permissions.

        """
        self.team.translate_policy = 40
        self.team.subtitle_policy = 40
        self.team.save()

        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'fr')
        #team admin
        self.video_lang_pg.log_in(self.admin.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertEqual('active',  
                         self.video_lang_pg.edit_subtitles_active(),
                         'team admin check failed')
 
        #team manager
        self.video_lang_pg.log_in(self.manager.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'team manager check failed')

        #team member
        self.video_lang_pg.log_in(self.member.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'team member check failed')


        #non-member has no button
        self.video_lang_pg.log_in(self.nonmember.username, 'password')
        self.video_lang_pg.page_refresh()

        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'fr')
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'non-member check failed')

        # Guest user has no button
        self.video_lang_pg.log_out()
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'fr')
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'Guest user check failed')



    def test_manager_subtitle_permissions(self):
        """Edit Subtitles inactive below manager permissions.
        """
        self.team.subtitle_policy = 30
        self.team.translate_policy = 30

        self.team.save()

        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')

        #team admin
        self.video_lang_pg.log_in(self.admin.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertEqual('active',  
                         self.video_lang_pg.edit_subtitles_active(),
                         'team admin check failed')
 
        #team manager
        self.video_lang_pg.log_in(self.manager.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertEqual('active',  
                         self.video_lang_pg.edit_subtitles_active(),
                         'team manager check failed')
 
        #team member
        self.video_lang_pg.log_in(self.member.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'team member check failed')
      
        #non-member has no button
        self.video_lang_pg.log_in(self.nonmember.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'non-member check failed')

        # Guest user has no button
        self.video_lang_pg.log_out()
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'Guest user check failed')

    def test_manager_translate_permissions(self):
        """Edit Subtitles inactive for below manager permissions.

        """
        self.team.translate_policy = 30
        self.team.subtitle_policy = 30

        self.team.save()

        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'fr')
        #team admin
        self.video_lang_pg.log_in(self.admin.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertEqual('active',  
                         self.video_lang_pg.edit_subtitles_active(),
                         'team admin check failed')
 
        #team manager
        self.video_lang_pg.log_in(self.manager.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertEqual('active',  
                         self.video_lang_pg.edit_subtitles_active(),
                         'team manager check failed')
 
        #team member
        self.video_lang_pg.log_in(self.member.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'team member check failed')

        #non-member has no button
        self.video_lang_pg.log_in(self.nonmember.username, 'password')
        self.video_lang_pg.page_refresh()

        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'fr')
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'non-member check failed')

        # Guest user has no button
        self.video_lang_pg.log_out()
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'fr')
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'Guest user check failed')


    def test_member_subtitle_permissions(self):
        """Edit Subtitles inactive below member permissions.
        """
        self.team.subtitle_policy = 20
        self.team.translate_policy = 20
        self.team.save()

        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')

        #team admin
        self.video_lang_pg.log_in(self.admin.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertEqual('active',  
                         self.video_lang_pg.edit_subtitles_active(),
                         'team admin check failed')
 
        #team manager
        self.video_lang_pg.log_in(self.manager.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertEqual('active',  
                         self.video_lang_pg.edit_subtitles_active(),
                         'team manager check failed')
 
        #team member
        self.video_lang_pg.log_in(self.member.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertEqual('active',  
                         self.video_lang_pg.edit_subtitles_active(),
                         'team member check failed')
      
        #non-member has no button
        self.video_lang_pg.log_in(self.nonmember.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'non-member check failed')

        # Guest user has no button
        self.video_lang_pg.log_out()
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'Guest user check failed')

    def test_member_translate_permissions(self):
        """Edit Subtitles inactive for below memeber permissions.

        """
        self.team.subtitle_policy = 20
        self.team.translate_policy = 20
        self.team.save()

        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'fr')
        #team admin
        self.video_lang_pg.log_in(self.admin.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertEqual('active',  
                         self.video_lang_pg.edit_subtitles_active(),
                         'team admin check failed')
 
        #team manager
        self.video_lang_pg.log_in(self.manager.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertEqual('active',  
                         self.video_lang_pg.edit_subtitles_active(),
                         'team manager check failed')
 
        #team member
        self.video_lang_pg.log_in(self.member.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertEqual('active',  
                         self.video_lang_pg.edit_subtitles_active(),
                         'team member check failed')

        #non-member has no button
        self.video_lang_pg.log_in(self.nonmember.username, 'password')
        self.video_lang_pg.page_refresh()

        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'fr')
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'non-member check failed')

        # Guest user has no button
        self.video_lang_pg.log_out()
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'fr')
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'Guest user check failed')

class TestCaseNoWorkflow(WebdriverTestCase):
    """TestSuite for display of Edit Subtitles button on a team revision """
    NEW_BROWSER_PER_TEST_CASE = False

    @classmethod
    def setUpClass(cls):
        super(TestCaseNoWorkflow, cls).setUpClass()
        cls.data_utils = data_helpers.DataHelpers()
        cls.video_lang_pg = video_language_page.VideoLanguagePage(cls)
        cls.video_pg = video_page.VideoPage(cls)
        cls.nonmember = UserFactory.create()

        cls.admin = UserFactory()
        cls.manager = UserFactory()
        cls.member = UserFactory()
        cls.team = TeamFactory(admin=cls.admin,
                               manager=cls.manager,
                               member=cls.member,
                               workflow_enabled=False,
                               translate_policy=20,
                               subtitle_policy=20,
                              )
        cls.video = VideoFactory()
        cls.tv = TeamVideoFactory(team=cls.team, 
                                  added_by=cls.admin, 
                                  video=cls.video)
        cls._upload_subs(cls.video, 'en', user=cls.member)
        cls._upload_subs(cls.video, 'fr', user=cls.member)
        cls.video_lang_pg.open_page('/')


    @classmethod
    def _upload_subs(cls, video, lc, user):
        data = {'language_code': lc,
                     'video': cls.video.pk,
                     'primary_audio_language_code': 'en',
                     'draft': open('apps/webdriver_testing/subtitle_data'
                                   '/Timed_text.en.srt'),
                     'complete': 1,
                     'is_complete': True
                    }
        cls.data_utils.upload_subs(user, **data)


    def test_admin_edit_permissions(self):
        """Edit Subtitles inactive for below admin permissions.

        """
        self.team.subtitle_policy = 40
        self.team.translate_policy = 40
        self.team.save()
        #team admin
        self.video_lang_pg.log_in(self.admin.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')
        self.assertEqual('active',  
                         self.video_lang_pg.edit_subtitles_active(),
                         'team admin check failed')
 
        #team manager
        self.video_lang_pg.log_in(self.manager.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'team member check failed')
 
        #team member
        self.video_lang_pg.log_in(self.member.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'team member check failed')
        #non-member has no button
        self.video_lang_pg.log_in(self.nonmember.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'non-member check failed')

        # Guest user has no button
        self.video_lang_pg.log_out()
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'Guest user check failed')


    def test_admin_translate_permissions(self):
        """Edit Subtitles inactive for below admin permissions.

        """
        self.team.translate_policy = 40
        self.team.subtitle_policy = 40
        self.team.save()
        #team admin
        self.video_lang_pg.log_in(self.admin.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'fr')
        self.assertEqual('active',  
                         self.video_lang_pg.edit_subtitles_active(),
                         'team admin check failed')
 
        #team manager
        self.video_lang_pg.log_in(self.manager.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'team manager check failed')

        #team member
        self.video_lang_pg.log_in(self.member.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'team member check failed')

        #non-member has no button
        self.video_lang_pg.log_in(self.nonmember.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')

        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'fr')
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'non-member check failed')

        # Guest user has no button
        self.video_lang_pg.log_out()
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'fr')
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'Guest user check failed')



    def test_manager_subtitle_permissions(self):
        """Edit Subtitles inactive below manager permissions.
        """
        self.team.subtitle_policy = 30
        self.team.translate_policy = 30
        self.team.save()
        #team admin
        self.video_lang_pg.log_in(self.admin.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')
        self.assertEqual('active',  
                         self.video_lang_pg.edit_subtitles_active(),
                         'team admin check failed')
 
        #team manager
        self.video_lang_pg.log_in(self.manager.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'fr')
        self.assertEqual('active',  
                         self.video_lang_pg.edit_subtitles_active(),
                         'team manager check failed')
 
        #team member
        self.video_lang_pg.log_in(self.member.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'fr')
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'team member check failed')
      
        #non-member has no button
        self.video_lang_pg.log_in(self.nonmember.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'fr')
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'non-member check failed')

        # Guest user has no button
        self.video_lang_pg.log_out()
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'Guest user check failed')

    def test_manager_translate_permissions(self):
        """Edit Subtitles inactive for below manager permissions.

        """
        self.team.translate_policy = 30
        self.team.subtitle_policy = 30
        self.team.save()

        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'fr')
        #team admin
        self.video_lang_pg.log_in(self.admin.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'fr')
        self.assertEqual('active',  
                         self.video_lang_pg.edit_subtitles_active(),
                         'team admin check failed')
 
        #team manager
        self.video_lang_pg.log_in(self.manager.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'fr')
        self.assertEqual('active',  
                         self.video_lang_pg.edit_subtitles_active(),
                         'team manager check failed')
 
        #team member
        self.video_lang_pg.log_in(self.member.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'fr')
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'team member check failed')

        #non-member has no button
        self.video_lang_pg.log_in(self.nonmember.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'fr')
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'non-member check failed')

        # Guest user has no button
        self.video_lang_pg.log_out()
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'fr')
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'Guest user check failed')


    def test_member_subtitle_permissions(self):
        """Edit Subtitles inactive below member permissions.
        """
        self.team.subtitle_policy = 20
        self.team.translate_policy = 20
        self.team.save()

        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')

        #team admin
        self.video_lang_pg.log_in(self.admin.username, 'password')
        self.video_lang_pg.page_refresh()
        self.assertEqual('active',  
                         self.video_lang_pg.edit_subtitles_active(),
                         'team admin check failed')
 
        #team manager
        self.video_lang_pg.log_in(self.manager.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')
        self.assertEqual('active',  
                         self.video_lang_pg.edit_subtitles_active(),
                         'team manager check failed')
 
        #team member
        self.video_lang_pg.log_in(self.member.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')
        self.assertEqual('active',  
                         self.video_lang_pg.edit_subtitles_active(),
                         'team member check failed')
      
        #non-member has no button
        self.video_lang_pg.log_in(self.nonmember.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'non-member check failed')

        # Guest user has no button
        self.video_lang_pg.log_out()
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'Guest user check failed')

    def test_member_translate_permissions(self):
        """Edit Subtitles inactive for below memeber permissions.

        """
        self.team.subtitle_policy = 20
        self.team.translate_policy = 20
        self.team.save()

        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'fr')
        #team admin
        self.video_lang_pg.log_in(self.admin.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'fr')
        self.assertEqual('active',  
                         self.video_lang_pg.edit_subtitles_active(),
                         'team admin check failed')
 
        #team manager
        self.video_lang_pg.log_in(self.manager.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'fr')
        self.assertEqual('active',  
                         self.video_lang_pg.edit_subtitles_active(),
                         'team manager check failed')
 
        #team member
        self.video_lang_pg.log_in(self.member.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'fr')
        self.assertEqual('active',  
                         self.video_lang_pg.edit_subtitles_active(),
                         'team member check failed')

        #non-member has no button
        self.video_lang_pg.log_in(self.nonmember.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'fr')

        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'fr')
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'non-member check failed')

        # Guest user has no button
        self.video_lang_pg.log_out()
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'fr')
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists(),
                         'Guest user check failed')




class TestCaseAdminUnpublish(WebdriverTestCase):
    """Edit Subtitles button display on a revision after latest version set private. """
    NEW_BROWSER_PER_TEST_CASE = False

    @classmethod
    def setUpClass(cls):
        super(TestCaseAdminUnpublish, cls).setUpClass()
        cls.data_utils = data_helpers.DataHelpers()
        cls.video_lang_pg = video_language_page.VideoLanguagePage(cls)
        cls.video_pg = video_page.VideoPage(cls)

        cls.admin = UserFactory()
        cls.manager = UserFactory()
        cls.member = UserFactory()
        cls.team = TeamFactory(admin=cls.admin,
                               manager=cls.manager,
                               member=cls.member,
                               workflow_enabled=True,
                               translate_policy=20,
                               subtitle_policy=20,
                               task_assign_policy=10,
                              )
        cls.workflow = WorkflowFactory(team = cls.team,
                                       autocreate_subtitle=True,
                                       autocreate_translate=True,
                                       approve_allowed = 10, # manager
                                       review_allowed = 10, # peer
                                       )
        lang_list = ['en', 'ru', 'pt-br', 'de', 'sv']
        for language in lang_list:
            TeamLangPrefFactory.create(team=cls.team, language_code=language,
                                       preferred=True)
        cls.subs_dir = os.path.join(os.getcwd(), 'apps', 'webdriver_testing', 
                                    'subtitle_data') 
        cls.video, cls.tv = cls._create_source_with_multiple_revisions()
        cls.video_lang_pg.open_video_lang_page(cls.video.video_id, 'en')

    def tearDown(self):
        if self.team.task_assign_policy > 10: #reset to default start value
            self.team.task_assign_policy = 10
            self.team.save()

    @classmethod
    def _upload_en_draft(cls, video, subs, user, complete=False):
        data = {'language_code': 'en',
                     'video': video.pk,
                     'primary_audio_language_code': 'en',
                     'draft': open(subs),
                     'complete': int(complete),
                     'is_complete': complete,
                    }
        cls.data_utils.upload_subs(user, **data)

    @classmethod
    def _add_team_video(cls):
        video = cls.data_utils.create_video()
        tv = TeamVideoFactory(team=cls.team, added_by=cls.admin, video=video)
        return video, tv

    @classmethod
    def _create_source_with_multiple_revisions(cls):
        cls.logger.info("Create a team video with 4 revisions:")
        cls.logger.info("""
                            v1: private (draft version only)
                            v2: private (draft version only)
                            v3: public (reviewed and approved)
                            v4: public 
                        """)
        video, tv = cls._add_team_video()

        #REV1 (draft)
        rev1_subs = os.path.join(cls.subs_dir, 'Timed_text.en.srt')
        cls._upload_en_draft(video, rev1_subs, user=cls.member)

        #REV2 (draft - marked complete)
        rev2_subs = os.path.join(cls.subs_dir, 'Timed_text.rev2.en.srt')
        cls._upload_en_draft(video, rev2_subs, user=cls.member, complete=True)

        #REV3, reviewed (private)
        rev3_subs = os.path.join(cls.subs_dir, 'Timed_text.rev3.en.srt')
        cls._upload_en_draft(video, rev3_subs, user=cls.admin, complete=True)
        cls.data_utils.complete_review_task(tv, 20, cls.admin)
        cls.data_utils.complete_approve_task(tv, 20, cls.admin)


        #REV4, approved (public)
        rev4_subs = os.path.join(cls.subs_dir, 'Timed_text.rev4.en.srt')
        cls._upload_en_draft(video, rev4_subs, user=cls.admin, complete=True)
        cls.en = video.subtitle_language('en')
        en_v4 = cls.en.get_tip(public=True)
        en_v4.visibility_override = 'private'
        en_v4.save() 
        return video, tv

    def tearDown(self):
        self.browser.execute_script("window.stop()")
        time.sleep(1) 

    def test_unpublished_admin(self):
        """Admin can always edit unpublished version.

        """
        self.video_lang_pg.log_in(self.admin.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')
        self.assertEqual('active',
                         self.video_lang_pg.edit_subtitles_active())

    def test_unpublished_owner(self):
        """Owner can always edit unpublished version.

        """
        owner = TeamMemberFactory(team=self.team).user 
        self.video_lang_pg.log_in(owner.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')
        self.assertEqual('active',
                         self.video_lang_pg.edit_subtitles_active())

    def test_unpublished_member_can_not_edit(self):
        """Member can't edit unpublished version when create tasks is manager level.

        """
        self.team.task_assign_policy = 30
        self.team.save()
        team_member = TeamMemberFactory(role=TeamMember.ROLE_CONTRIBUTOR,team=self.team).user
        self.video_lang_pg.log_in(team_member.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')
        
        self.assertEqual(self.video_lang_pg.EDIT_INACTIVE_TEXT,
                         self.video_lang_pg.edit_subtitles_active())

    def test_unpublished_guest_sees_no_button(self):
        """Guest sees no Edit Subtitles button after version unpublished.

        """
        self.video_lang_pg.log_out()
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists())

    def test_unpublished_non_member_sees_no_button(self):
        """Edit Subtitles not visible for non-member.
        """
        siteuser = UserFactory.create()
        self.video_lang_pg.log_in(siteuser.username, 'password')
        self.video_lang_pg.open_video_lang_page(self.video.video_id, 'en')
        self.assertFalse(self.video_lang_pg.edit_subtitles_exists())

