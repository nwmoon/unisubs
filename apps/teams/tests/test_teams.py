# -*- coding: utf-8 -*-

from __future__ import absolute_import

from datetime import datetime, timedelta, date
import os, re, json

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.core.urlresolvers import reverse
from django.db.models import ObjectDoesNotExist
from django.test import TestCase

from auth.models import CustomUser as User
from haystack.query import SearchQuerySet
from messages.models import Message
from subtitles import models as sub_models
from subtitles.models import SubtitleLanguage
from subtitles.pipeline import add_subtitles
from teams.forms import InviteForm
from teams import moderation_const as MODERATION
from teams import tasks
from teams.cache import invalidate_lang_preferences
from teams.models import (
    Team, Invite, TeamVideo, Application, TeamMember,
    TeamLanguagePreference, Partner, TeamNotificationSetting,
    InviteExpiredException
)
from teams.permissions import add_role
from teams.rpc import TeamsApiClass
from teams.templatetags import teams_tags
from teams.tests.teamstestsutils import refresh_obj, reset_solr
from utils import test_utils
from utils import translation
from utils.factories import *
from utils.rpc import Error, Msg
from videos import metadata_manager
from videos.models import Video, SubtitleVersion
from videos.search_indexes import VideoIndex

LANGUAGE_RE = re.compile(r"S_([a-zA-Z\-]+)")

def fix_teams_roles(teams=None):
    for t in teams or Team.objects.all():
       for member in t.members.all():
           add_role(t, member.user,  t.members.all()[0], member.role)

class TestNotification(TestCase):
    def setUp(self):
        fix_teams_roles()
        self.team = TeamFactory()
        self.user = UserFactory()
        self.tm = TeamMember(team=self.team, user=self.user)
        self.tm.save()
        self.tv1 = TeamVideoFactory(team=self.team, added_by=self.user)
        self.tv2 = TeamVideoFactory(team=self.team, added_by=self.user)

    def test_new_team_video_notification(self):
        #check initial data
        self.assertEqual(self.team.teamvideo_set.count(), 2)
        self.assertEqual(self.team.users.count(), 1)


        #mockup for send_templated_email to test context of email
        import utils

        send_templated_email = utils.send_templated_email

        def send_templated_email_mockup(to, subject, body_template, body_dict, *args, **kwargs):
            send_templated_email_mockup.context = body_dict
            send_templated_email(to, subject, body_template, body_dict, *args, **kwargs)

        utils.send_templated_email = send_templated_email_mockup
        reload(tasks)

        #test notification about two new videos
        TeamVideo.objects.filter(pk__in=[self.tv1.pk, self.tv2.pk]).update(created=datetime.today())
        self.assertEqual(TeamVideo.objects.filter(created__gt=self.team.last_notification_time).count(), 2)
        mail.outbox = []
        self.user.notify_by_email = True
        self.user.save()
        tasks.add_videos_notification_daily.delay()
        self.team = Team.objects.get(pk=self.team.pk)
        self.assertEqual(len(mail.outbox), 1)

        self.assertIn(self.user.email, mail.outbox[0].to[0] )
        self.assertEqual(len(send_templated_email_mockup.context['team_videos']), 2)

        self.user.notify_by_email = False
        self.user.save()
        #test if user turn off notification
        self.user.is_active = False
        self.user.save()
        mail.outbox = []
        tasks.add_videos_notification_daily.delay()
        self.team = Team.objects.get(pk=self.team.pk)
        self.assertEqual(len(mail.outbox), 0)

        self.user.is_active = True
        self.user.notify_by_email = False
        self.user.save()
        mail.outbox = []
        tasks.add_videos_notification_daily.delay()
        self.team = Team.objects.get(pk=self.team.pk)
        self.assertEqual(len(mail.outbox), 0)


        self.tm.save()

        self.user.notify_by_email = True
        self.user.save()
        #test notification if one video is new
        created_date = self.team.last_notification_time + timedelta(seconds=10)
        TeamVideo.objects.filter(pk=self.tv1.pk).update(created=created_date)

        self.assertEqual(TeamVideo.objects.filter(created__gt=self.team.last_notification_time).count(), 1)
        mail.outbox = []
        tasks.add_videos_notification_daily.delay()
        self.team = Team.objects.get(pk=self.team.pk)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(send_templated_email_mockup.context['team_videos']), 1)
        self.assertEqual(send_templated_email_mockup.context['team_videos'][0], self.tv1)

        #test notification if all videos are already old
        created_date = self.team.last_notification_time - timedelta(seconds=10)
        TeamVideo.objects.filter(team=self.team).update(created=created_date)
        self.assertEqual(TeamVideo.objects.filter(created__gt=self.team.last_notification_time).count(), 0)
        mail.outbox = []
        tasks.add_videos_notification_daily.delay()
        self.team = Team.objects.get(pk=self.team.pk)
        self.assertEqual(len(mail.outbox), 0)

    def test_notify_lookup(self):
        p = Partner.objects.create(name='p', slug='p')
        t1 = Team.objects.create(name='t1', slug='t1', partner=p)
        t2 = Team.objects.create(name='t2', slug='t2')
        t3 = Team.objects.create(name='t3', slug='t3')
        t4 = Team.objects.create(name='t4', slug='t4')

        TeamNotificationSetting.objects.create(partner=p)
        TeamNotificationSetting.objects.create(team=t2)
        TeamNotificationSetting.objects.create(team=t4)

        TeamNotificationSetting.objects.notify_team(t1.pk, 'x')
        TeamNotificationSetting.objects.notify_team(t2.pk, 'x')
        TeamNotificationSetting.objects.notify_team(t3.pk, 'x')

class NeedsNewVideoNotificationTest(TestCase):
    def make_team(self, notify_interval, add_video=True):
        team = TeamFactory(notify_interval=notify_interval)
        member = TeamMemberFactory(team=team)
        if add_video:
            TeamVideoFactory(team=team, added_by=member.user)
        return team

    def setUp(self):
        self.t1 = self.make_team(Team.NOTIFY_HOURLY)
        self.t2 = self.make_team(Team.NOTIFY_HOURLY, add_video=False)
        self.t3 = self.make_team(Team.NOTIFY_DAILY)
        self.t4 = self.make_team(Team.NOTIFY_DAILY, add_video=False)

    def check_needs_new_video_notification(self, notify_interval,
                                           *correct_teams):
        qs = Team.objects.needs_new_video_notification(notify_interval)
        self.assertEquals(set(t.slug for t in qs),
                          set(t.slug for t in correct_teams))

    def test_hourly(self):
        self.check_needs_new_video_notification(Team.NOTIFY_HOURLY, self.t1)

    def test_daily(self):
        self.check_needs_new_video_notification(Team.NOTIFY_DAILY, self.t3)

