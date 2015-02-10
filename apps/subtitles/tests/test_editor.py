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

import datetime
import json
from unittest2 import skip

from django.core.exceptions import ValidationError
from django.core.urlresolvers import  reverse
from django.test import TestCase

from auth.models import CustomUser
from subtitles.tests.utils import (
    make_video
)

class EditorViewTest(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.get_or_create(username='admin')[0]
        self.user.set_password('admin')
        self.user.save()

    def _login(self, user=None):
        user = user or self.user
        self.client.login(username=user.username, password='admin')

    def _get_boostrapped_data(self, response):
        '''
        Get the data that is passed to the angular app as a json object
        writen on a page <script> tag, as a python dict
        '''
        return json.loads(response.context['editor_data'])

    def test_login_required(self):
        video = make_video()
        url = reverse("subtitles:subtitle-editor", args=(video.video_id,'en'))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        # redirect from the login_required decorator does not include
        # the locale name, but the reverse we use does ;)
        login_url = "/".join(reverse("auth:login").split("/")[2:])
        self.assertIn(login_url, response['location'])
        self._login()
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)

    def test_valid_language_required(self):
        video = make_video()
        self._login()
        url = reverse("subtitles:subtitle-editor", args=(video.video_id,'xxxxx'))
        self.assertRaises(ValidationError, self.client.get, url)

    def test_apikey_present(self):
        video = make_video()
        self._login()
        url = reverse("subtitles:subtitle-editor", args=(video.video_id,'en'))
        response =  self.client.get(url)
        data = self._get_boostrapped_data(response)
        self.assertEqual(self.user.get_api_key(), data['authHeaders']['x-apikey'])
        self.assertEqual(self.user.username, data['authHeaders']['x-api-username'])


    def test_permission(self):
        # test public video is ok
        # test video on hidden team to non members is not ok
        # test video on public team with memebership requirements
        pass

    def test_writelock(self):
        # test two users can't access the same langauge at the same time
        # expire the first write lock
        # test second user can aquire it
        pass

    def test_translated_language_present(self):
        # make sure if the subtitle version to be edited
        # is a translation, that we bootstrap the data correctly on
        # the editor data
        pass

    def test_stand_alone_langauge_loads(self):
        # make sure the view doesn't blow up if there is
        # no translation to be showed
        pass
