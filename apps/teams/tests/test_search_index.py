# Amara, universalsubtitles.org
#
# Copyright (C) 2014 Participatory Culture Foundation
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

from django.test import TestCase
from haystack import site

from teams.models import TeamVideo
from subtitles import pipeline
from utils.factories import *

class SearchRecordTest(TestCase):
    # test that we save the correct info in our search records

    # FIXME: This TestCase was written after other index-related tests and I
    # think we should try to remove a lot of the other tests and replace them
    # with this.  The old tests would use a live solr instance, and also
    # probably the django test web client.  These tests simple test that
    # TeamVideoLanguagesIndex stores the correct data.
    #
    # I think this approach is better because:
    #   - It's much faster
    #   - We don't have to worry about managing a solr instance
    #   - It's testing a smaller set of code, which seems good.  I didn't like
    #     that the old tests would be testing several different things at
    #     once: how we construct our querysets, how we prepare data to index,
    #     and how we handle updating the search via tasks.
    #   - If the test fails, it's a lot more obvious why

    def setUp(self):
        self.team_video = TeamVideoFactory()
        self.video = self.team_video.video
        self.team = self.team_video.team

    def get_prepared_data(self):
        return site.get_index(TeamVideo).prepare(self.team_video)

    def test_completed_langs(self):
        pipeline.add_subtitles(self.video, 'en', None, complete=True)
        pipeline.add_subtitles(self.video, 'fr', None, complete=True)
        pipeline.add_subtitles(self.video, 'es', None, complete=False)
        self.assertEquals(
            set(self.get_prepared_data()['video_completed_langs']),
            set(['en', 'fr']))