class TeamVideoTest(TestCase):

    def setUp(self):
        self.auth = {
            "username": u"admin",
            "password": u"admin"
        }

        self.user = UserFactory(**self.auth)
        self.team = TeamFactory()

        TeamMemberFactory(team=self.team, user=self.user,
                          role=TeamMember.ROLE_ADMIN)
        reset_solr()

    def _get_team_videos(self):
        return SearchQuerySet().models(TeamVideo).filter(owned_by_team_id=self.team.pk)

    def _search_for_video(self, team_video):
        qs = VideoIndex.public().filter(title=team_video.video_title_exact)

        if not qs:
            return False

        for video in qs:
            if video.video_id == team_video.video_id:
                return True

        return False

    def test_save_updates_is_visible(self):
        videos = self._get_team_videos()
        self.assertTrue(False not in [v.is_public for v in videos])

        self.client.login(**self.auth)

        url = reverse("teams:settings_basic", kwargs={"slug": self.team.slug})

        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        data = {
            "name": u"New team",
            "is_visible": u"0",
            "description": u"testing",
        }

        response = self.client.post(url, data, follow=True)
        test_utils.update_search_index.run_original()
        self.failUnlessEqual(response.status_code, 200)
        self.assertFalse(Team.objects.get(id=1).is_visible)

        videos = self._get_team_videos()

        for video in videos:
            self.assertFalse(video.is_public)
            self.assertFalse(self._search_for_video(video))

        data['is_visible'] = u'1'

        response = self.client.post(url, data, follow=True)
        test_utils.update_search_index.run_original()
        self.failUnlessEqual(response.status_code, 200)
        self.assertTrue(Team.objects.get(id=1).is_visible)

        videos = self._get_team_videos()

        for video in videos:
            self.assertTrue(video.is_public)
            self.assertTrue(self._search_for_video(video))

    def test_wrong_project_team_fails(self):
        project = ProjectFactory(team=self.team, name="One Project")
        team_video = TeamVideoFactory(team=self.team, added_by=self.user,
                                      description="", project=project)

        other_team = TeamFactory()
        other_project = ProjectFactory(team=other_team, name="Other Project")

        team_video.project = other_project

        self.assertNotEquals(team_video.project, project)
        self.assertNotEquals(team_video.project.team, self.team)

        try:
            team_video.save()
            self.fail("Assertion for team + project did not work")
        except AssertionError:
            pass

    def test_publish_draft_when_teamvideo_deleted(self):
        user = UserFactory()
        team = TeamFactory()
        tv = TeamVideoFactory(team=team, added_by=user)
        video = tv.video

        subs = [(0, 1000, 'Hello',)]
        add_subtitles(video, 'en', subs, visibility='private')

        self.assertEquals(1, sub_models.SubtitleVersion.objects.count())
        sub = sub_models.SubtitleVersion.objects.full()[0]
        self.assertEquals('private', sub.visibility)

        tv.delete()

        self.assertEquals(1, sub_models.SubtitleVersion.objects.count())
        sub = sub_models.SubtitleVersion.objects.full()[0]
        self.assertEquals('public', sub.visibility)


