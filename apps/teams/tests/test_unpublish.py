import mock
from django.test import TestCase
from django.test.client import Client

from subtitles import pipeline
from subtitles.models import SubtitleLanguage, SubtitleVersion
from teams.models import Task
from teams.forms import DeleteLanguageForm
from teams.permissions_const import ROLE_ADMIN, ROLE_OWNER, ROLE_MANAGER, ROLE_CONTRIBUTOR
from utils.factories import *

class UnpublishTestCase(TestCase):
    def setUp(self):
        self.team = TeamFactory(workflow_enabled=True)
        self.workflow = WorkflowFactory(team=self.team)
        self.user = UserFactory(is_staff=True)
        self.member = TeamMemberFactory(team=self.team, user=self.user,
                                        role=ROLE_ADMIN)
        self.video = VideoFactory(primary_audio_language_code='en')
        self.team_video = TeamVideoFactory(team=self.team, added_by=self.user,
                                           video=self.video)
        self.non_team_video = VideoFactory()
        # create a bunch of versions
        self.versions = [
            pipeline.add_subtitles(self.video, 'en', None) for i in xrange(5)
        ]
        self.language = self.video.get_primary_audio_subtitle_language()

    def check_version_counts(self, extent_count, public_count):
        subtitleversion_set = self.language.subtitleversion_set
        self.assertEquals(subtitleversion_set.extant().count(), extent_count)
        self.assertEquals(subtitleversion_set.public().count(), public_count)

    def check_task_count(self, count):
        qs = Task.objects.filter(language=self.language.language_code)
        self.assertEquals(qs.count(), count)

    def update_workflow(self, approve_allowed):
        if approve_allowed:
            self.workflow.approve_allowed = 10
        else:
            self.workflow.approve_allowed = 0
        self.workflow.save()

    def make_dependent_language(self, code, parent):
        sv = pipeline.add_subtitles(self.video, code, None, parents=[parent])
        return sv.subtitle_language

class UnpublishedVersionTest(UnpublishTestCase):
    # test what happens if the admin unpublishes subtitle versions
    def test_translation_tasks_not_blocked(self):
        # test that translation tasks are not blocked if the admin unpublishes
        # the version

        # make a translation task
        task = Task(team=self.team, team_video=self.team_video,
                    assignee=self.user, type=Task.TYPE_IDS['Translate'],
                     language='ru')
        task.save()
        # complete the translation task to create an approval task
        lang = self.make_dependent_language('ru', self.versions[-1])
        task.new_subtitle_version = lang.get_tip()
        approve_task = task.complete()
        # complete the parent subtitles language, so that that's not an issue
        # for is_blocked().
        self.language.subtitles_complete = True
        self.language.save()
        # unpublish the last version and check that that doesn't block the
        # approval task
        self.versions[-1].visibility_override = 'private'
        self.versions[-1].save()
        self.assertEquals(approve_task.is_blocked(), False)

