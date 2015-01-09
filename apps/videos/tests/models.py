# -*- coding: utf-8 -*-
# Amara, universalsubtitles.org
#
# Copyright (C) 2013 Participatory Culture Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see
# http://www.gnu.org/licenses/agpl-3.0.html.

from django.db import IntegrityError
from django.test import TestCase
from nose.tools import *
import babelsubs
import mock

from auth.models import CustomUser as User
from subtitles import pipeline
from subtitles.models import SubtitleLanguage
from videos.models import Action, Video
from videos.tasks import video_changed_tasks
from videos.tests.data import (
    get_video, make_subtitle_language, make_subtitle_version, make_rollback_to
)
from widget import video_cache
from utils.subtitles import dfxp_merge
from utils import test_utils
from utils.factories import *

def refresh(m):
    return m.__class__._default_manager.get(pk=m.pk)

class TestVideoUrl(TestCase):
    def setUp(self):
        self.video = VideoFactory()
        self.primary_url = self.video.get_primary_videourl_obj()
        self.url = VideoURLFactory(video=self.video)
        self.user = UserFactory()

    def test_remove(self):
        self.url.remove(self.user)
        assert_equal(self.video.videourl_set.count(), 1)

    def test_remove_creates_action(self):
        self.url.remove(self.user)
        action = self.video.action_set.get(action_type=Action.DELETE_URL)
        assert_equal(action.user, self.user)
        # we use new_video_title to store the removed uRL
        assert_equal(action.new_video_title, self.url.url)

    def test_remove_primary(self):
        with assert_raises(IntegrityError):
            self.primary_url.remove(self.user)