class TeamsTest(TestCase):

    def setUp(self):
        fix_teams_roles()
        self.auth = {
            "username": u"admin",
            "password": u"admin"
        }
        self.user = UserFactory(username=u'admin', password=u'admin',
                                is_staff=True, is_superuser=True)
        reset_solr()

    def _add_team_video(self, team, language, video_url):
        mail.outbox = []
        data = {
            "description": u"",
            "language": language,
            "video_url": video_url,
            "thumbnail": u"",
        }

        if team.has_projects:
            data['project'] = team.project_set.exclude(slug='_root')[0].pk
        else:
            data['project'] = team.default_project.pk

        old_count = TeamVideo.objects.count()
        old_video_count = Video.objects.count()

        url = reverse("teams:add_video", kwargs={"slug": team.slug})
        # the lowest permission level where one can add videos
        member = team.members.get(user=self.user)
        member.role = TeamMember.ROLE_MANAGER
        member.save()
        self.client.post(url, data)
        new_count = TeamVideo.objects.count()
        self.assertEqual(old_count+1, new_count)

        if Video.objects.count() > old_video_count:
            created_video = Video.objects.order_by('-created')[0]
            self.assertEqual(self.user, created_video.user)

    def _set_my_languages(self, *args):
        from auth.models import UserLanguage
        for ul in self.user.userlanguage_set.all():
            ul.delete()
        for lang in args:
            ul = UserLanguage(
                user=self.user,
                language=lang)
            ul.save()
        self.user = User.objects.get(id=self.user.id)

    def _create_new_team_video(self):
        self.client.login(**self.auth)
        response = self.client.get(reverse("teams:create"))

        data = {
            "description": u"",
            "video_url": u"",
            "membership_policy": u"4",
            "video_policy": u"1",
            "workflow_type": u"O",
            "logo": u"",
            "slug": u"new-team",
            "name": u"New team",

        }

        response = self.client.post(reverse("teams:create"), data)
        self.assertEqual(response.status_code, 302)

        team = Team.objects.get(slug=data['slug'])

        self._add_team_video(team, u'en', u"http://videos.mozilla.org/firefox/3.5/switch/switch.ogv")

        tv = TeamVideo.objects.order_by('-id')[0]

        return team, tv

    def _make_data(self, video_id, lang):

        return {
            'language_code': lang,
            'video': video_id,
            'subtitles': open(os.path.join(settings.PROJECT_ROOT, "apps", 'videos', 'fixtures' ,'test.srt'))
            }

    def _tv_search_record_list(self, team):
        test_utils.update_team_video.run_original()
        url = reverse("teams:detail", kwargs={"slug": team.slug})
        response = self.client.get(url)
        return response.context['team_video_md_list']

    def _complete_search_record_list(self, team):
        url = reverse("teams:detail", kwargs={"slug": team.slug})
        response = self.client.get(url)
        return response.context['team_video_md_list']

    def test_team_join_leave(self):
        team = TeamFactory()
        manager = UserFactory()
        TeamMemberFactory(team=team, user=manager)

        join_url = reverse('teams:join_team', args=[team.slug])
        leave_url = reverse('teams:leave_team', args=[team.slug])

        self.client.login(**self.auth)

        #---------------------------------------
        self.assertTrue(team.is_open())
        self.assertFalse(team.is_member(self.user))
        TeamMember.objects.filter(team=team, user=self.user).delete()
        self.assertFalse(team.is_member(self.user))
        response = self.client.get(join_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(team.is_member(self.user))

        #---------------------------------------
        response = self.client.get(leave_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(team.is_member(self.user))

        #---------------------------------------
        team.membership_policy = Team.INVITATION_BY_MANAGER
        team.save()
        self.assertFalse(team.is_open())
        response = self.client.get(join_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(team.is_member(self.user))

    def test_add_video(self):
        self.client.login(**self.auth)

        team = TeamFactory()
        self.assertEqual(team.users.count(), 0)
        TeamMemberFactory(team=team, user=self.user)
        self.assertEqual(team.users.count(), 1)

        for tm in team.members.all():
            tm.notify_by_email = True
            tm.save()
            tm.user.is_active = True
            tm.user.notify_by_email = True
            tm.user.save()

        self._add_team_video(team, u'en', u"http://videos.mozilla.org/firefox/3.5/switch/switch.ogv")

    def test_team_video_delete(self):
        #this test can fail only on MySQL
        team = TeamFactory()
        video = VideoFactory()
        tv = TeamVideoFactory(team=team, added_by=self.user, video=video)

        # create a few languages with subs
        from videos.tests.videotestutils import create_langs_and_versions
        video.is_public = False
        video.moderated_by = team
        video.save()
        langs = ["en" ,"es", 'fr', 'pt-br']
        versions = create_langs_and_versions(video, langs)
        for v in versions:
            v.moderation_status = MODERATION.WAITING_MODERATION
        tv.delete()
        try:
            TeamVideo.objects.get(pk=tv.pk)
            self.fail()
        except TeamVideo.DoesNotExist:
            pass
        video = refresh_obj(video)
        for lang in langs:
            l = video.subtitle_language(lang)
            self.assertTrue(l.version())
            self.assertTrue(l.subtitleversion_set.full().count())
        self.assertTrue(video.is_public)
        self.assertEqual(video.moderated_by, None)

    def test_detail_contents_after_edit(self):
        # make sure edits show up in search result from solr
        self.client.login(**self.auth)
        team = TeamFactory()
        TeamMemberFactory(team=team, user=self.user)
        tv = TeamVideoFactory(team=team, added_by=self.user, description='')
        data = {
            "languages-MAX_NUM_FORMS": u"",
            "languages-INITIAL_FORMS": u"0",
            "title": u"change title",
            "languages-0-language": u"el",
            "languages-0-id": u"",
            "languages-TOTAL_FORMS": u"1",
            "languages-0-completed": u"on",
            "thumbnail": u"",
            "description": u"and descriptionnn",
            "project": team.default_project.pk,

        }
        url = reverse("teams:team_video", kwargs={"team_video_pk": tv.pk})
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("teams:team_video", kwargs={"team_video_pk": tv.pk}))

        reset_solr()

        tv = team.teamvideo_set.get(pk=1)
        team_video_search_records = self._tv_search_record_list(team)

        team_video = [team_video for team_video in team_video_search_records if team_video.team_video_pk == tv.pk][0]
        self.assertEquals('and descriptionnn', team_video.description)

    def test_detail_contents_after_remove(self):
        # make sure removals show up in search result from solr
        self.client.login(**self.auth)
        team = TeamFactory()
        TeamMemberFactory(team=team, user=self.user)
        tv = TeamVideoFactory(team=team, added_by=self.user)
        num_team_videos = len(self._tv_search_record_list(team))

        url = reverse("teams:remove_video", kwargs={"team_video_pk": tv.pk})
        self.client.post(url)

        self.assertEquals(num_team_videos - 1, len(self._tv_search_record_list(team)))

    def test_detail_contents(self):
        team, new_team_video = self._create_new_team_video()

        reset_solr()

        # The video should be in the list.
        record_list = self._tv_search_record_list(team)
        self.assertEqual(1, len(record_list))
        self.assertEqual(new_team_video.video.video_id, record_list[0].video_id)

    def test_detail_contents_original_subs(self):
        team, new_team_video = self._create_new_team_video()

        # upload some subs to the new video. make sure it still appears.
        data = self._make_data(new_team_video.video.id, 'en')
        response = self.client.post(reverse('videos:upload_subtitles'), data)

        reset_solr()

        url = reverse("teams:detail", kwargs={"slug": team.slug})
        response = self.client.get(url)

        # The video should be in the list.
        self.assertEqual(1, len(response.context['team_video_md_list']))

        # but we should see no "no work" message
        self.assertTrue('allow_noone_language' not in response.context or \
                            not response.context['allow_noone_language'])

    def test_detail_contents_unrelated_video(self):
        team, new_team_video = self._create_new_team_video()
        en = SubtitleLanguage(video=new_team_video.video, language_code='en')
        en.subtitles_complete = True
        en.save()

        self._set_my_languages('en', 'ru')

        # now add a Russian video with no subtitles.
        self._add_team_video(
            team, u'ru',
            u'http://upload.wikimedia.org/wikipedia/commons/6/61/CollateralMurder.ogv')

        reset_solr()

        team = Team.objects.get(id=team.id)

        self.assertEqual(2, team.teamvideo_set.count())

        # both videos should be in the list
        search_record_list = self._tv_search_record_list(team)
        self.assertEqual(2, len(search_record_list))

        # but the one with en subs should be second, since it was added earlier
        self.assertEqual(new_team_video, search_record_list[1].object)

    def test_one_tvl(self):
        team, new_team_video = self._create_new_team_video()
        reset_solr()
        self._set_my_languages('ko')
        url = reverse("teams:detail", kwargs={"slug": team.slug})
        response = self.client.get(url)
        self.assertEqual(1, len(response.context['team_video_md_list']))

    def test_no_dupes_without_buttons(self):
        team, new_team_video = self._create_new_team_video()
        self._set_my_languages('ko', 'en')

        self.client.post(
            reverse('videos:upload_subtitles'),
            self._make_data(new_team_video.video.id, 'en'))

        self.client.post(
            reverse('videos:upload_subtitles'),
            self._make_data(new_team_video.video.id, 'es'))

        reset_solr()

        url = reverse("teams:detail", kwargs={"slug": team.slug})
        response = self.client.get(url)
        self.assertEqual(1, len(response.context['team_video_md_list']))

    def test_team_create_with_video(self):
        self.client.login(**self.auth)

        response = self.client.get(reverse("teams:create"))
        self.failUnlessEqual(response.status_code, 200)

        data = {
            "description": u"",
            "video_url": u"http://www.youtube.com/watch?v=OFaWxcH6I9E",
            "membership_policy": u"4",
            "workflow_type": u"O",
            "video_policy": u"1",
            "logo": u"",
            "slug": u"new-team-with-video",
            "name": u"New team with video"
        }
        response = self.client.post(reverse("teams:create"), data)
        self.failUnlessEqual(response.status_code, 302)
        team = Team.objects.get(slug=data['slug'])
        self.assertTrue(team.video)
        self.assertEqual(team.video.user, self.user)
        self.assertTrue(team.video.title)

    def test_all_views(self):
        self.client.login(**self.auth)

        team = Team(
           slug="new-team",
            membership_policy=4,
            video_policy =1,
           name="New-name")
        team.save()
        tm = TeamMember.objects.create_first_member(team, self.user)
        #------- create ----------

        data = {
            "description": u"",
            "video_url": u"",
            "membership_policy": u"4",
            "video_policy": u"1",
            "logo": u"",
            "slug": u"new-team",
            "name": u"New team"
        }

        #---------- index -------------
        response = self.client.get(reverse("teams:index"))
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get(reverse("teams:index"), {'q': 'vol'})
        self.failUnlessEqual(response.status_code, 200)

        data = {
            "q": u"vol",
            "o": u"date"
        }
        response = self.client.get(reverse("teams:index"), data)
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get(reverse("teams:index"), {'o': 'my'})
        self.failUnlessEqual(response.status_code, 200)

        #-------------- applications ----------------
        url = reverse("teams:applications", kwargs={"slug": team.slug})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        #------------ detail ---------------------
        url = reverse("teams:detail", kwargs={"slug": team.slug})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("teams:detail", kwargs={"slug": team.slug})
        response = self.client.get(url, {'q': 'Lions'})
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("teams:detail", kwargs={"slug": team.slug})
        response = self.client.get(url, {'q': 'empty result'})
        self.failUnlessEqual(response.status_code, 200)

        #------------ detail members -------------

        url = reverse("teams:detail_members", kwargs={"slug": team.slug})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("teams:detail_members", kwargs={"slug": team.slug})
        response = self.client.get(url, {'q': 'test'})
        self.failUnlessEqual(response.status_code, 200)

        #-------------members activity ---------------
        #Deprecated
        #url = reverse("teams:members_actions", kwargs={"slug": team.slug})
        #response = self.client.get(url)
        #self.failUnlessEqual(response.status_code, 200)

        #------------- add video ----------------------
        self.client.login(**self.auth)

        data = {
            "languages-MAX_NUM_FORMS": u"",
            "description": u"",
            "language": u"en",
            "title": u"",
            "languages-0-language": u"be",
            "languages-0-id": u"",
            "languages-TOTAL_FORMS": u"1",
            "video_url": u"http://www.youtube.com/watch?v=Hhgfz0zPmH4&feature=grec_index",
            "thumbnail": u"",
            "languages-INITIAL_FORMS": u"0",
            "project":team.default_project.pk,
        }
        tv_len = team.teamvideo_set.count()
        url = reverse("teams:add_video", kwargs={"slug": team.slug})
        response = self.client.post(url, data)
        self.assertEqual(tv_len+1, team.teamvideo_set.count())
        self.assertRedirects(response, reverse("teams:dashboard", kwargs={"slug": team.slug}))

        #-------edit team video -----------------
        team = Team.objects.get(pk=1)
        tv = team.teamvideo_set.get(pk=1)
        tv.description = ''
        tv.save()
        data = {
            "languages-MAX_NUM_FORMS": u"",
            "languages-INITIAL_FORMS": u"0",
            "languages-0-language": u"el",
            "languages-0-id": u"",
            "languages-TOTAL_FORMS": u"1",
            "languages-0-completed": u"on",
            "thumbnail": u"",
            "description": u"and description",
            "author": u"Test Author",
            "creation_date": u"2011-01-01",
            "project": team.default_project.pk
        }
        url = reverse("teams:team_video", kwargs={"team_video_pk": tv.pk})
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("teams:team_video", kwargs={"team_video_pk": tv.pk}))
        tv = team.teamvideo_set.get(pk=1)
        self.assertEqual(tv.description, u"and description")
        meta = tv.video.metadata()
        self.assertEqual(meta.get('author'), 'Test Author')
        self.assertEqual(meta.get('creation_date'), date(2011, 1, 1))

        #-----------delete video -------------
        url = reverse("teams:remove_video", kwargs={"team_video_pk": tv.pk})
        response = self.client.post(url)
        self.failUnlessEqual(response.status_code, 302)
        try:
            team.teamvideo_set.get(pk=1)
            self.fail()
        except ObjectDoesNotExist:
            pass

        #----------inviting to team-----------
        user2 = UserFactory(password='alerion')

        member = TeamMember.objects.get(user=self.user, team=team)
        member.role = TeamMember.ROLE_OWNER
        member.save()

        data = {
            "user_id": user2.id,
            "message": u"test message",
            "role": TeamMember.ROLE_CONTRIBUTOR,
        }
        user_mail_box_count = Message.objects.unread().filter(user=user2).count()
        invite_url = reverse("teams:invite_members", args=(), kwargs={'slug': team.slug})
        response = self.client.post(invite_url, data, follow=True)
        self.failUnlessEqual(response.status_code, 200)

        self.assertEqual(user_mail_box_count + 1,
                         Message.objects.unread().filter(user=user2).count())


        invite = Invite.objects.get(user__username=user2.username, team=team)
        self.assertEqual(invite.role, TeamMember.ROLE_CONTRIBUTOR)
        self.assertEqual(invite.note, u'test message')

        ct = ContentType.objects.get_for_model(Invite)
        Message.objects.filter(object_pk=invite.pk, content_type=ct, user=user2)

        members_count = team.members.count()

        self.client.login(username = user2.username, password ='alerion')
        url = reverse("teams:accept_invite", kwargs={"invite_pk": invite.pk})
        response = self.client.get(url)

        self.assertEqual(members_count+1, team.members.count())

        self.client.login(**self.auth)

        tm,c = TeamMember.objects.get_or_create(user=self.user, team=team)
        tm.role = TeamMember.ROLE_ADMIN
        tm.save()
        url = reverse("teams:remove_member", kwargs={"user_pk": user2.pk, "slug": team.slug})
        response = self.client.post(url)
        self.failUnlessEqual(response.status_code, 302)

        self.assertFalse(team.is_member(user2))

        url = reverse("teams:activity", kwargs={"slug": team.slug})
        response = self.client.post(url)
        self.failUnlessEqual(response.status_code, 200)

        self.client.login()
        TeamMember.objects.filter(user=self.user, team=team).delete()
        self.assertFalse(team.is_member(self.user))
        url = reverse("teams:join_team", kwargs={"slug": team.slug})
        response = self.client.post(url)
        self.failUnlessEqual(response.status_code, 302)
        self.assertTrue(team.is_member(self.user))

    def test_fixes(self):
        url = reverse("teams:detail", kwargs={"slug": 'slug-does-not-exist'})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 404)

    def get_dashboard_page(self, team):
        url = reverse("teams:dashboard", kwargs={"slug":team.slug})
        return self.client.get(url)

    def test_non_visible(self):
        invitation_team = TeamFactory(is_visible=False,
                                      membership_policy=Team.INVITATION_BY_ALL)
        open_team = TeamFactory(is_visible=False,
                                membership_policy=Team.OPEN)
        application_team = TeamFactory(is_visible=False,
                                       membership_policy=Team.APPLICATION)

        for team in (invitation_team, open_team, application_team):
            TeamVideoFactory(team=team)

        # non-visible teams should show up on the listing only if their are
        # application-based on open
        response = self.client.get(reverse('teams:index'))
        self.assertEquals(set(response.context['teams_list']),
                          set([application_team, open_team]))
        # those teams listed should allow non-members to see their dashboards,
        # but make sure that no videos are visible.
        for team in (open_team, application_team):
            response = self.get_dashboard_page(team)
            self.assertEquals(response.status_code, 200)
            self.assertEquals(response.context['videos'], [])
        # invitation teams should not allow non-members to view them
        response = self.get_dashboard_page(invitation_team)
        self.assertEquals(response.status_code, 404)

    def test_search_with_utf8(self):
        title = (u'\u041f\u0435\u0442\u0443\u0445 '
                 u'\u043e\u0442\u0436\u0438\u0433\u0430\u0435\u0442!!!')
        # "Петух отжигает!!!"
        team = TeamFactory()
        TeamMemberFactory(team=team, user=self.user)
        video = VideoFactory(title=title)

        self.assertTrue(video.get_team_video() is None)

        team_video, _ = TeamVideo.objects.get_or_create(video=video, team=team,
                                                        added_by=self.user)
        test_utils.update_team_video.run_original()
        url = reverse("teams:detail", kwargs={"slug": team.slug})
        response = self.client.get(url + u"?q=" + title)
        videos = response.context['team_video_md_list']

        self.assertEquals(len(videos), 1)

        video = videos[0]

        self.assertEquals(video.title, title)