class DeleteLanguageModelTest(UnpublishTestCase):
    def check_language_deleted(self, language):
        self.assertEquals(language.subtitleversion_set.extant().count(), 0)

    def check_language_not_deleted(self, language):
        self.assertNotEquals(language.subtitleversion_set.extant().count(), 0)

    def test_delete_language(self):
        self.language.nuke_language()
        self.check_language_deleted(self.language)

    def test_delete_tasks(self):
        # Add a review task for the last SubtitleVersion
        Task(team=self.team, team_video=self.team_video, assignee=None,
             language=self.language.language_code,
             type=Task.TYPE_IDS['Review'],
             new_subtitle_version=self.versions[-1]).save()
        # add a completed review task for the one before that
        Task(team=self.team, team_video=self.team_video, assignee=None,
             language=self.language.language_code,
             type=Task.TYPE_IDS['Review'],
             approved=Task.APPROVED_IDS['Approved'],
             new_subtitle_version=self.versions[-1]).save()
        # add a task for another video, but with the same language
        other_team_video = TeamVideoFactory(team=self.team,
                                            added_by=self.user)
        Task(team=self.team, team_video=other_team_video, assignee=None,
             language=self.language.language_code,
             type=Task.TYPE_IDS['Translate']).save()
        self.check_task_count(3)
        # deleting the language should delete both tasks for this video, but
        # not the task for the other video.
        self.language.nuke_language()
        self.check_task_count(1)

    def test_delete_translation_tasks(self):
        # We should delete translation tasks if there are no more languages
        # with public versions available.  However, we should not delete
        # in-progress translation tasks, or review/approve tasks.  Those can
        # continue alright with the forked language.

        # make a translation task
        Task(team=self.team, team_video=self.team_video, assignee=None,
             language='de', type=Task.TYPE_IDS['Translate']).save()
        # make an in-progress translation task
        Task(team=self.team, team_video=self.team_video,
             language='ja', type=Task.TYPE_IDS['Translate'],
             assignee=self.user).save()
        v = pipeline.add_subtitles(self.video, 'ja', None, action='save-draft')
        # make review/approve tasks
        TaskFactory.create_review(self.team_video, 'es', self.user)
        TaskFactory.create_approve(self.team_video, 'sv', self.user)
        # check initial task counts
        translate_qs = Task.objects.incomplete_translate().filter(
            language='de')
        in_progress_qs = Task.objects.incomplete_translate().filter(
            language='ja')
        review_qs = Task.objects.incomplete_review().filter(language='es')
        approve_qs = Task.objects.incomplete_approve().filter(language='sv')

        self.assertEquals(translate_qs.count(), 1)
        self.assertEquals(in_progress_qs.count(), 1)
        self.assertEquals(review_qs.count(), 1)
        self.assertEquals(approve_qs.count(), 1)
        # make a second language.  If we delete that language, we should still
        # keep translation tasks.
        other_lang_version = pipeline.add_subtitles(self.video, 'fr', None)
        other_lang_version.subtitle_language.nuke_language()
        self.assertEquals(translate_qs.count(), 1)
        self.assertEquals(in_progress_qs.count(), 1)
        self.assertEquals(review_qs.count(), 1)
        self.assertEquals(approve_qs.count(), 1)
        # but when we delete our original language, then there's no source
        # languages, so we should delete the translation task, but keep
        # in-progress translation tasks, as well as review tasks
        self.language.nuke_language()
        self.assertEquals(translate_qs.count(), 0)
        self.assertEquals(in_progress_qs.count(), 1)
        self.assertEquals(review_qs.count(), 1)
        self.assertEquals(approve_qs.count(), 1)

    def test_sublanguages(self):
        sub_lang1 = self.make_dependent_language('ru', self.versions[0])
        sub_lang2 = self.make_dependent_language('fr', sub_lang1.get_tip())
        forked_lang = self.make_dependent_language('de', self.versions[0])
        forked_lang.is_forked = True
        forked_lang.save()

        self.language.nuke_language()
        self.check_language_deleted(self.language)
        self.check_language_deleted(sub_lang1)
        self.check_language_deleted(sub_lang2)
        self.check_language_not_deleted(forked_lang)

