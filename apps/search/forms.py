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

from django import forms
from django.utils.translation import ugettext_lazy as _
from utils.translation import get_language_choices
from videos.search_indexes import VideoIndex

ALL_LANGUAGES = get_language_choices()

def _get_language_facet_counts(sqs):
    """Use haystack faceting to find the counts for the language fields

    The facet count data will be a list of (language_code, count) tuples.

    Return a tuple containing facet count data for the video language and
    the subtitle languages
    """

    sqs = sqs.facet('video_language').facet('languages')
    facet_counts = sqs.facet_counts()

    try:
        video_lang_counts = facet_counts['fields']['video_language']
    except KeyError:
        video_lang_counts = []

    try:
        language_counts = facet_counts['fields']['languages']
    except KeyError:
        language_counts = []

    return (video_lang_counts, language_counts)

class SearchForm(forms.Form):
    SORT_CHOICES = (
        ('score', _(u'Relevance')),
        ('languages_count', _(u'Most languages')),
        ('today_views', _(u'Views Today')),
        ('week_views', _(u'Views This Week')),
        ('month_views', _(u'Views This Month')),
        ('total_views', _(u'Total Views')),
    )
    q = forms.CharField(label=_(u'query'), required=False)
    langs = forms.ChoiceField(choices=ALL_LANGUAGES, required=False, label=_(u'Subtitled Into'),
                              help_text=_(u'Left blank for any language'), initial='')
    video_lang = forms.ChoiceField(choices=ALL_LANGUAGES, required=False, label=_(u'Video In'),
                              help_text=_(u'Left blank for any language'), initial='')

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)

        video_language_facet_counts, language_facet_counts = \
            _get_language_facet_counts(self.queryset_from_query())

        self.fields['video_lang'].choices = self._make_choices_from_faceting(
            video_language_facet_counts)

        self.fields['langs'].choices = self._make_choices_from_faceting(
            language_facet_counts)

    def has_any_criteria(self):
        return (self.cleaned_data['q'] or
                self.cleaned_data['langs'] or
                self.cleaned_data['video_lang'])

    def _make_choices_from_faceting(self, data):
        choices = []

        ALL_LANGUAGES_NAMES = dict(get_language_choices())

        for lang, val in data:
            try:
                choices.append((lang, u'%s (%s)' % (ALL_LANGUAGES_NAMES[lang], val), val))
            except KeyError:
                pass

        choices.sort(key=lambda item: item[-1], reverse=True)
        choices = list((item[0], item[1]) for item in choices)
        choices.insert(0, ('', _('All Languages')))

        return choices

    def queryset_from_query(self):
        q = self.data.get('q')
        if q:
            qs = VideoIndex.public()
            return (qs
                    .auto_query(q)
                    .filter_or(title=qs.query.clean(q)))
        else:
            return VideoIndex.public()

    def queryset(self):
        if not self.is_valid() or not self.has_any_criteria():
            return self.empty_queryset()
        ordering = self.cleaned_data.get('sort', '')
        langs = self.cleaned_data.get('langs')
        video_language = self.cleaned_data.get('video_lang')

        qs = self.queryset_from_query()

        #apply filtering
        if video_language:
            qs = qs.filter(video_language_exact=video_language)

        if langs:
            qs = qs.filter(languages_exact=langs)

        if ordering:
            qs = qs.order_by('-' + ordering)
        else:
            qs = qs.order_by('-score')

        return qs

    def empty_queryset(self):
        return VideoIndex.public().none()