class TeamListingTest(TestCase):
    def setUp(self):
        self.random_user = UserFactory()
        self.public_teams = {}
        self.private_teams = {}
        for is_visible in True, False:
            for membership_policy, label in Team.MEMBERSHIP_POLICY_CHOICES:
                self.setup_team(is_visible, membership_policy)

    def setup_team(self, is_visible, membership_policy):
        team = TeamFactory(is_visible=is_visible,
                           membership_policy=membership_policy)
        if is_visible:
            self.public_teams[membership_policy] = team
        else:
            self.private_teams[membership_policy] = team

    def publicly_listed_teams(self):
        """Get the teams that should be listed for anyone.

        We should list teams that are either visible, or their membership is
        not invitation-only
        """
        private_teams_to_list = [
            self.private_teams[Team.OPEN],
            self.private_teams[Team.APPLICATION]
        ]
        return self.public_teams.values() + private_teams_to_list

    def check_listing(self, user, correct_teams, exclude_private=False):
        def sort_func(team):
            return team.slug
        for_user = Team.objects.for_user(user, exclude_private)
        self.assertEquals(sorted(for_user, key=sort_func),
                          sorted(correct_teams, key=sort_func))

    def test_listing_for_non_member(self):
        self.check_listing(self.random_user, self.publicly_listed_teams())

    def test_members_see_private_teams(self):
        private_team = self.private_teams[Team.INVITATION_BY_ADMIN]
        user = TeamMemberFactory(team=private_team).user
        self.check_listing(user,
                           self.publicly_listed_teams() + [private_team])

    def test_members_dont_see_duplicates(self):
        # if a user is a member of a public team, make sure we don't list it
        # twice
        public_team = self.public_teams[Team.INVITATION_BY_ADMIN]
        user = TeamMemberFactory(team=public_team).user
        # make a second team member, which is one way this error happens
        TeamMemberFactory(team=public_team)
        self.check_listing(user, self.publicly_listed_teams())

    def test_deleted_teams_not_listed(self):
        deleted_team = self.public_teams[Team.INVITATION_BY_ADMIN]
        deleted_team.deleted = True
        deleted_team.save()
        self.check_listing(self.random_user,
                           [t for t in self.publicly_listed_teams()
                            if t != deleted_team])

    def test_exclude_private(self):
        self.check_listing(self.random_user, self.public_teams.values(),
                           exclude_private=True)

