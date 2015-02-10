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

from __future__ import absolute_import

from babelsubs import storage
from django.test import TestCase

from externalsites.subfetch import should_fetch_subs, fetch_subs
from subtitles import pipeline
from subtitles.models import ORIGIN_IMPORTED
from utils import test_utils
from utils.factories import *

class SubFetchTestCase(TestCase):
    def test_should_fetch_subs(self):
        video_url = VideoFactory().get_primary_videourl_obj()
        youtube_url = YouTubeVideoFactory().get_primary_videourl_obj()

        self.assertEqual(should_fetch_subs(youtube_url), True)
        self.assertEqual(should_fetch_subs(video_url), False)

    @test_utils.patch_for_test("utils.youtube.get_subtitled_languages")
    @test_utils.patch_for_test("utils.youtube.get_subtitles")
    def test_fetch_subs(self, mock_get_subtitles,
                        mock_get_subtitled_languages):
        mock_get_subtitled_languages.return_value = ['en', 'fr']

        en_subs = storage.SubtitleSet('en')
        en_subs.append_subtitle(100, 200, 'text')
        fr_subs = storage.SubtitleSet('fr')
        fr_subs.append_subtitle(100, 200, 'french text')
        def get_subtitles(video_id, language_code):
            if language_code == 'en':
                return en_subs
            elif language_code == 'fr':
                return fr_subs
            else:
                raise ValueError(language_code)
        mock_get_subtitles.side_effect = get_subtitles

        video = YouTubeVideoFactory()
        video_url = video.get_primary_videourl_obj()
        fetch_subs(video_url)
        # check that we called the correct API methods
        self.assertEqual(mock_get_subtitled_languages.called, True)
        self.assertEqual(mock_get_subtitles.call_args_list, [
            ((video_url.videoid, 'en'), {}),
            ((video_url.videoid, 'fr'), {}),
        ])
        # check that we created the correct languages
        self.assertEqual(set(l.language_code for l in
                             video.all_subtitle_languages()),
                         set(['en', 'fr']))
        lang_en = video.subtitle_language('en')
        lang_fr = video.subtitle_language('fr')
        # check subtitle data
        self.assertEqual(lang_en.get_tip().get_subtitles().to_xml(),
                         en_subs.to_xml())
        self.assertEqual(lang_fr.get_tip().get_subtitles().to_xml(),
                         fr_subs.to_xml())
        # check additional data
        self.assertEqual(lang_en.subtitles_complete, True)
        self.assertEqual(lang_fr.subtitles_complete, True)
        self.assertEqual(lang_en.get_tip().origin, ORIGIN_IMPORTED)
        self.assertEqual(lang_fr.get_tip().origin, ORIGIN_IMPORTED)
        self.assertEqual(lang_en.get_tip().note, "From youtube")
        self.assertEqual(lang_fr.get_tip().note, "From youtube")

    @test_utils.patch_for_test("utils.youtube.get_subtitled_languages")
    @test_utils.patch_for_test("utils.youtube.get_subtitles")
    def test_fetch_subs_skips_existing_languages(self, mock_get_subtitles,
                                                 mock_get_subtitled_languages):
        # test that we don't try to get subtitles for languages that already
        # have data in the DB
        mock_get_subtitled_languages.return_value = ['en']

        video = YouTubeVideoFactory()
        video_url = video.get_primary_videourl_obj()
        existing_version = pipeline.add_subtitles(video, 'en', None)
        fetch_subs(video_url)
        self.assertEqual(mock_get_subtitles.call_count, 0)
        self.assertEqual(video.subtitle_language('en').get_tip(),
                         existing_version)

    @test_utils.patch_for_test("utils.youtube.get_subtitled_languages")
    @test_utils.patch_for_test("utils.youtube.get_subtitles")
    def test_fetch_subs_handles_bcp47_codes(self, mock_get_subtitles,
                                            mock_get_subtitled_languages):
        # youtube uses BCP-47 language codes.  Ensure that we use this code
        # when talking to youtube, but our own internal codes when storing
        # subtitles.
        mock_get_subtitled_languages.return_value = ['pt-BR']

        subs = storage.SubtitleSet('pt-br')
        subs.append_subtitle(100, 200, 'text')
        mock_get_subtitles.return_value = subs

        video = YouTubeVideoFactory()
        video_url = video.get_primary_videourl_obj()

        fetch_subs(video_url)
        mock_get_subtitles.assert_called_with(video_url.videoid, 'pt-BR')

        self.assertEqual(set(l.language_code for l in
                             video.all_subtitle_languages()),
                         set(['pt-br']))
