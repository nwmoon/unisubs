# Amara, universalsubtitles.org
#
# Copyright (C) 2015 Participatory Culture Foundation
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program.  If not, see http://www.gnu.org/licenses/agpl-3.0.html.

from django.test import TestCase
from nose.tools import *
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.test import APIClient, APIRequestFactory
import mock

from api.views.videos import VideoSerializer, VideoViewSet
from subtitles import pipeline
from utils.factories import *
from utils import test_utils
import teams.signals

class VideoSerializerTest(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.video = VideoFactory(
            title='test-title',
            description='test-description',
            duration=100,
            thumbnail='http://example.com/image.jpg',
        )
        self.video_moved_from_team_to_team_handler = mock.Mock()
        teams.signals.video_moved_from_team_to_team.connect(
            self.video_moved_from_team_to_team_handler, weak=False)
        self.addCleanup(
            teams.signals.video_moved_from_team_to_team.disconnect,
            self.video_moved_from_team_to_team_handler)

    def video_detail_request(self):
        request = APIRequestFactory().get('/videos/{0}'.format(
            self.video.video_id
        ))
        request.user = self.user
        return request

    def video_list_request(self):
        request = APIRequestFactory().get('/videos/')
        request.user = self.user
        return request

    def get_serialized_data(self):
        context = { 'request': self.video_detail_request() }
        video_serializer = VideoSerializer(test_utils.reload_obj(self.video), 
                                           context=context)
        return video_serializer.data

    def run_create(self, data):
        context = {
            'request': self.video_list_request()
        }
        video_serializer = VideoSerializer(data=data, context=context)
        video_serializer.is_valid(raise_exception=True)
        return video_serializer.save()

    def run_update(self, data):
        context = {
            'request': self.video_list_request()
        }
        video_serializer = VideoSerializer(instance=self.video, data=data,
                                           context=context)
        video_serializer.is_valid(raise_exception=True)
        return video_serializer.save()

    def test_simple_fields(self):
        data = self.get_serialized_data()
        assert_equal(data['id'], self.video.video_id)
        assert_equal(data['title'], self.video.title)
        assert_equal(data['description'], self.video.description)
        assert_equal(data['duration'], self.video.duration)
        assert_equal(data['created'], self.video.created.isoformat())
        assert_equal(data['thumbnail'], self.video.thumbnail)
        assert_equal(data['resource_uri'],
                     'http://testserver/api/videos/{0}/'.format(
                         self.video.video_id))

    def test_language_field(self):
        # test the original_language/primary_audio_language_code fields
        data = self.get_serialized_data()
        assert_equal(data['original_language'], None)
        assert_equal(data['primary_audio_language_code'], None)
        self.video.primary_audio_language_code = 'en'
        self.video.save()
        data = self.get_serialized_data()
        assert_equal(data['original_language'], 'en')
        assert_equal(data['primary_audio_language_code'], 'en')

    def test_team_field(self):
        data = self.get_serialized_data()
        assert_equal(data['team'], None)
        tv = TeamVideoFactory(video=self.video, team__slug='test-team')
        self.video.clear_team_video_cache()
        data = self.get_serialized_data()
        assert_equal(data['team'], 'test-team')

    def test_project_field(self):
        assert_equal(self.get_serialized_data()['project'], None)
        # if the project is the default project, we should set it to None
        team = TeamFactory()
        team_video = TeamVideoFactory(video=self.video, team=team)
        assert_equal(self.get_serialized_data()['project'], None)

        team_video.project = ProjectFactory(team=team, slug='test-project')
        team_video.save()
        assert_equal(self.get_serialized_data()['project'], 'test-project')

    def test_invalid_project(self):
        with assert_raises(ValidationError):
            self.run_update({
                'team': TeamFactory().slug,
                'project': 'invalid-project',
            })


    def test_project_without_team(self):
        with assert_raises(ValidationError):
            self.run_update({
                'project': ProjectFactory().slug
            })

    def test_metadata_field(self):
        data = self.get_serialized_data()
        assert_equal(data['metadata'], {})
        self.video.update_metadata({
            'speaker-name': 'Someone',
        })
        data = self.get_serialized_data()
        assert_equal(data['metadata'], {
            'speaker-name': 'Someone',
        })

    def test_all_urls(self):
        primary_url = self.video.get_primary_videourl_obj()
        secondary_url = VideoURLFactory(video=self.video)
        data = self.get_serialized_data()
        assert_equal(data['all_urls'], [
            primary_url.url,
            secondary_url.url,
        ])

    def test_languages(self):
        pipeline.add_subtitles(self.video, 'en', SubtitleSetFactory(),
                               visibility='public')
        pipeline.add_subtitles(self.video, 'he', SubtitleSetFactory(),
                               visibility='private')

        data = self.get_serialized_data()
        lang_url_root = ('/api2/partners/videos/{0}/'
                         'languages/'.format(self.video.video_id))
        assert_items_equal(data['languages'], [
            {
                'code': 'en',
                'name': 'English',
                u'subtitles_uri': lang_url_root + 'en/subtitles/',
                'dir': 'ltr',
                'visible': True,
                'resource_uri':  lang_url_root + 'en/'
            },
            {
                'code': 'he',
                'name': 'Hebrew',
                u'subtitles_uri': lang_url_root + 'he/subtitles/',
                'dir': 'rtl',
                'visible': False,
                'resource_uri':  lang_url_root + 'he/'
            },
        ])

    def test_create(self):
        data = {
            'video_url': 'http://example.com/new-video.mp4',
            'primary_audio_language_code': 'en',
            'title': 'title',
            'description': 'description',
            'duration': '100',
            'thumbnail': 'http://example.com/thumb.jpg',
        }
        result = self.run_create(data)
        assert_equal(result.get_primary_videourl_obj().url, data['video_url'])
        assert_equal(result.primary_audio_language_code,
                     data['primary_audio_language_code'])
        assert_equal(result.title, data['title'])
        assert_equal(result.description, data['description'])
        assert_equal(result.duration, 100)
        assert_equal(result.thumbnail, data['thumbnail'])
        assert_equal(result.get_primary_videourl_obj().added_by, self.user)
        test_utils.assert_saved(result)

    def test_cant_create_with_existing_video_url(self):
        url = 'http://example.com/existing-video.mp4'
        VideoFactory(video_url__url=url)
        with assert_raises(ValidationError):
            self.run_create({
                'video_url': url,
            })

    def test_update(self):
        data = {
            'primary_audio_language_code': 'fr',
            'title': 'new-title',
            'description': 'new-description',
            'duration': '100',
            'thumbnail': 'http://example.com/new-thumbnail.png',
        }
        result = self.run_update(data)
        assert_equal(result.id, self.video.id)
        assert_equal(result.primary_audio_language_code,
                     data['primary_audio_language_code'])
        assert_equal(result.title, data['title'])
        assert_equal(result.description, data['description'])
        assert_equal(result.duration, 100)
        assert_equal(result.thumbnail, data['thumbnail'])

    def test_set_metadata(self):
        new_metadata = {
            'speaker-name': 'Test Speaker',
            'location': 'Test Location',
        }
        result = self.run_update({
            'metadata': new_metadata,
        })
        assert_equal(result.get_metadata(), new_metadata)

    def test_set_metadata_invalid_key(self):
        with assert_raises(ValidationError):
            self.run_update({
                'metadata': {
                    'invalid-key': 'Test Value'
                }
            })

    def test_writable_fields(self):
        video_serializer = VideoSerializer(data={},
                                           context={'request': mock.Mock()})
        writable_fields = [
            name for (name, field) in video_serializer.fields.items()
            if not field.read_only
        ]
        assert_items_equal(writable_fields, [
            'video_url',
            'title',
            'description',
            'duration',
            'primary_audio_language_code',
            'thumbnail',
            'metadata',
            'team',
            'project',
        ])

    def test_writable_fields_update(self):
        video_serializer = VideoSerializer(instance=VideoFactory(), data={},
                                           context={'request': mock.Mock()})
        writable_fields = [
            name for (name, field) in video_serializer.fields.items()
            if not field.read_only
        ]
        assert_items_equal(writable_fields, [
            'title',
            'description',
            'duration',
            'primary_audio_language_code',
            'thumbnail',
            'metadata',
            'team',
            'project',
        ])

    def test_create_with_team(self):
        team = TeamFactory(slug='test-team')
        data = {
            'video_url': 'http://example.com/video.mp4',
            'team': 'test-team',
        }
        result = self.run_create(data)
        assert_equal(result.get_team_video().team, team)

    def test_add_to_team(self):
        team = TeamFactory(slug='test-team')
        self.run_update({ 'team': 'test-team', })
        assert_equal(self.video.get_team_video().team, team)

    def test_move_team(self):
        team1 = TeamFactory(slug='team1')
        team2 = TeamFactory(slug='team2')
        TeamVideoFactory(video=self.video, team=team1)
        self.run_update({ 'team': 'team2' })
        assert_equal(self.video.get_team_video().team, team2)
        assert_equal(self.video_moved_from_team_to_team_handler.call_count, 1)

    def test_remove_team(self):
        team = TeamFactory(slug='team')
        TeamVideoFactory(video=self.video, team=team)
        self.run_update({ 'team': None })
        assert_equal(test_utils.reload_obj(self.video).get_team_video(), None)

    def test_set_project(self):
        project = ProjectFactory()
        self.run_update({
            'team': project.team.slug,
            'project': project.slug,
        })
        team_video = self.video.get_team_video()
        assert_equal(team_video.project, project)
        # None signifies the default project
        self.run_update({
            'team': project.team.slug,
            'project': None,
        })
        assert_true(
            test_utils.reload_obj(team_video).project.is_default_project
        )

    def test_update_without_team_or_project(self):
        # if we run an update without team or project field, we should keep it
        # in its current place
        team = TeamFactory(slug='team', admin=self.user)
        project = ProjectFactory(team=team)
        TeamVideoFactory(video=self.video, team=team, project=project)
        self.run_update({ 'title': 'new-title'})
        team_video = test_utils.reload_obj(self.video).get_team_video()
        assert_equal(team_video.team, team)
        assert_equal(team_video.project, project)

    def test_add_to_invalid_team(self):
        with assert_raises(ValidationError):
            self.run_update({
                'team': 'non-existent-team',
            })

    def test_update_with_blank_values(self):
        # test that blank values don't overwrite existing values
        self.video.primary_audio_language_code = 'en'
        self.video.title = 'orig-title'
        self.video.description = 'orig-description'
        self.video.duration = 100
        self.video.save()
        orig_thumbnail = 'http://example.com/new-thumbnail.png'
        self.video.thumbnail = orig_thumbnail
        project = ProjectFactory(team__slug='test-team', slug='test-project')
        TeamVideoFactory(video=self.video, team=project.team, project=project)
        result = self.run_update({
            'primary_audio_language_code': '',
            'title': '',
            'duration': '',
            'description': '',
            'duration': '',
            'thumbnail': '',
            'project': '',
            'team': '',
        })
        assert_equal(result.primary_audio_language_code, 'en')
        assert_equal(result.title, 'orig-title')
        assert_equal(result.description, 'orig-description')
        assert_equal(result.duration, 100)
        assert_equal(result.thumbnail, orig_thumbnail)
        team_video = result.get_team_video()
        assert_equal(team_video.team.slug, 'test-team')
        assert_equal(team_video.project.slug, 'test-project')

    def test_null_team_string(self):
        # sending the string "null" for team should work the same as sending
        # None
        TeamVideoFactory(video=self.video)
        result = self.run_update({
            'team': 'null',
        })
        assert_equal(test_utils.reload_obj(result).get_team_video(), None)

    def test_null_project_string(self):
        # sending the string "null" for project should work the same as
        # sending None
        team = TeamFactory()
        project = ProjectFactory(team=team)
        TeamVideoFactory(video=self.video, team=team, project=project)
        result = self.run_update({
            'team': team.slug,
            'project': 'null'
        })
        assert_true(result.get_team_video().project.is_default_project)

class VideoSerializerTeamChangeTest(TestCase):
    def setUp(self):
        self.team = TeamFactory(slug='team')
        self.other_team = TeamFactory(slug='other-team')
        self.team_video = TeamVideoFactory(team=self.team).video
        self.non_team_video = VideoFactory()

    def make_serializer(self, instance, data):
        serializer = VideoSerializer(instance=instance, data=data, context={
            'request': mock.Mock(),
        })
        serializer.is_valid(raise_exception=True)
        return serializer

    def test_creating_with_a_team(self):
        serializer = self.make_serializer(None, {
            'video_url': 'http://example.com/video.mp4',
            'team': self.team.slug,
        })
        assert_true(serializer.will_add_video_to_team())
        assert_false(serializer.will_remove_video_from_team())

    def test_create_without_team(self):
        serializer = self.make_serializer(None, {
            'video_url': 'http://example.com/video.mp4',
        })
        assert_false(serializer.will_add_video_to_team())
        assert_false(serializer.will_remove_video_from_team())

    def test_update_with_team(self):
        serializer = self.make_serializer(self.non_team_video, {
            'team': self.team.slug,
        })
        assert_true(serializer.will_add_video_to_team())
        assert_false(serializer.will_remove_video_from_team())

    def test_update_with_different_team(self):
        serializer = self.make_serializer(self.team_video, {
            'team': self.other_team.slug,
        })
        assert_true(serializer.will_add_video_to_team())
        assert_true(serializer.will_remove_video_from_team())

    def test_update_with_different_project(self):
        other_project = ProjectFactory(team=self.team,
                                       slug='new-project')
        serializer = self.make_serializer(self.team_video, {
            'team': self.team.slug,
            'project': other_project.slug,
        })
        assert_true(serializer.will_add_video_to_team())
        assert_false(serializer.will_remove_video_from_team())

    def test_update_with_no_changes(self):
        serializer = self.make_serializer(self.team_video, {
            'team': self.team.slug,
            'project': self.team.default_project.slug,
        })
        assert_false(serializer.will_add_video_to_team())
        assert_false(serializer.will_remove_video_from_team())

    def test_update_with_fields_missing(self):
        # simulate an update that doesn't have the team/project fields.  IN
        # this case we shouldn't touch the team video
        serializer = self.make_serializer(self.team_video, {
            'title': 'new-title',
        })
        assert_false(serializer.will_add_video_to_team())
        assert_false(serializer.will_remove_video_from_team())

class VideoViewSetTest(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.viewset = VideoViewSet()
        self.query_params = {
        }
        self.viewset.request = mock.Mock(user=self.user,
                                         query_params=self.query_params)
        self.viewset.kwargs = {}

    def test_listing(self):
        public_team = TeamFactory()
        private_team = TeamFactory(is_visible=False)
        user_team = TeamFactory(is_visible=False, member=self.user)

        v1 = VideoFactory(title='public video')
        v2 = VideoFactory(title='public team video')
        v3 = VideoFactory(title='user team video')
        v4 = VideoFactory(title='private team video')
        TeamVideoFactory(video=v2, team=public_team)
        TeamVideoFactory(video=v3, team=user_team)
        TeamVideoFactory(video=v4, team=private_team)

        assert_items_equal([v1, v2, v3], self.viewset.get_queryset())

    @test_utils.patch_for_test('subtitles.workflows.get_workflow')
    def test_get_detail_checks_workflow_permissions(self, mock_get_workflow):
        video = VideoFactory()
        workflow = mock.Mock()
        workflow.user_can_view_video.return_value = True
        mock_get_workflow.return_value = workflow
        # test successful permissions check
        self.viewset.kwargs['video_id'] = video.video_id
        assert_equal(self.viewset.get_object(), video)
        # test failed permissions check
        workflow.user_can_view_video.return_value = False
        with assert_raises(PermissionDenied):
            self.viewset.get_object()

    def test_get_detail_returns_403_when_video_not_found(self):
        # for non-staff users, if they try to get a video ID that's not in the
        # DB, we should return a 403 error.  This way they can't use the API
        # to query if a team video exists or not.
        self.viewset.kwargs['video_id'] = 'bad-video-id'
        with assert_raises(PermissionDenied):
            self.viewset.get_object()

    def test_video_url_filter(self):
        v1 = VideoFactory(title='correct video url')
        v2 = VideoFactory(title='other video url')
        self.query_params['video_url'] = v1.get_video_url()
        assert_items_equal([v1], self.viewset.get_queryset())

    def test_team_filter(self):
        team = TeamFactory()
        v1 = VideoFactory(title='correct team')
        v2 = VideoFactory(title='wrong team')
        v3 = VideoFactory(title='not in team')
        TeamVideoFactory(team=team, video=v1)
        TeamVideoFactory(video=v2)
        self.query_params['team'] = team.slug
        assert_items_equal([v1], self.viewset.get_queryset())

    def test_project_filter(self):
        team = TeamFactory()
        project = ProjectFactory(team=team, slug='project')
        other_project = ProjectFactory(team=team, slug='wrong-project')
        v1 = VideoFactory(title='correct project')
        v2 = VideoFactory(title='wrong project')
        v3 = VideoFactory(title='default project')
        v4 = VideoFactory(title='no team')
        TeamVideoFactory(video=v1, team=team, project=project)
        TeamVideoFactory(video=v2, team=team, project=other_project)
        TeamVideoFactory(video=v3, team=team)

        self.query_params['team'] = team.slug
        self.query_params['project'] = project.slug
        assert_items_equal([v1], self.viewset.get_queryset())

    def test_default_project_filter(self):
        team = TeamFactory()
        project = ProjectFactory(team=team, slug='project-slug')
        v1 = VideoFactory(title='in default project')
        v2 = VideoFactory(title='not in default project')
        TeamVideoFactory(video=v1, team=team)
        TeamVideoFactory(video=v2, team=team, project=project)

        self.query_params['team'] = team.slug
        self.query_params['project'] = 'null'
        assert_items_equal([v1], self.viewset.get_queryset())

    def test_team_filter_user_is_not_member(self):
        team = TeamFactory(is_visible=False)
        video = TeamVideoFactory(team=team).video
        self.query_params['team'] = team.slug
        assert_items_equal([], self.viewset.get_queryset())

class ViewSetCreateUpdateTestCase(TestCase):
    def setUp(self):
        # set up a bunch of mock objects so that we can test VideoViewSetTest
        # methods.
        self.team = TeamFactory()
        self.project = ProjectFactory(team=self.team)
        self.user = UserFactory()
        self.serializer = mock.Mock(validated_data={
            'team': self.team,
            'project': self.project,
        })
        self.serializer.will_add_video_to_team.return_value = False
        self.serializer.will_remove_video_from_team.return_value = False
        self.viewset = VideoViewSet()
        self.viewset.request = mock.Mock(user=self.user)

    @test_utils.patch_for_test('teams.permissions.can_add_video')
    def test_add_videos_perm_check(self, mock_can_add_video):
        # if will_add_video_to_team() returns False, we shouldn't check the
        # permission
        mock_can_add_video.return_value = True
        self.serializer.will_add_video_to_team.return_value = False
        self.viewset.check_save_permissions(self.serializer)
        assert_equal(mock_can_add_video.call_count, 0)
        # if will_add_video_to_team() returns True, we should
        self.serializer.will_add_video_to_team.return_value = True
        self.viewset.check_save_permissions(self.serializer)
        assert_equal(mock_can_add_video.call_count, 1)
        assert_equal(mock_can_add_video.call_args, mock.call(
            self.team, self.user, self.project))
        # test can_add_video returning False
        mock_can_add_video.return_value = False
        with assert_raises(PermissionDenied):
            self.viewset.check_save_permissions(self.serializer)

    @test_utils.patch_for_test('teams.permissions.can_remove_video')
    def test_remove_video_perm_check(self, mock_can_remove_video):
        team_video = TeamVideoFactory(team=self.team)
        self.serializer.instance = team_video.video
        mock_can_remove_video.return_value = True
        # if will_remove_video_from_team() returns False, we shouldn't check the
        # permission
        self.serializer.will_remove_video_from_team.return_value = False
        self.viewset.check_save_permissions(self.serializer)
        assert_equal(mock_can_remove_video.call_count, 0)
        # if will_remove_video_from_team() returns True, we should
        self.serializer.will_remove_video_from_team.return_value = True
        self.viewset.check_save_permissions(self.serializer)
        assert_equal(mock_can_remove_video.call_count, 1)
        assert_equal(mock_can_remove_video.call_args, mock.call(
            team_video, self.user))
        # test mock_can_remove_video returning False
        mock_can_remove_video.return_value = False
        with assert_raises(PermissionDenied):
            self.viewset.check_save_permissions(self.serializer)

    @test_utils.patch_for_test('videos.tasks.video_changed_tasks')
    def test_perform_update_runs_task(self, mock_video_changed_tasks):
        video = VideoFactory()
        self.serializer.save.return_value = video
        self.viewset.perform_update(self.serializer)
        assert_equal(mock_video_changed_tasks.delay.call_count, 1)
        assert_equal(mock_video_changed_tasks.delay.call_args,
                     mock.call(video.pk))