class TestJqueryRpc(TestCase):

    def setUp(self):
        fix_teams_roles()
        self.team = Team(name='Test', slug='test')
        self.team.save()
        self.user = UserFactory()
        self.rpc = TeamsApiClass()

    def test_promote_user(self):
        other_user = UserFactory()
        user_tm = TeamMember(team=self.team, user=self.user)
        user_tm.save()
        other_user_tm = TeamMember(team=self.team, user=other_user)
        other_user_tm.save()

        self.assertEqual(other_user_tm.role, TeamMember.ROLE_CONTRIBUTOR)
        self.assertEqual(user_tm.role, TeamMember.ROLE_CONTRIBUTOR)

        response = self.rpc.promote_user(self.team.pk, other_user_tm.pk, TeamMember.ROLE_MANAGER, AnonymousUser())
        if not isinstance(response, Error):
            self.fail('Anonymouse user is not member of team')

        response = self.rpc.promote_user(self.team.pk, other_user_tm.pk, TeamMember.ROLE_MANAGER, self.user)
        if not isinstance(response, Error):
            self.fail('User should be manager')

        user_tm.role = TeamMember.ROLE_MANAGER
        user_tm.save()

        NEW_ROLE = TeamMember.ROLE_CONTRIBUTOR
        response = self.rpc.promote_user(self.team.pk, other_user_tm.pk, NEW_ROLE, self.user)
        self.assertTrue(isinstance(response, Msg))
        other_user_tm = refresh_obj(other_user_tm)
        self.assertEqual(other_user_tm.role, NEW_ROLE)

        response = self.rpc.promote_user(self.team.pk, user_tm.pk, TeamMember.ROLE_CONTRIBUTOR, self.user)
        if not isinstance(response, Error):
            self.fail('Can\'t promote yourself')

        response = self.rpc.promote_user(self.team.pk, other_user_tm.pk, 'undefined role 123456', self.user)
        if not isinstance(response, Error):
            self.fail('Incorrect role')

        response = self.rpc.promote_user(self.team.pk, 123456, TeamMember.ROLE_MANAGER, self.user)
        if not isinstance(response, Error):
            self.fail('Undefined team member')

        undefined_team_pk = 123456
        self.assertFalse(Team.objects.filter(pk=undefined_team_pk))
        response = self.rpc.promote_user(undefined_team_pk, other_user_tm.pk, TeamMember.ROLE_MANAGER, self.user)
        if not isinstance(response, Error):
            self.fail('Undefined team')

    def test_create_application(self):
        response = self.rpc.create_application(self.team.pk, 'Note', AnonymousUser())
        if not isinstance(response, Error):
            self.fail('User should be authenticated')
        #---------------------------------------

        response = self.rpc.create_application(None, 'Note', self.user)
        if not isinstance(response, Error):
            self.fail('Undefined team')
        #---------------------------------------
        self.team.membership_policy = Team.INVITATION_BY_MANAGER
        self.team.save()

        response = self.rpc.create_application(self.team.pk, 'Note', self.user)
        if not isinstance(response, Error):
            self.fail('Team is not opened')
        #---------------------------------------
        self.team.membership_policy = Team.OPEN
        self.team.save()

        self.assertFalse(self.team.is_member(self.user))

        response = self.rpc.create_application(self.team.pk, 'Note', self.user)

        if isinstance(response, Error):
            self.fail(response)

        self.assertTrue(self.team.is_member(self.user))
        #---------------------------------------
        self.team.members.filter(user=self.user).delete()

        self.team.membership_policy = Team.APPLICATION
        self.team.save()

        self.assertFalse(Application.objects.filter(user=self.user, team=self.team).exists())
        response = self.rpc.create_application(self.team.pk, 'Note', self.user)

        if isinstance(response, Error):
            self.fail(response)

        self.assertFalse(self.team.is_member(self.user))
        self.assertTrue(Application.objects.filter(user=self.user, team=self.team).exists())
        #---------------------------------------


class TeamsDetailQueryTest(TestCase):

    def setUp(self):
        fix_teams_roles()
        self.auth = {
            "username": u"admin",
            "password": u"admin"
        }
        self.user = UserFactory(**self.auth)

        self.client.login(**self.auth)
        from testhelpers.views import _create_videos, _create_team_videos
        fixture_path = os.path.join(settings.PROJECT_ROOT, "apps", "videos", "fixtures", "teams-list.json")
        data = json.load(open(fixture_path))
        self.videos = _create_videos(data, [self.user])
        self.team, created = Team.objects.get_or_create(name="test-team", slug="test-team")
        self.tvs = _create_team_videos( self.team, self.videos, [self.user])
        reset_solr()

    def _set_my_languages(self, *args):
        from auth.models import UserLanguage
        for ul in self.user.userlanguage_set.all():
            ul.delete()
        for lang in args:
            ul = UserLanguage(
                user=self.user,
                language=lang)
            ul.save()
        self.user = User.objects.get(id=self.user.id)

    def _create_rdm_video(self, i):
        video, created = Video.get_or_create_for_url("http://www.example.com/%s.mp4" % i)
        return video

    def test_multi_query(self):
        team, created = Team.objects.get_or_create(slug='arthur')
        team.videos.all().delete()
        from utils import multi_query_set as mq
        user = UserFactory()
        created_tvs = [TeamVideo.objects.get_or_create(team=team, added_by=user, video=self._create_rdm_video(x) )[0] for x in xrange(10,30)]
        created_pks = [x.pk for x in created_tvs]
        multi = mq.MultiQuerySet(*[TeamVideo.objects.filter(pk=x) for x in created_pks])
        self.assertTrue([x.pk for x in multi] == created_pks)


