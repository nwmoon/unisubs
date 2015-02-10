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

from django.test import TestCase

from auth.models import CustomUser as User
from utils.factories import *
from utils.rpc import Error
from videos.rpc import VideosApiClass
from videos.models import Video, Action

class RpcTest(TestCase):
    def setUp(self):
        self.rpc = VideosApiClass()
        self.user = UserFactory(is_superuser=True)
        self.video = VideoFactory()

    def test_change_title_video(self):
        title = u'New title'
        rv = self.rpc.change_title_video(self.video.pk, title, self.user)
        if isinstance(rv, Error):
            raise AssertionError('RPC error: %s' % rv)

        video = Video.objects.get(pk=self.video.pk)
        self.assertEqual(video.title, title)
        try:
            Action.objects.get(video=self.video, new_video_title=title,
                               action_type=Action.CHANGE_TITLE)
        except Action.DoesNotExist:
            self.fail()

