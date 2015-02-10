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

from django.conf import settings
from django.db.models import Count
from haystack import site
from haystack.backends import SQ
from haystack.indexes import (
    IntegerField, CharField, BooleanField, SearchIndex, DateTimeField,
    MultiValueField
)
from haystack.query import SearchQuerySet
from teams import models
from subtitles.models import SubtitleLanguage

from haystack.exceptions import AlreadyRegistered


class TeamVideoLanguagesIndex(SearchIndex):
    text = CharField(
        document=True, use_template=True,
        template_name="teams/teamvideo_languages_for_search.txt")
    team_id = IntegerField()
    team_video_pk = IntegerField(indexed=False)
    video_pk = IntegerField(indexed=False)
    video_id = CharField(indexed=False)
    video_title = CharField(faceted=True)
    video_url = CharField(indexed=False)
    original_language = CharField()
    original_language_display = CharField(indexed=False)
    absolute_url = CharField(indexed=False)
    project_pk = IntegerField(indexed=True)
    task_count = IntegerField()
    # never store an absolute url with solr
    # since the url changes according to the user
    # one cannot construct the url at index time
    # video_absolute_url = CharField(indexed=False)
    thumbnail = CharField(indexed=False)
    title = CharField()
    project_name = CharField(indexed=False)
    project_slug = CharField(indexed=False)
    description = CharField(indexed=True)
    is_complete = BooleanField()
    video_complete_date = DateTimeField(null=True)
    # list of completed language codes
    video_completed_langs = MultiValueField()
    # list of completed language absolute urls. should have 1-1 mapping to video_compelted_langs
    video_completed_lang_urls = MultiValueField(indexed=False)

    latest_submission_date = DateTimeField(null=True)
    team_video_create_date = DateTimeField()

    # possible values for visibility:
    # is_public=True anyone can see
    # is_public=False and owned_by_team_id=None -> a regular user owns, no teams can list this video
    # is_public=False and owned_by_team_id=X -> only team X can see this video
    is_public = BooleanField()
    owned_by_team_id = IntegerField(null=True)

    # All subtitle languages containing at least one version are included in the total count.
    num_total_langs = IntegerField()

    # Completed languages are languages which have at least one version that is:
    #
    # * Public
    # * Covers all dialog
    # * Fully synced
    # * Fully translated, if a translation
    num_completed_langs = IntegerField()

    def prepare(self, obj):
        self.prepared_data = super(TeamVideoLanguagesIndex, self).prepare(obj)
        self.prepared_data['team_id'] = obj.team.id
        self.prepared_data['team_video_pk'] = obj.id
        self.prepared_data['video_pk'] = obj.video.id
        self.prepared_data['video_id'] = obj.video.video_id
        self.prepared_data['video_title'] = obj.video.title.strip()
        self.prepared_data['video_url'] = obj.video.get_video_url()

        original_sl = obj.video.subtitle_language()

        if original_sl:
            self.prepared_data['original_language_display'] = original_sl.get_language_code_display
            self.prepared_data['original_language'] = original_sl.language_code
        else:
            self.prepared_data['original_language_display'] = ''
            self.prepared_data['original_language'] = ''

        self.prepared_data['absolute_url'] = obj.get_absolute_url()
        self.prepared_data['thumbnail'] = obj.get_thumbnail()
        self.prepared_data['title'] = obj.video.title_display()
        self.prepared_data['description'] = obj.description
        self.prepared_data['is_complete'] = obj.video.complete_date is not None
        self.prepared_data['video_complete_date'] = obj.video.complete_date
        self.prepared_data['project_pk'] = obj.project.pk
        self.prepared_data['project_name'] = obj.project.name
        self.prepared_data['project_slug'] = obj.project.slug
        self.prepared_data['team_video_create_date'] = obj.created

        completed_sls = list(obj.video.completed_subtitle_languages())
        all_sls = obj.video.newsubtitlelanguage_set.having_nonempty_tip()

        self.prepared_data['num_total_langs'] = all_sls.count()
        self.prepared_data['num_completed_langs'] = len(completed_sls)

        self.prepared_data['video_completed_langs'] = \
            [sl.language_code for sl in completed_sls]
        self.prepared_data['video_completed_lang_urls'] = \
            [sl.get_absolute_url() for sl in completed_sls]

        self.prepared_data['task_count'] = models.Task.objects.incomplete().filter(team_video=obj).count()

        team_video = obj.video.get_team_video()

        self.prepared_data['is_public'] =  team_video.team.is_visible 
        self.prepared_data["owned_by_team_id"] = team_video.team.id if team_video else None

        return self.prepared_data

    @classmethod
    def results_for_members(self, team):
        base_qs = SearchQuerySet().models(models.TeamVideo)
        public = SQ(is_public=True)
        mine = SQ(is_public=False, owned_by_team_id=team.pk)
        return base_qs.filter(public | mine)


    @classmethod
    def results(self):
        return SearchQuerySet().models(models.TeamVideo).filter(is_public=True)


try:
    site.register(models.TeamVideo, TeamVideoLanguagesIndex)
except AlreadyRegistered:
    # i hate python imports with all my will.
    # i hope they die.
    pass
