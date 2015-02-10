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

"""Implement pagination.

This module has a bunch of code to overrides the default paginate_queryset()
method to use offset/limit based pagination instead of page based pagination.

This will get much simpler  once we switch to django-rest-framework 3.1 which
has built-in support for this.
"""

import urlparse

from django.http import Http404, QueryDict
from rest_framework import pagination
from rest_framework import serializers

class MetaSerializer(serializers.Serializer):
    previous = serializers.SerializerMethodField()
    next = serializers.SerializerMethodField()
    offset = serializers.IntegerField(read_only=True)
    limit = serializers.IntegerField(read_only=True)
    total_count = serializers.IntegerField(read_only=True)

    def get_next(self, page):
        if page.has_next():
            return self._make_link(page.next_offset(), page.limit)
        else:
            return None

    def get_previous(self, page):
        if page.has_previous():
            return self._make_link(page.previous_offset(), page.limit)
        else:
            return None

    def _make_link(self, offset, limit):
        request = self.context.get('request')
        url = request and request.build_absolute_uri() or ''
        (scheme, netloc, path, query, fragment) = urlparse.urlsplit(url)
        query_dict = QueryDict(query).copy()
        query_dict['offset'] = offset
        query_dict['limit'] = limit
        query = query_dict.urlencode()
        return urlparse.urlunsplit((scheme, netloc, path, query, fragment))

class AmaraPaginationSerializer(pagination.BasePaginationSerializer):
    meta = MetaSerializer(source='*')

    results_field = 'objects'

class AmaraPage(object):
    def __init__(self, queryset, offset, limit):
        self.object_list = queryset[offset:offset+limit]
        self.total_count = queryset.count()
        self.offset = offset
        self.limit = limit

    def has_next(self):
        return self.offset + self.limit < self.total_count

    def next_offset(self):
        return self.offset + self.limit

    def has_previous(self):
        return self.offset > 0

    def previous_offset(self):
        return max(self.offset - self.limit, 0)

class AmaraPaginationMixin(object):
    paginate_by_param = 'limit'
    max_paginate_by = 100

    def paginate_queryset(self, queryset):
        limit = self.get_paginate_by()
        if not limit:
            return None
        print self, limit

        offset = self.request.query_params.get('offset', 0)
        try:
            offset = int(offset)
        except ValueError:
            offset = 0
        return AmaraPage(queryset, offset, limit)