class TestLanguagePreference(TestCase):
    def setUp(self):
        fix_teams_roles()
        self.team = TeamFactory()
        self.langs_set = translation.ALL_LANGUAGE_CODES
        invalidate_lang_preferences(self.team)

    def test_readable_lang(self):
        # no tlp, should be all languages
        generated =TeamLanguagePreference.objects._generate_readable(self.team )
        cached =TeamLanguagePreference.objects.get_readable(self.team )
        self.assertItemsEqual(self.langs_set, generated )
        self.assertItemsEqual(self.langs_set, cached )
        # create one blocked
        tlp  = TeamLanguagePreference(team=self.team, language_code="en")
        tlp.save()
        # test generation
        generated =TeamLanguagePreference.objects._generate_readable(self.team )
        #test cache
        cached =TeamLanguagePreference.objects.get_readable(self.team )
        self.assertEquals(len(self.langs_set), len(generated)+1)
        self.assertEquals(len(self.langs_set), len(cached)+1)
        self.assertIn("en" , self.langs_set)
        self.assertNotIn("en" , generated)
        self.assertNotIn("en" , cached)

    def test_writable_lang(self):
        # no tlp, should be all languages
        generated =TeamLanguagePreference.objects._generate_writable(self.team )
        cached =TeamLanguagePreference.objects.get_writable(self.team )
        self.assertItemsEqual(self.langs_set, generated )
        self.assertItemsEqual(self.langs_set, cached )
        # create one blocked
        tlp  = TeamLanguagePreference(team=self.team, language_code="en")
        tlp.save()
        # test generation
        generated =TeamLanguagePreference.objects._generate_writable(self.team )
        #test cache
        cached =TeamLanguagePreference.objects.get_writable(self.team )
        self.assertEquals(len(self.langs_set), len(generated)+1)
        self.assertEquals(len(self.langs_set), len(cached)+1)
        self.assertIn("en" , self.langs_set)
        self.assertNotIn("en" , generated)
        self.assertNotIn("en" , cached)

    def test_preferred_lang(self):
        # No preference, so no languages should be preferred.
        generated = TeamLanguagePreference.objects._generate_preferred(self.team)
        cached = TeamLanguagePreference.objects.get_preferred(self.team)
        self.assertItemsEqual([], generated)
        self.assertItemsEqual([], cached)

        # Create one preferred.
        tlp = TeamLanguagePreference(team=self.team, language_code="en", preferred=True)
        tlp.save()

        # Check everything.
        generated = TeamLanguagePreference.objects._generate_preferred(self.team)
        cached = TeamLanguagePreference.objects.get_preferred(self.team)

        self.assertItemsEqual(["en"], generated)
        self.assertItemsEqual(["en"], cached)

        # Make sure this preferred language doesn't show up as a blocker.
        generated = TeamLanguagePreference.objects._generate_readable(self.team)
        cached = TeamLanguagePreference.objects.get_readable(self.team)

        self.assertIn("en", generated)
        self.assertIn("en", cached)

        generated = TeamLanguagePreference.objects._generate_writable(self.team)
        cached = TeamLanguagePreference.objects.get_writable(self.team)

        self.assertIn("en", generated)
        self.assertIn("en", cached)


class TestInvites(TestCase):

    def setUp(self):
        self.user = UserFactory(notify_by_message=True)
        self.user.set_password(self.user.username)
        self.user.save()
        self.owner = UserFactory(notify_by_message=True)
        self.team = Team.objects.create(name='test-team', slug='test-team', membership_policy=Team.APPLICATION)
        TeamMember.objects.create(user=self.owner, role=TeamMember.ROLE_ADMIN, team=self.team)

    def test_invite_invalid_after_accept(self):
        invite_form = InviteForm(self.team, self.owner, {
            'user_id': self.user.pk,
            'message': 'Subtitle ALL the things!',
            'role':'contributor',
        })
        invite_form.is_valid()
        self.assertFalse(invite_form.errors)
        self.assertEquals(Message.objects.for_user(self.user).count(), 0)
        invite = invite_form.save()
        # user has the invitation message on their inbox now
        self.assertEquals(Message.objects.for_user(self.user).count(), 1)
        invite.accept()
        self.assertTrue(self.team.members.filter(user=self.user).exists())
        self.team.members.filter(user=self.user).delete()
        # now the invite re-accepts:
        self.client.login(
            username=self.user.username,
            password=self.user.username
        )
        url = reverse("teams:accept_invite", args=(invite.pk,))
        response  = self.client.get(url)
        self.assertEqual(response.status_code, 500)
        self.assertIn( 'error_msg', response.context)
        self.assertFalse(self.team.members.filter(user=self.user).exists())

    def test_invite_invalid_after_deny(self):
        invite_form = InviteForm(self.team, self.owner, {
            'user_id': self.user.pk,
            'message': 'Subtitle ALL the things!',
            'role':'contributor',
        })
        invite_form.is_valid()
        self.assertFalse(invite_form.errors)
        self.assertEquals(Message.objects.for_user(self.user).count(), 0)
        invite = invite_form.save()
        # user has the invitation message on their inbox now
        invite.deny()
        self.assertFalse(self.team.members.filter(user=self.user).exists())
        # now the invite re-accepts:
        url = reverse("teams:deny_invite", args=(invite.pk,))
        self.client.login(
            username=self.user.username,
            password=self.user.username
        )
        response  = self.client.get(url)
        self.assertEqual(response.status_code, 500)
        self.assertIn( 'error_msg', response.context)
        self.assertFalse(self.team.members.filter(user=self.user).exists())

    def test_invite_after_removal(self):
        invite_form = InviteForm(self.team, self.owner, {
            'user_id': self.user.pk,
            'message': 'Subtitle ALL the things!',
            'role': TeamMember.ROLE_MANAGER,
        })
        invite_form.is_valid()
        self.assertFalse(invite_form.errors)
        self.assertEquals(Message.objects.for_user(self.user).count(), 0)
        invite = invite_form.save()
        # user has the invitation message on their inbox now
        invite.accept()
        self.assertTrue(self.team.members.filter(user=self.user).exists())
        self.team.members.filter(user=self.user).delete()
        # now the invite re-accepts:
        self.client.login(
            username=self.user.username,
            password=self.user.username
        )
        # acn't accept twice:
        self.assertRaises(InviteExpiredException, invite.accept)
        self.assertFalse(self.team.members.filter(user=self.user, team=self.team).exists())
        # re-invite
        invite_form = InviteForm(self.team, self.owner, {
            'user_id': self.user.pk,
            'message': 'Subtitle ALL the things!',
            'role': TeamMember.ROLE_CONTRIBUTOR,
        })
        invite_form.is_valid()
        self.assertFalse( invite_form.errors)
        invite = invite_form.save()
        url = reverse("teams:accept_invite", args=(invite.pk,))
        response  = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.team.members.filter(user=self.user, team=self.team).exists())


    def test_invite_after_leaving(self):
        # user is invited
        invite_form = InviteForm(self.team, self.owner, {
            'user_id': self.user.pk,
            'message': 'Subtitle ALL the things!',
            'role': TeamMember.ROLE_MANAGER,
        })
        invite_form.is_valid()
        self.assertFalse(invite_form.errors)
        self.assertEquals(Message.objects.for_user(self.user).count(), 0)
        invite = invite_form.save()
        # user has the invitation message on their inbox now
        # user accepts
        invite.accept()
        self.assertTrue(self.team.members.filter(user=self.user).exists())
        # now the invite re-accepts, should fail
        self.client.login(
            username=self.user.username,
            password=self.user.username
        )

        url = reverse("teams:accept_invite", args=(invite.pk,))
        response  = self.client.get(url)
        self.assertEqual(response.status_code, 500)
        self.assertTrue(self.team.members.filter(user=self.user, team=self.team).exists())

        # user leaves team
        url = reverse("teams:leave_team", args=(self.team.slug,))
        response  = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.team.members.filter(user=self.user, team=self.team).exists())


        # user tries to re-accept old invite - fails
        url = reverse("teams:accept_invite", args=(invite.pk,))
        response  = self.client.get(url)
        self.assertEqual(response.status_code, 500)
        self.assertFalse(self.team.members.filter(user=self.user, team=self.team).exists())
        # user is re-invited, should work


        invite_form = InviteForm(self.team, self.owner, {
            'user_id': self.user.pk,
            'message': 'Subtitle ALL the things!',
            'role': TeamMember.ROLE_MANAGER,
        })
        invite_form.is_valid()
        self.assertFalse(invite_form.errors)
        self.assertEquals(Message.objects.for_user(self.user).count(), 3)
        invite = invite_form.save()
        # user has the invitation message on their inbox now
        # user accepts
        url = reverse("teams:accept_invite", args=(invite.pk,))
        response  = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.team.members.filter(user=self.user, team=self.team).exists())


