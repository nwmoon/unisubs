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

from videos.types.base import VideoType
from vidscraper.sites import blip
from django.utils.html import strip_tags
# FIXME: we should just call the module "json" but that conflicts with our
# variable names
import json as simplejson

import urllib2

import re

class BlipTvVideoType(VideoType):

    abbreviation = 'B'
    name = 'Blip.tv'  
    site = 'blip.tv'

    pattern = re.compile(r"^https?://blip.tv/(?P<subsite>[a-zA-Z0-9-]+)/(?P<file_id>[a-zA-Z0-9-]+)/?$")
    
    def __init__(self, url):
        self.url = url
        self.subsite, self.file_id = self._parse_url()
        self.json = self._fetch_json()
    
    def convert_to_video_url(self):
        return "http://blip.tv/%s/%s" % (self.subsite, self.file_id)

    @property
    def video_id(self):
        if self.json and 'embedLookup' in self.json:
            return self.json['embedLookup']
        else:
            return None

    @classmethod
    def matches_video_url(cls, url):
        return cls.pattern.match(url)

    def set_values(self, video_obj):
        json = self.json

        if 'title' in json:
            video_obj.title = unicode(json['title'])
        
        if 'description' in json:
            video_obj.description = unicode(json['description'])

        if 'media' in json:
            video_obj.duration = int(json['media']['duration'])

        if 'thumbnailUrl' in json:
            video_obj.thumbnail = json['thumbnailUrl']

    def _parse_url(self):
        matches = self.pattern.match(self.url).groupdict()
        return matches['subsite'], matches['file_id']

    def _fetch_json(self):
        # bliptv just knows how to return jsonp. argh.
        url = self.url + "?skin=json&callback="

        try:
            jsonp = urllib2.urlopen(url).read().strip()
        except Exception:
            return {}

        # strip the json parentesis. argh.
        if jsonp.endswith(');'):
            jsonp = jsonp[1:-2]

        json = simplejson.loads(jsonp)
        return json[0].get('Post', {}) if len(json) > 0 else None
