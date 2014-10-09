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

import os

from django.conf import settings
from django.conf.urls.defaults import patterns, url
from django.conf.urls.static import static

from staticmedia import utils
import logging
logger= logging.getLogger("urls")
if settings.STATIC_MEDIA_USES_S3:
    # don't serve up the media from the local server if we're using S3
    urlpatterns = patterns('staticmedia.views')
else:
    # mimic the S3 directory structure using views from the local server
    urlpatterns = patterns(
        'staticmedia.views',
        url(r'^css/(?P<bundle_name>[\w\.-]+)$', 'css_bundle', name='css_bundle'),
        url(r'^js/(?P<bundle_name>[\w\.-]+)$', 'js_bundle', name='js_bundle'),
        # embed.js is a weird file, but we want to continue support for a
        # while
        url(r'^embed.js$', 'old_embedder_js', name='old_embedder_js'),
    ) + static(
        '/images/', document_root=os.path.join(settings.STATIC_ROOT, 'images')
    ) + static(
        '/flowplayer/', document_root=os.path.join(settings.STATIC_ROOT, 'flowplayer')
    ) + static(
        '/fonts/', document_root=os.path.join(settings.STATIC_ROOT, 'fonts')
    )
    for static_dir in utils.app_static_media_dirs():
        urlpatterns += static('/' + static_dir["label"], document_root=static_dir["path"])
if settings.DEBUG:
    urlpatterns += patterns(
        'staticmedia.views',
        url(r'^test/old-embedder/$', 'old_embedder_test',
            name='old_embedder_test'),
        url(r'^test/embedder/$', 'embedder_test', name='embedder_test'),
    )