class TestApplication(TestCase, test_utils.TestCaseMessagesMixin):
    def setUp(self):
        self.team, c = Team.objects.get_or_create(name='test', slug='test',membership_policy=Team.APPLICATION )
        self.owner = UserFactory(username='test-owner')
        self.owner.set_password('test')
        self.owner.save()
        TeamMember.objects.create(team=self.team, user=self.owner, role=TeamMember.ROLE_OWNER)

        self.applicant = UserFactory(username='test-applicant')
        self.applicant.set_password('test')
        self.applicant.save()


        self.rpc = TeamsApiClass()

    def _send_application(self):
        self._login(False)
        # if te team member left, he can auto join
        should_auto_join = False
        try:
            application = Application.objects.get(team=self.team,user=self.applicant)
            should_auto_join = application.status  == Application.STATUS_MEMBER_LEFT
        except Application.DoesNotExist:
            application = None

        response = self.rpc.create_application(self.team.pk, 'Note', self.applicant)
        if isinstance(response, Error):
            self.fail(response)
        if not should_auto_join:
            self.assertFalse(self.team.is_member(self.applicant))
            self.assertTrue(Application.objects.filter(user=self.applicant, team=self.team, status=Application.STATUS_PENDING).exists())
            self.assertTrue(Application.objects.open(user=self.applicant, team=self.team).exists())
        else:
            self.assertTrue(self.team.is_member(self.applicant))
            self.assertTrue(Application.objects.filter(user=self.applicant, team=self.team, status=Application.STATUS_APPROVED).exists())
        return Application.objects.get(pk=application.pk) if application else Application.objects.order_by('-pk')[0]

    def _login(self, as_owner):
        username = self.owner.username if as_owner else self.applicant.username
        self.assertTrue(self.client.login(username=username, password='test'))

    def _approve(self, application):
        self._login(True)
        #num_messages = self._getMessagesCount(level=LEVEL_SUCCESS)
        url = reverse("teams:approve_application", args=(self.team.slug, application.pk))
        response = self.client.post(url, follow=True)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.status_code, 200)

    def _deny(self, application):
        self._login(True)
        #num_messages = self._getMessagesCount(level=LEVEL_SUCCESS)
        url = reverse("teams:deny_application", args=(self.team.slug, application.pk))
        response = self.client.post(url, follow=True)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.status_code, 200)



    def _leave_team(self, user):
        url = reverse("teams:leave_team", args=(self.team.slug,))
        self.client.post(url)

    def _remove_member(self, user):
        self._login(True)
        member_count = self.team.members.count()
        url = reverse("teams:remove_member", args=(self.team.slug,user.pk))
        self.client.post(url)
        self.assertEqual(member_count -1, self.team.members.count())


    def test_user_leaves(self):
        # user applies
        application = self._send_application()
        # owner approves
        self._approve(application)
        # is member!
        self.assertTrue(self.team.is_member(self.applicant))
        # cannot apply again
        self.assertFalse(teams_tags.can_apply(self.team, self.applicant))
        # regular application inbox is empty
        self.assertEquals(Application.objects.open(team=self.team).count(), 0)
        # applicant leaves team
        self.client.logout()
        self._login(False)
        self._leave_team(self.applicant)

        self.assertFalse(Application.objects.filter(team=self.team, status=Application.STATUS_APPROVED).exists())
        self.assertTrue(Application.objects.filter(team=self.team, status=Application.STATUS_MEMBER_LEFT).exists())
        # applicant is not member
        self.assertFalse(self.team.is_member(self.applicant))
        # application can join again
        self.assertTrue(teams_tags.can_apply(self.team, self.applicant))
        application = self._send_application()

        # applicant is a team member again
        self.assertTrue(self.team.is_member(self.applicant))

    def test_user_removed(self):
        # user applies
        application = self._send_application()
        # owner approves
        self._approve(application)
        # is member!
        self.assertTrue(self.team.is_member(self.applicant))
        # cannot apply again
        self.assertFalse(teams_tags.can_apply(self.team, self.applicant))
        # regular application inbox is empty
        self.assertEquals(Application.objects.open(team=self.team).count(), 0)
        # applicant leaves team
        self.client.logout()
        self._login(True)
        self._remove_member(self.applicant)

        self.assertFalse(Application.objects.filter(team=self.team, status=Application.STATUS_APPROVED).exists())
        self.assertTrue(Application.objects.filter(team=self.team, status=Application.STATUS_MEMBER_REMOVED).exists())
        # applicant is not member
        self.assertFalse(self.team.is_member(self.applicant))
        # application can join again
        self.assertFalse(teams_tags.can_apply(self.team, self.applicant))
        self._login(False)
        response = self.rpc.create_application(self.team.pk, 'Note', self.applicant)
        # removed user, cannot send application again
        self.assertTrue( isinstance(response, Error))


    def test_denied_kills_it(self):
        # user applies
        application = self._send_application()
        # owner approves
        self._deny(application)
        # is member!
        self.assertFalse(self.team.is_member(self.applicant))
        # cannot apply again
        self.assertFalse(teams_tags.can_apply(self.team, self.applicant))
        # regular application inbox is empty
        self.assertEquals(Application.objects.open(team=self.team).count(), 0)
        # applicant leaves team
        self.assertTrue(Application.objects.filter(team=self.team, status=Application.STATUS_DENIED).exists())
        # applicant is not member
        self.assertFalse(self.team.is_member(self.applicant))
        # application can join again
        self._login(False)
        response = self.rpc.create_application(self.team.pk, 'Note', self.applicant)
        # removed user, cannot send application again
        self.assertTrue( isinstance(response, Error))


    def test_can_apply(self):
        # user is already a memeber, can't apply
        self.assertFalse(Application.objects.can_apply(self.team, self.owner))
        # if has bad application or is already a member
        self.assertTrue(Application.objects.can_apply(self.team, self.applicant))
        # create applications where team owners have already blocked the user or are still waiting
        for app_status in [Application.STATUS_MEMBER_REMOVED, Application.STATUS_DENIED, Application.STATUS_PENDING]:
            application = Application.objects.create(status=app_status, team=self.team, user=self.applicant)
            self.assertFalse(Application.objects.can_apply(self.team, self.applicant))
            application.delete()


