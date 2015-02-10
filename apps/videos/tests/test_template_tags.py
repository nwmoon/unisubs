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

from django.contrib.sites.models import Site
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase

from videos.models import Video
from videos.templatetags.subtitles_tags import language_url
from videos.templatetags.videos_tags import shortlink_for_video
from videos.tests.data import get_video, make_subtitle_language



class TestTemplateTags(TestCase):
    def test_language_url_for_empty_lang(self):
        v = get_video(1)
        sl = make_subtitle_language(v, 'en')
        self.assertIsNotNone(language_url(None, sl))

class ShortUrlTest(TestCase):
    def setUp(self):
        self.video = Video.get_or_create_for_url("http://example.com/hey.mp4")[0]
        site = Site.objects.get_current()
        site.domain = "www.amara.org"
        site.save()
        # on production our domain might have www,
        # make sure we have such domain and that
        # www is not present
        self.short_url = shortlink_for_video(self.video)
        Site.objects.clear_cache()

    def tearDown(self):
        Site.objects.clear_cache()

    def test_short_url(self):
        response = self.client.get(self.short_url, follow=True)
        location = response.redirect_chain[-1][0]
        self.assertTrue(location.endswith(self.video.get_absolute_url()))

    def test_short_url_no_locale(self):
        self.assertFalse('/en/' in self.short_url)

    def test_short_url_no_www(self):
        self.assertTrue(self.short_url.startswith('%s://amara.org' % settings.DEFAULT_PROTOCOL))
