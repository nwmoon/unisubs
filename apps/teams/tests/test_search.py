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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see
# http://www.gnu.org/licenses/agpl-3.0.html.

from __future__ import absolute_import

from datetime import datetime

from django.test import TestCase
from haystack import site
import mock

from subtitles import pipeline
from teams.models import TeamVideo
from utils.factories import *

class TeamVideoSearchIndexTestCase(TestCase):
    def setUp(self):
        member = TeamMemberFactory()
        self.team = member.team
        self.user = member.user

    def reindex_team_videos(self):
        site.get_index(TeamVideo).reindex()

    def check_search_results(self, **kwargs):
        if 'user' not in kwargs:
            kwargs['user'] = self.user
        correct = kwargs.pop('correct')
        results = self.team.get_videos_for_languages_haystack(**kwargs)
        self.assertEquals(
            set(r.title for r in results),
            set((tv.video.title_display()) for tv in correct))

    def test_search_by_language(self):
        # make a bunch of videos that either have or don't have french
        # subtitles.  Make sure we test both single languages and multiple
        # languages.
        tv1 = TeamVideoFactory(team=self.team)
        tv2 = TeamVideoFactory(team=self.team)
        tv3 = TeamVideoFactory(team=self.team)
        tv4 = TeamVideoFactory(team=self.team)
        pipeline.add_subtitles(tv1.video, 'en', None, complete=True)
        pipeline.add_subtitles(tv2.video, 'en', None, complete=True)
        pipeline.add_subtitles(tv2.video, 'es', None, complete=True)
        pipeline.add_subtitles(tv3.video, 'fr', None, complete=True)
        pipeline.add_subtitles(tv4.video, 'en', None, complete=True)
        pipeline.add_subtitles(tv4.video, 'fr', None, complete=True)
        self.reindex_team_videos()
        self.check_search_results(language='fr', correct=[tv3, tv4])
        self.check_search_results(exclude_language='fr', correct=[tv1, tv2])