class PartnerTest(TestCase):
    def setUp(self):
        fix_teams_roles()
        self.auth = {
            "username": u"admin",
            "password": u"admin"
        }
        self.user = UserFactory(**self.auth)

        self.client.login(**self.auth)
        from testhelpers.views import _create_videos, _create_team_videos
        fixture_path = os.path.join(settings.PROJECT_ROOT, "apps", "videos", "fixtures", "teams-list.json")
        data = json.load(open(fixture_path))
        self.videos = _create_videos(data, [self.user])
        self.team, created = Team.objects.get_or_create(name="test-team", slug="test-team")
        self.tvs = _create_team_videos( self.team, self.videos, [self.user])
        reset_solr()

    def test_is_admin(self):
        partner = Partner.objects.create(name='Le Partner', slug='partner')
        user = UserFactory()

        self.assertFalse(partner.is_admin(user))
        partner.admins.add(user)
        self.assertTrue(partner.is_admin(user))

    def test_approved(self):
        # TODO: Closing this up to unblock a merge
        return
        from teams.models import Workflow, BillingReport
        # from teams.moderation_const import APPROVED

        self.assertEquals(0, Workflow.objects.count())

        team = TeamFactory(workflow_enabled=True)
        user = UserFactory()
        TeamMemberFactory(team=team, user=user)
        video = VideoFactory()
        TeamVideoFactory(team=team, added_by=user, video=video)

        Workflow.objects.create(team=team, approve_allowed=20)

        self.assertEquals(1, Workflow.objects.count())
        self.assertTrue(team.get_workflow().approve_enabled)

        language = SubtitleLanguage.objects.create(video=video, language="en")

        subs = [
            (0, 1000, 'hello', {}),
            (2000, 3000, 'world', {})
        ]

        for i in range(1, 10):
            add_subtitles(language.video, language.language, subs)

        # v1 = sub_models.SubtitleVersion.objects.get(
        #         subtitle_language__language_code='en',
        #         version_number=3)
        # v2 = sub_models.SubtitleVersion.objects.get(
        #         subtitle_language__language_code='en',
        #         version_number=6)

        # v1.moderation_status = APPROVED
        # v1.save()
        # v2.moderation_status = APPROVED
        # v2.save()

        b = BillingReport.objects.create(team=team,
                start_date=date(2012, 1, 1), end_date=date(2012, 1, 2))

        langs = language.video.newsubtitlelanguage_set.all()
        c = langs[0]
        d = team.created - timedelta(days=5)
        SubtitleVersion.objects.create(subtitle_language=c, version_number=0,
                note='From youtube', created=d)

        self.assertTrue(len(langs) > 0)
        created, imported, _ = b._get_lang_data(langs, datetime(2012, 1, 1, 13, 30, 0))

        self.assertTrue(len(created) > 0)

        v = created[0][1]
        self.assertEquals(v.version_number, 3)

        team.workflow_enabled = False
        team.save()

        created, imported, _ = b._get_lang_data(langs, datetime(2012, 1, 1, 13, 30, 0))
        self.assertEquals(1, len(created))
        v = created[0][1]
        self.assertEquals(v.version_number, 9)

    def test_get_imported(self):
        # TODO: Closing this up to unblock a merge
        return
        from teams.models import BillingReport
        team = Team.objects.all()[0]
        video = Video.objects.all()[0]

        team_created = team.created

        b = BillingReport.objects.create(team=team,
                start_date=date(2012, 1, 1), end_date=date(2012, 1, 2))

        SubtitleLanguage.objects.all().delete()

        sl_en = SubtitleLanguage.objects.create(video=video, language_code='en')
        sl_cs = SubtitleLanguage.objects.create(video=video, language_code='cs')
        sl_fr = SubtitleLanguage.objects.create(video=video, language_code='fr')
        sl_es = SubtitleLanguage.objects.create(video=video, language_code='es')
        SubtitleLanguage.objects.create(video=video, language_code='ru')

        before_team_created = team_created - timedelta(days=10)
        after_team_created = team_created + timedelta(days=10)

        SubtitleVersion.objects.create(subtitle_language=sl_fr,
                created=before_team_created, note='From youtube',
                version_number=0)

        SubtitleVersion.objects.create(subtitle_language=sl_fr,
                created=after_team_created,
                version_number=1)

        SubtitleVersion.objects.create(subtitle_language=sl_en,
                created=before_team_created, note='From youtube',
                version_number=0)

        SubtitleVersion.objects.create(subtitle_language=sl_es,
                created=before_team_created,
                version_number=0)

        SubtitleVersion.objects.create(subtitle_language=sl_cs,
                created=after_team_created, note='From youtube',
                version_number=0)

        # Done with setup, let's test things

        languages = sub_models.SubtitleLanguage.objects.all()
        imported, crowd_created = b._separate_languages(languages)

        self.assertEquals(len(imported), 3)
        imported_pks = [i.pk for i in imported]
        self.assertTrue(sl_fr.pk in imported_pks)
        self.assertTrue(sl_es.pk in imported_pks)
        self.assertTrue(sl_cs.pk in imported_pks)

    def test_incomplete_language(self):
        from teams.models import BillingRecord
        from videos.tasks import video_changed_tasks

        user = UserFactory()
        team = TeamFactory()
        tv = TeamVideoFactory(team=team, added_by=user)
        video = tv.video

        self.assertEquals(0, BillingRecord.objects.count())

        sub_models.SubtitleVersion.objects.full().delete()
        sub_models.SubtitleLanguage.objects.all().delete()

        subs = [
            (0, 1000, 'Hello',),
            (1000, 5000, 'world',),
            (8000, 12 * 1000, 'end',)
        ]
        sv = add_subtitles(video, 'en', subs, complete=False)
        video_changed_tasks(video.pk, sv.pk)

        self.assertEquals(0, BillingRecord.objects.count())

    def test_original_language(self):
        from teams.models import BillingRecord
        from videos.tasks import video_changed_tasks

        user = UserFactory()
        team = TeamFactory()
        tv = TeamVideoFactory(team=team, added_by=user,
                              video__primary_audio_language_code='en')
        video = tv.video

        self.assertEquals(0, BillingRecord.objects.count())

        sub_models.SubtitleVersion.objects.full().delete()
        sub_models.SubtitleLanguage.objects.all().delete()

        subs = [
            (0, 1000, 'Hello',),
            (1000, 5000, 'world',),
            (8000, 12 * 1000, 'end',)
        ]

        sv = add_subtitles(video, 'en', subs, complete=True)
        video_changed_tasks(video.pk, sv.pk)

        sv = add_subtitles(video, 'cs', subs, complete=True)
        video_changed_tasks(video.pk, sv.pk)

        self.assertEquals(2, BillingRecord.objects.count())

        br_cs = BillingRecord.objects.get(video=video,
                new_subtitle_language__language_code='cs')
        br_en = BillingRecord.objects.get(video=video,
                new_subtitle_language__language_code='en')

        self.assertTrue(br_en.is_original)
        self.assertFalse(br_cs.is_original)

    def test_get_minutes(self):
        from teams.models import BillingRecord
        from videos.tasks import video_changed_tasks

        user = UserFactory()
        team = TeamFactory()
        tv = TeamVideoFactory(team=team, added_by=user)
        video = tv.video

        self.assertEquals(0, BillingRecord.objects.count())

        sub_models.SubtitleVersion.objects.full().delete()
        sub_models.SubtitleLanguage.objects.all().delete()

        subs = [
            (0, 1000, 'Hello',),
            (1000, 5000, 'world',),
            (8000, 12 * 1000, 'end',)
        ]
        sv = add_subtitles(video, 'en', subs, complete=True)
        video_changed_tasks(video.pk, sv.pk)

        self.assertEquals(1, BillingRecord.objects.count())

        br = BillingRecord.objects.all()[0]
        self.assertEquals(br.minutes, 1)
