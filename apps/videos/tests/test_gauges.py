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


from django.test import TestCase
import mock

from subtitles import pipeline
from utils.factories import *
from videos.tasks import gauge_videos, gauge_videos_long

class TestGauges(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.gauges = {}
        self.patcher = mock.patch('videos.tasks.Gauge',
                                  new=mock.Mock(side_effect=self.make_guage))
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        TestCase.tearDown(self)

    def make_guage(self, name):
        if name not in self.gauges:
            self.gauges[name] = mock.Mock()
        return self.gauges[name]

    def test_gauge_videos(self):
        videos = [VideoFactory() for i in range(10)]
        # video #1 has 1 language with 1 version
        pipeline.add_subtitles(videos[0], 'en', None)
        # video #2 has 2 languages with 1 version
        pipeline.add_subtitles(videos[1], 'en', None)
        pipeline.add_subtitles(videos[1], 'fr', None)
        # video #3 has 2 languages with 2 versions
        pipeline.add_subtitles(videos[2], 'de', None)
        pipeline.add_subtitles(videos[2], 'de', None)
        pipeline.add_subtitles(videos[2], 'pt-br', None)
        pipeline.add_subtitles(videos[2], 'pt-br', None)
        gauge_videos()
        self.assertEquals(set(self.gauges.keys()), set([
            'videos.Video',
            'videos.Video-captioned',
            'videos.SubtitleVersion',
            'videos.SubtitleLanguage',
        ]))
        gauges = self.gauges
        gauges['videos.Video'].report.assert_called_once_with(10)
        gauges['videos.Video-captioned'].report.assert_called_once_with(3)
        gauges['videos.SubtitleVersion'].report.assert_called_once_with(7)
        gauges['videos.SubtitleLanguage'].report.assert_called_once_with(5)

    def test_gauge_videos_long(self):
        video1 = VideoFactory()
        video2 = VideoFactory()
        pipeline.add_subtitles(video1, 'de', [
            (100, 200, "foo",{'new_paragraph':True} ),
            (300, 400, "bar",{'new_paragraph':True} ),
        ])
        pipeline.add_subtitles(video2, 'en', [
            (100, 200, "foo",{'new_paragraph':True} ),
            (300, 400, "bar",{'new_paragraph':True} ),
        ])
        pipeline.add_subtitles(video2, 'en', [
            (100, 200, "foo",{'new_paragraph':True} ),
            (300, 400, "bar",{'new_paragraph':True} ),
            (500, 600, "baz",{'new_paragraph':True} ),
        ])
        gauge_videos_long()
        self.assertEquals(set(self.gauges.keys()), set([
            'videos.Subtitle',
        ]))
        self.gauges['videos.Subtitle'].report.assert_called_once_with(5)
