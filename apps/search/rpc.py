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

from utils.rpc import add_request_to_kwargs
from search.forms import SearchForm
from videos.search_indexes import VideoSearchResult, VideoIndex

from videos.models import Video
from django.template.loader import render_to_string
from videos.rpc import render_page
from django.template import RequestContext
from django.core.cache import cache

class SearchApiClass(object):
    def search(self, rdata, user):
        try:
            return self._search(rdata, user)
        except StandardError:
            import traceback
            traceback.print_exc()
            raise

    def _search(self, rdata, user):
        form = SearchForm(rdata)

        output = render_page(rdata.get('page', 1), form.queryset(), 20)
        output['sidebar'] = render_to_string('search/_sidebar.html', {
            'form': form,
            'rdata': rdata,
        })

        # Assume we're currently indexing if the number of public
        # indexed vids differs from the count of video objects by
        # more than 1000
        is_indexing = cache.get('is_indexing')
        if is_indexing is None:
            is_indexing = Video.objects.all().count() - VideoIndex.public().count() > 1000
            cache.set('is_indexing', is_indexing, 300)

        output['is_indexing'] = is_indexing

        return output