class TestVideo(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.youtube_video = 'http://www.youtube.com/watch?v=pQ9qX8lcaBQ'
        self.html5_video = 'http://mirrorblender.top-ix.org/peach/bigbuckbunny_movies/big_buck_bunny_1080p_stereo.ogg'

    def test_get_or_create_for_url(self):
        def _assert_create_and_get(video_url):
            video, created = Video.get_or_create_for_url(video_url)
            self.assertIsNotNone(video)
            self.assertTrue(created)

            video2, created = Video.get_or_create_for_url(video_url)
            self.assertEqual(video.pk, video2.pk)
            self.assertFalse(created)

        _assert_create_and_get(self.youtube_video)
        _assert_create_and_get(self.html5_video)

    def test_url_cache(self):
        test_utils.invalidate_widget_video_cache.run_original_for_test()
        video = get_video(1)
        video_url = video.get_video_url()

        # After adding the video, we should be able to look up its ID in the
        # cache, given just the URL.
        cache_id_1 = video_cache.get_video_id(video_url)
        self.assertIsNotNone(cache_id_1)
        self.assertTrue(Video.objects.filter(video_id=cache_id_1).exists())

        # Remove the video (and make sure it's gone).
        video.delete()
        self.assertFalse(Video.objects.exists())

        # Trying to get the video ID out of the cache now actually *creates* the
        # video!
        cache_id_2 = video_cache.get_video_id(video_url)
        self.assertTrue(Video.objects.exists())

        # The video_id will be different than before (since this is a new Video
        # record) and the cache should have been updated properly.
        self.assertNotEqual(cache_id_1, cache_id_2)
        self.assertTrue(Video.objects.filter(video_id=cache_id_2).exists())

        # Now try to create a new video with the same URL.  This should return
        # the existing video.
        video2, created = Video.get_or_create_for_url(video_url)
        self.assertFalse(created)

        video2_url = video2.get_video_url()

        # The cache should still have the correct ID, of course.
        cache_id_3 = video_cache.get_video_id(video2_url)
        self.assertEqual(cache_id_2, cache_id_3)
        self.assertEqual(Video.objects.count(), 1)

    def test_video_title(self):
        video = get_video(url='http://www.youtube.com/watch?v=pQ9qX8lcaBQ')

        def _assert_title(correct_title):
            self.assertEquals(refresh(video).title, correct_title)

        # Test title before any subtitles are added.
        _assert_title(test_utils.test_video_info.title)

        # Make a subtitle language in the primary language.
        video.primary_audio_language_code = 'en'
        video.save()
        sl_en = make_subtitle_language(video, 'en')

        # Just adding languages shouldn't affect the title.
        _assert_title(test_utils.test_video_info.title)

        # Add subtitles with a custom title.  The title should be updated to
        # reflect this.
        make_subtitle_version(sl_en, [], title="New Title")
        _assert_title("New Title")

        # New versions should continue update the title properly.
        make_subtitle_version(sl_en, [], title="New Title 2")
        _assert_title("New Title 2")

        # Versions in a non-primary-audio-language should not affect the video
        # title.
        sl_ru = make_subtitle_language(video, 'ru')
        make_subtitle_version(sl_ru, [], title="New Title 3")
        _assert_title("New Title 2")

        # Rollbacks (of the primary audio language) should affect the title just
        # like a new version.
        make_rollback_to(sl_en, 1)
        _assert_title("New Title")

class TestModelsSaving(TestCase):
    # TODO: These tests may be more at home in the celery_tasks test file...
    def test_video_languages_count(self):
        # TODO: Merge this into the metadata tests file?
        video = get_video()

        # Start with no languages.
        self.assertEqual(video.languages_count, 0)
        self.assertEqual(video.newsubtitlelanguage_set.having_nonempty_tip()
                                                      .count(),
                         0)

        # Create one.
        sl_en = make_subtitle_language(video, 'en')
        make_subtitle_version(sl_en, [(100, 200, "foo")])

        # The query should immediately show it.
        self.assertEqual(video.newsubtitlelanguage_set.having_nonempty_tip()
                                                      .count(),
                         1)

        # But the model object will not.
        self.assertEqual(video.languages_count, 0)

        # Even if we refresh it, the model still doesn't show it.
        video = Video.objects.get(pk=video.pk)
        self.assertEqual(video.languages_count, 0)

        # Until we run the proper tasks.
        video_changed_tasks.delay(video.pk)

        # But we still need to refresh it to see the change.
        self.assertEqual(video.languages_count, 0)
        video = Video.objects.get(pk=video.pk)
        self.assertEqual(video.languages_count, 1)

    def test_subtitle_language_save(self):
        def _refresh(video):
            video_changed_tasks.delay(video.pk)
            return Video.objects.get(pk=video.pk)

        # Start out with a video with one language.
        # By default languages are not complete, so the video should not be
        # complete either.
        video = get_video()
        sl_en = make_subtitle_language(video, 'en')
        self.assertIsNone(video.complete_date)
        self.assertEqual(video.newsubtitlelanguage_set.count(), 1)

        # Marking the language as complete doesn't complete the video on its own
        # -- we need at least one version!
        sl_en.subtitles_complete = True
        sl_en.save()
        video = _refresh(video)
        self.assertIsNone(video.complete_date)

        # But an unsynced version can't be complete either!
        # TODO: uncomment once babelsubs supports unsynced subs...
        # make_subtitle_version(sl_en, [(100, None, "foo")])
        # video = _refresh(video)
        # self.assertIsNone(video.complete_date)

        # A synced version (plus the previously set flag on the language) should
        # result in a completed video.
        make_subtitle_version(sl_en, [(100, 200, "foo")])
        video = _refresh(video)
        self.assertIsNotNone(video.complete_date)

        # Unmarking the language as complete should uncomplete the video.
        sl_en.subtitles_complete = False
        sl_en.save()
        video = _refresh(video)
        self.assertIsNone(video.complete_date)

        # Any completed language is enough to complete the video.
        sl_ru = make_subtitle_language(video, 'ru')
        make_subtitle_version(sl_ru, [(100, 200, "bar")])
        sl_ru.subtitles_complete = True
        sl_ru.save()

        video = _refresh(video)
        self.assertIsNotNone(video.complete_date)

class TestSubtitleLanguageCaching(TestCase):
    def setUp(self):
        self.videos, self.langs, self.versions = bulk_subs({
            'video': {
                'en': [
                    {},
                    {},
                    {}
                ],
                'es': [
                    {},
                ],
                'fr': [
                    {},
                    {'visibility': 'private'},
                ],
            },
        })
        self.video = self.videos['video']

    def test_fetch_one_language(self):
        self.assertEquals(self.video.subtitle_language('en').id,
                          self.langs['video', 'en'].id)

    def test_fetch_all_languages(self):
        self.assertEquals(
            set(l.id for l in self.video.all_subtitle_languages()),
            set(l.id for l in self.langs.values()))

    def test_cache_one_language(self):
        # the first call should result in a query
        with self.assertNumQueries(1):
            lang = self.video.subtitle_language('en')
        # subsequent calls shouldn't
        with self.assertNumQueries(0):
            self.assertEquals(self.video.subtitle_language('en'), lang)
            # the language video should be cached as well
            lang.video
        # but they should once we clear the cache
        self.video.clear_language_cache()
        with self.assertNumQueries(1):
            self.video.subtitle_language('en')

    def test_cache_all_languages(self):
        with self.assertNumQueries(1):
            languages = self.video.all_subtitle_languages()

        lang_map = dict((l.language_code, l) for l in languages)
        with self.assertNumQueries(0):
            self.assertEquals(set(languages),
                              set(self.video.all_subtitle_languages()))
            # the videos should be cached
            for lang in languages:
                lang.video
            # fetching one video should use the cache as well
            self.assertEquals(self.video.subtitle_language('en'),
                              lang_map['en'])
        self.video.clear_language_cache()
        with self.assertNumQueries(1):
            self.video.all_subtitle_languages()

    def test_non_existant_language(self):
        # subtitle_language() should return None for non-existant languages
        self.assertEquals(self.video.subtitle_language('pt-br'), None)
        # we should cache that result
        with self.assertNumQueries(0):
            self.assertEquals(self.video.subtitle_language('pt-br'), None)
        # just because None is in the cache, we shouldn't return it from
        # all_subtitle_languages()
        for lang in self.video.all_subtitle_languages():
            self.assertNotEquals(lang, None)
        # try that again now that all the languages are cached
        for lang in self.video.all_subtitle_languages():
            self.assertNotEquals(lang, None)

    def test_prefetch(self):
        self.video.prefetch_languages()
        with self.assertNumQueries(0):
            self.video.all_subtitle_languages()
            lang = self.video.subtitle_language('en')
            # fetching the video should be cached
            lang.video

    def test_prefetch_some_languages(self):
        self.video.prefetch_languages(languages=['en', 'es'])
        with self.assertNumQueries(0):
            self.video.subtitle_language('en')
            self.video.subtitle_language('es')
        with self.assertNumQueries(1):
            self.video.subtitle_language('fr')

    def test_prefetch_with_tips(self):
        self.video.prefetch_languages(with_public_tips=True,
                                      with_private_tips=True)
        with self.assertNumQueries(0):
            for lang in self.video.all_subtitle_languages():
                # fetching the tips should be cached
                lang.get_tip(public=True)
                lang.get_tip(public=False)
                # fetching the version video should be cached
                lang.get_tip(public=True).video
                lang.get_tip(public=False).video


class TestGetMergedDFXP(TestCase):
    def test_get_merged_dfxp(self):
        video = VideoFactory(primary_audio_language_code='en')
        pipeline.add_subtitles(video, 'en', [
            (100, 200, 'text'),
        ])
        pipeline.add_subtitles(video, 'fr', [
            (100, 200, 'french text'),
        ])
        pipeline.add_subtitles(video, 'es', [
            (100, 200, 'spanish text'),
        ])
        pipeline.add_subtitles(video, 'de', [
            (100, 200, 'spanish text'),
        ], visibility='private')

        video.clear_language_cache()

        subtitles = [
            video.subtitle_language(lang).get_public_tip().get_subtitles()
            for lang in ('en', 'fr', 'es')
        ]

        self.assertEquals(video.get_merged_dfxp(), dfxp_merge(subtitles))