class DeleteLanguageFormTest(UnpublishTestCase):
    def check_form_is_valid(self, verify_text, is_valid):
        form = DeleteLanguageForm(self.user, self.team, self.language, {
            'verify_text': verify_text,
        })
        self.assertEquals(form.is_valid(), is_valid)

    def test_verification(self):
        self.check_form_is_valid('', False)
        self.check_form_is_valid('incorrect phrase', False)
        self.check_form_is_valid('Yes I want to delete this language', True)
        self.check_form_is_valid('yes i want to delete this language', False)

    def test_sublanguages(self):
        sub_lang1 = self.make_dependent_language('ru', self.versions[0])
        sub_lang2 = self.make_dependent_language('fr', sub_lang1.get_tip())
        forked_lang = self.make_dependent_language('de', self.versions[0])
        forked_lang.is_forked = True
        forked_lang.save()
        form = DeleteLanguageForm(self.user, self.team, self.language)
        self.assertEquals(
            set([f.as_widget() for f in form.sublanguage_fields()]),
            set([form['delete_ru'].as_widget(),
                 form['delete_fr'].as_widget()]))
        bound_form = DeleteLanguageForm(self.user, self.team, self.language, {
            'verify_text': 'Yes I want to delete this language',
            'delete_fr': 1,
        })
        self.assertEquals(bound_form.errors, {})
        self.assertEquals(bound_form.is_valid(), True)
        self.assertEquals(bound_form.languages_to_fork(), [sub_lang1])

    def check_user_perm(self, user, should_have_permission):
        form = DeleteLanguageForm(user, self.team, self.language, {
            'verify_text': 'Yes I want to delete this language',
        })
        self.assertEquals(form.is_valid(), should_have_permission)

    def test_permissions(self):
        # only team admins and staff members should be able to submit the form
        self.check_user_perm(UserFactory(), False)
        self.check_user_perm(UserFactory(is_staff=True), True)
        for role in (ROLE_ADMIN, ROLE_OWNER):
            member = TeamMemberFactory(team=self.team, role=role)
            self.check_user_perm(member.user, True)
        for role in (ROLE_CONTRIBUTOR, ROLE_MANAGER):
            member = TeamMemberFactory(team=self.team, role=role)
            self.check_user_perm(member.user, False)

class DeleteLanguageViewTest(UnpublishTestCase):
    def setUp(self):
        UnpublishTestCase.setUp(self)
        self.client = Client()
        self.client.login(username=self.user.username, password='password')
        self.url = '/en/teams/%s/delete-language/%s/' % (
            self.team.slug, self.language.pk)

    def test_unpublish_with_forking(self):
        sub_lang1 = self.make_dependent_language('ru', self.versions[0])
        sub_lang2 = self.make_dependent_language('fr', sub_lang1.get_tip())
        forked_lang = self.make_dependent_language('de', self.versions[0])
        forked_lang.is_forked = True
        forked_lang.save()

        response = self.client.get(self.url)
        self.assertEquals(response.status_code, 200)

        response = self.client.post(self.url, {
            'verify_text': 'Yes I want to delete this language',
            'delete_ru': 1,
        })
        self.assertEquals(self.language.subtitleversion_set.extant().count(),
                          0)
        # we should delete russian, but not french or german
        self.assertEquals(sub_lang1.subtitleversion_set.extant().count(), 0)
        self.assertNotEquals(sub_lang2.subtitleversion_set.extant().count(),
                             0)
        self.assertNotEquals(forked_lang.subtitleversion_set.extant().count(),
                             0)

    def check_user_perm(self, user, should_have_permission):
        self.client.login(username=user.username, password='password')
        response = self.client.get(self.url)
        if should_have_permission:
            self.assertEquals(response.status_code, 200)
        else:
            self.assertRedirects(response,
                                 '/auth/login/?next=' + self.url,
                                 target_status_code=302)
        self.check_button_present(self.versions[-1], should_have_permission)

    def check_button_present(self, version, should_be_present):
        url = '/en/videos/%s/%s/%s/' % (
            version.video.video_id,
            version.subtitle_language.language_code,
            version.subtitle_language.pk,
        )
        response = self.client.get(url)
        button_html = '<a class="button" href="%s">' % self.url
        if should_be_present:
            self.assert_(button_html in response.content.decode('utf-8'))
        else:
            self.assert_(button_html not in response.content.decode('utf-8'))

    def test_permissions(self):
        self.check_user_perm(UserFactory(), False)
        self.check_user_perm(UserFactory(is_staff=True), True)
        for role in (ROLE_ADMIN, ROLE_OWNER):
            member = TeamMemberFactory(team=self.team, role=role)
            self.check_user_perm(member.user, True)
        for role in (ROLE_CONTRIBUTOR, ROLE_MANAGER):
            member = TeamMemberFactory(team=self.team, role=role)
            self.check_user_perm(member.user, False)

    def test_no_button_for_non_team_videos(self):
        non_team_version = pipeline.add_subtitles(self.non_team_video, 'en',
                                                  None)
        self.check_button_present(non_team_version, False)
