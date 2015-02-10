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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see
# http://www.gnu.org/licenses/agpl-3.0.html.
from datetime import datetime, timedelta
from urlparse import urlparse

from django.core.urlresolvers import reverse
from django.core import mail
from django.test import TestCase
from auth.models import CustomUser as User, UserLanguage
from auth.models import LoginToken
from caching.tests.utils import assert_invalidates_model_cache
from utils.factories import *

class VideosFieldTest(TestCase):
    def setUp(self):
        self.user = UserFactory()

    def check_user_videos(self, videos):
        self.assertEqual(set(self.user.videos.all()), set(videos))

    def test_with_video_followers(self):
        video = VideoFactory(title='video1')
        video2 = VideoFactory(title='video2')
        self.check_user_videos([])
        # add
        video.followers.add(self.user)
        self.check_user_videos([video])
        # add with reverse relation
        self.user.followed_videos.add(video2)
        self.check_user_videos([video, video2])
        # remove
        video.followers.remove(self.user)
        self.check_user_videos([video2])
        # remove with reverse relation
        self.user.followed_videos.remove(video2)
        self.check_user_videos([])
        # clear
        video.followers.add(self.user)
        self.check_user_videos([video])
        video.followers = []
        self.check_user_videos([])
        # clear with reverse relation
        video.followers.add(self.user)
        self.check_user_videos([video])
        self.user.followed_videos = []
        self.check_user_videos([])

class UserCreationTest(TestCase):
    def test_notfications(self):
        self.assertEqual(len(mail.outbox), 0)
        user = User(email='la@example.com', username='someone')
        user.set_password("secret")
        user.save()
        self.assertEqual(len(mail.outbox), 1)

    def test_notifications_unicode(self):
        self.assertEqual(len(mail.outbox), 0)
        user = User(email=u'Leandro Andrés@example.com', username='unicodesomeone')
        user.set_password("secret")
        user.save()
        self.assertEqual(len(mail.outbox), 1)

class UserCacheTest(TestCase):
    def test_user_language_change_invalidates_cache(self):
        user = UserFactory()
        with assert_invalidates_model_cache(user):
            user_lang = UserLanguage.objects.create(user=user, language='en')
        with assert_invalidates_model_cache(user):
            user_lang.delete()

class LoginTokenModelTest(TestCase):
    def test_creation(self):
        user = UserFactory()
        lt1 = LoginToken.objects.for_user(user)
        lt2 = LoginToken.objects.for_user(user, updates=False)
        self.assertEqual(lt1.token, lt2.token)
        self.assertEqual(len(lt1.token), 40)
        # assesrt updates does what it says
        lt3 = LoginToken.objects.for_user(user, updates=True)
        self.assertNotEqual(lt3.token, lt2.token)
        self.assertEqual(len(lt3.token), 40)

    def test_expire(self):
        user = UserFactory()

        lt1 = LoginToken.objects.for_user(user)
        self.assertFalse(lt1.is_expired)
        self.assertFalse(LoginToken.objects.get_expired().filter(pk=lt1.pk).exists())
        older_date = datetime.now() - timedelta(minutes=1) - LoginToken.EXPIRES_IN
        lt1.created = older_date
        lt1.save()
        self.assertTrue(lt1.is_expired)
        self.assertTrue(LoginToken.objects.get_expired().filter(pk=lt1.pk).exists())


class LoginTokenViewsTest(TestCase):
    def test_valid_login(self):
        user = UserFactory()
        lt1 = LoginToken.objects.for_user(user)
        redirect_url = '/en/videos/watch'
        url = reverse("auth:token-login", args=(lt1.token,)) + "?next=%s" % redirect_url
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        location = response._headers['location'][1]
        redirect_path = urlparse(location).path
        self.assertEqual(redirect_path, redirect_url)

    def test_invalid_login(self):
        user = UserFactory()
        lt1 = LoginToken.objects.for_user(user)
        redirect_url = '/en/videos/watch'
        url = reverse("auth:token-login", args=(lt1.token,)) + "?next=%s" % redirect_url
        lt1.delete()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_staff_is_offlimit(self):
        user = UserFactory()
        lt1 = LoginToken.objects.for_user(user)
        user.is_staff  = True
        user.save()
        redirect_url = '/en/videos/watch'
        url = reverse("auth:token-login", args=(lt1.token,)) + "?next=%s" % redirect_url
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_superuser_is_offlimit(self):
        user = UserFactory()
        lt1 = LoginToken.objects.for_user(user)
        user.is_superuser  = True
        user.save()
        redirect_url = '/en/videos/watch'
        url = reverse("auth:token-login", args=(lt1.token,)) + "?next=%s" % redirect_url
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

