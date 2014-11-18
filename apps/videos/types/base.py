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

from urlparse import urlparse

from django.core.exceptions import ValidationError

class VideoType(object):

    abbreviation = None
    name = None    

    CAN_IMPORT_SUBTITLES = False

    def __init__(self, url):
        self.url = url

    @property
    def video_id(self):
        return

    @classmethod 
    def video_url(cls, obj):
        return obj.url
    
    def convert_to_video_url(self):
        return self.format_url(self.url)
    
    @classmethod
    def matches_video_url(cls, url):
        raise Exception('Not implemented')

    @staticmethod
    def url_extension(url):
        """Get the extension of an URL's path.

        Returns the extension as a lowercase string (without the "." part).
        If the path for url doesn't have an extension, None is returned.
        """

        parsed = urlparse(url)
        components = parsed.path.split('.')
        if len(components) == 1:
            # no extension at all
            return None
        return components[-1].lower()

    @property
    def defaults(self):
        return {
            'allow_community_edits': True
        }

    def set_values(self, video):
        pass

    def owner_username(self):
        return None
    
    @classmethod
    def format_url(cls, url):
        return url.strip()
    
class VideoTypeRegistrar(dict):
    
    domains = []
    
    def __init__(self, *args, **kwargs):
        super(VideoTypeRegistrar, self).__init__(*args, **kwargs)
        self.choices = []
        self.type_list = []
        
    def register(self, video_type):
        self[video_type.abbreviation] = video_type
        self.type_list.append(video_type)
        self.choices.append((video_type.abbreviation, video_type.name))
        domain = getattr(video_type, 'site', None)
        domain and self.domains.append(domain)
        
    def video_type_for_url(self, url):
        for video_type in self.type_list:
            if video_type.matches_video_url(url):
                return video_type(url)
            
class VideoTypeError(Exception):
    pass
