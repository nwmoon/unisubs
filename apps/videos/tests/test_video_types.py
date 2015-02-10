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

import datetime

from django.test import TestCase

from babelsubs.storage import SubtitleLine, SubtitleSet

from auth.models import CustomUser as User
from teams.models import Team, TeamVideo
from subtitles import pipeline
from subtitles.models import SubtitleLanguage, SubtitleVersion
from videos.models import Video, VIDEO_TYPE_BRIGHTCOVE
from videos.types import video_type_registrar, VideoTypeError
from videos.types.base import VideoType, VideoTypeRegistrar
from videos.types.bliptv import BlipTvVideoType
from videos.types.brightcove  import BrightcoveVideoType
from videos.types.dailymotion import DailymotionVideoType
from videos.types.flv import FLVVideoType
from videos.types.htmlfive import HtmlFiveVideoType
from videos.types.kaltura import KalturaVideoType
from videos.types.mp3 import Mp3VideoType
from videos.types.vimeo import VimeoVideoType
from videos.types.youtube import YoutubeVideoType
from utils import test_utils
from utils import youtube

class YoutubeVideoTypeTest(TestCase):
    def setUp(self):
        self.vt = YoutubeVideoType
        self.data = [{
            'url': 'http://www.youtube.com/watch#!v=UOtJUmiUZ08&feature=featured&videos=Qf8YDn9mbGs',
            'video_id': 'UOtJUmiUZ08'
        },{
            'url': 'http://www.youtube.com/v/6Z5msRdai-Q',
            'video_id': '6Z5msRdai-Q'
        },{
            'url': 'http://www.youtube.com/watch?v=woobL2yAxD4',
            'video_id': 'woobL2yAxD4'
        },{
            'url': 'http://www.youtube.com/watch?v=woobL2yAxD4&amp;playnext=1&amp;videos=9ikUhlPnCT0&amp;feature=featured',
            'video_id': 'woobL2yAxD4'
        }]
        self.shorter_url = "http://youtu.be/HaAVZ2yXDBo"

    @test_utils.patch_for_test('utils.youtube.get_video_info')
    def test_set_values(self, mock_get_video_info):
        video_info = youtube.VideoInfo('test-channel-id', 'title',
                                       'description', 100,
                                       'http://example.com/thumb.png')
        mock_get_video_info.return_value = video_info

        video, created = Video.get_or_create_for_url(
            'http://www.youtube.com/watch?v=_ShmidkrcY0')
        vu = video.videourl_set.all()[:1].get()

        self.assertEqual(vu.videoid, '_ShmidkrcY0')
        self.assertEqual(video.title, video_info.title)
        self.assertEqual(video.description, video_info.description)
        self.assertEqual(video.duration, video_info.duration)
        self.assertEqual(video.thumbnail, video_info.thumbnail_url)

    @test_utils.patch_for_test('utils.youtube.get_video_info')
    def test_get_video_info_exception(self, mock_get_video_info):
        video_info = youtube.VideoInfo('test-channel-id', 'title',
                                       'description', 100,
                                       'http://example.com/thumb.png')
        mock_get_video_info.side_effect = youtube.APIError()

        video, created = Video.get_or_create_for_url(
            'http://www.youtube.com/watch?v=_ShmidkrcY0')
        vu = video.videourl_set.all()[:1].get()

        self.assertEqual(vu.videoid, '_ShmidkrcY0')
        self.assertEqual(video.description, '')
        self.assertEqual(video.duration, None)
        self.assertEqual(video.thumbnail, '')
        # since get_video_info failed, we don't know the channel id of our
        # video URL.  We should use a dummy value to make it easier to fix the
        # issue in the future
        self.assertEqual(vu.owner_username, None)

    def test_matches_video_url(self):
        for item in self.data:
            self.assertTrue(self.vt.matches_video_url(item['url']))
            self.assertFalse(self.vt.matches_video_url('http://some-other-url.com'))
            self.assertFalse(self.vt.matches_video_url(''))
            self.assertFalse(self.vt.matches_video_url('http://youtube.com/'))
            self.assertFalse(self.vt.matches_video_url('http://youtube.com/some-video/'))
            self.assertTrue(self.vt.matches_video_url(self.shorter_url))

    def test_get_video_id(self):
        for item in self.data:
            self.failUnlessEqual(item['video_id'], self.vt._get_video_id(item['url']))

    def test_shorter_format(self):
        vt = self.vt(self.shorter_url)
        self.assertTrue(vt)
        self.assertEqual(vt.video_id , self.shorter_url.split("/")[-1])

class HtmlFiveVideoTypeTest(TestCase):
    def setUp(self):
        self.vt = HtmlFiveVideoType

    def test_type(self):
        self.assertTrue(self.vt.matches_video_url(
            'http://someurl.com/video.ogv'))
        self.assertTrue(self.vt.matches_video_url(
            'http://someurl.com/video.OGV'))
        self.assertTrue(self.vt.matches_video_url('http://someurl.com/video.ogg'))
        self.assertTrue(self.vt.matches_video_url('http://someurl.com/video.mp4'))
        self.assertTrue(self.vt.matches_video_url('http://someurl.com/video.m4v'))
        self.assertTrue(self.vt.matches_video_url('http://someurl.com/video.webm'))

        self.assertFalse(self.vt.matches_video_url('http://someurl.ogv'))
        self.assertFalse(self.vt.matches_video_url('http://someurl.com/ogv'))
        self.assertFalse(self.vt.matches_video_url(''))
        #for this is other type
        self.assertFalse(self.vt.matches_video_url('http://someurl.com/video.flv'))
        self.assertFalse(self.vt.matches_video_url('http://someurl.com/ogv.video'))

class Mp3VideoTypeTest(TestCase):
    def setUp(self):
        self.vt = Mp3VideoType

    def test_type(self):
        self.assertTrue(self.vt.matches_video_url(
            'http://someurl.com/audio.mp3'))
        self.assertTrue(self.vt.matches_video_url(
            'http://someurl.com/audio.MP3'))
        self.assertFalse(self.vt.matches_video_url(
            'http://someurl.com/mp3.audio'))

class BlipTvVideoTypeTest(TestCase):
    def setUp(self):
        self.vt = BlipTvVideoType

    def test_type(self):
        url = 'http://blip.tv/day9tv/day-9-daily-438-p3-build-orders-made-easy-newbie-tuesday-6066868'
        video, created = Video.get_or_create_for_url(url)
        vu = video.videourl_set.all()[:1].get()

        # this is the id used to embed videos
        self.assertEqual(vu.videoid, 'hdljgvKmGAI')
        self.assertTrue(video.title)
        self.assertTrue(video.thumbnail)
        self.assertTrue(vu.url)

        self.assertTrue(self.vt.matches_video_url(url))
        self.assertTrue(self.vt.matches_video_url('http://blip.tv/day9tv/day-9-daily-438-p3-build-orders-made-easy-newbie-tuesday-6066868'))
        self.assertFalse(self.vt.matches_video_url('http://blip.tv'))
        self.assertFalse(self.vt.matches_video_url(''))

    def test_video_title(self):
        url = 'http://blip.tv/day9tv/day-9-daily-100-my-life-of-starcraft-3505715'
        video, created = Video.get_or_create_for_url(url)
        #really this should be jsut not failed
        self.assertTrue(video.get_absolute_url())

    def test_creating(self):
        # this test is for ticket: https://www.pivotaltracker.com/story/show/12996607
        url = 'http://blip.tv/day9tv/day-9-daily-1-flash-vs-hero-3515432'
        video, created = Video.get_or_create_for_url(url)

class DailymotionVideoTypeTest(TestCase):
    def setUp(self):
        self.vt = DailymotionVideoType

    def test_type(self):
        url = 'http://www.dailymotion.com/video/x7u2ww_juliette-drums_lifestyle#hp-b-l'

        video, created = Video.get_or_create_for_url(url)
        vu = video.videourl_set.all()[:1].get()

        self.assertEqual(vu.videoid, 'x7u2ww')
        self.assertTrue(video.title)
        self.assertTrue(video.thumbnail)
        self.assertEqual(vu.url, 'http://dailymotion.com/video/x7u2ww')

        self.assertTrue(self.vt.matches_video_url(url))
        self.assertFalse(self.vt.matches_video_url(''))
        self.assertFalse(self.vt.matches_video_url('http://www.dailymotion.com'))

    def test_type1(self):
        url = u'http://www.dailymotion.com/video/edit/xjhzgb_projet-de-maison-des-services-a-fauquembergues_news'
        vt = self.vt(url)
        try:
            vt.get_metadata(vt.videoid)
            self.fail('This link should return wrong response')
        except VideoTypeError:
            pass

class FLVVideoTypeTest(TestCase):
    def setUp(self):
        self.vt = FLVVideoType

    def test_type(self):

        self.assertTrue(self.vt.matches_video_url(
            'http://someurl.com/video.flv'))
        self.assertFalse(self.vt.matches_video_url(
            'http://someurl.flv'))
        self.assertFalse(self.vt.matches_video_url(
            ''))
        self.assertFalse(self.vt.matches_video_url(
            'http://someurl.com/flv.video'))

    def test_blip_type(self):
        url = 'http://blip.tv/file/get/Coldguy-SpineBreakersLiveAWizardOfEarthsea210.FLV'
        video, created = Video.get_or_create_for_url(url)
        video_url = video.videourl_set.all()[0]
        self.assertEqual(self.vt.abbreviation, video_url.type)

class VimeoVideoTypeTest(TestCase):
    def setUp(self):
        self.vt = VimeoVideoType

    def test_type(self):
        url = 'http://vimeo.com/15786066?some_param=111'

        video, created = Video.get_or_create_for_url(url)
        vu = video.videourl_set.all()[:1].get()

        self.assertEqual(vu.videoid, '15786066')

        self.assertTrue(self.vt.matches_video_url(url))

        self.assertFalse(self.vt.matches_video_url('http://vimeo.com'))
        self.assertFalse(self.vt.matches_video_url(''))

    def test1(self):
        #For this video Vimeo API returns response with strance error
        #But we can get data from this response. See vidscraper.sites.vimeo.get_shortmem
        #So if this test is failed - maybe API was just fixed and other response is returned
        # FIXME: restablish when vimeo api is back!
        return
        url = u'http://vimeo.com/22070806'
        video, created = Video.get_or_create_for_url(url)

        self.assertNotEqual(video.title, '')
        self.assertNotEqual(video.description, '')
        vu = video.videourl_set.all()[:1].get()

        self.assertEqual(vu.videoid, '22070806')

class VideoTypeRegistrarTest(TestCase):
    def test_base(self):
        registrar = VideoTypeRegistrar()

        class MockupVideoType(VideoType):
            abbreviation = 'mockup'
            name = 'MockUp'

        registrar.register(MockupVideoType)
        self.assertEqual(registrar[MockupVideoType.abbreviation], MockupVideoType)
        self.assertEqual(registrar.choices[-1], (MockupVideoType.abbreviation, MockupVideoType.name))

    def test_video_type_for_url(self):
        type = video_type_registrar.video_type_for_url('some url')
        self.assertEqual(type, None)
        type = video_type_registrar.video_type_for_url('http://youtube.com/v=UOtJUmiUZ08')
        self.assertTrue(isinstance(type, YoutubeVideoType))
        return
        self.assertRaises(VideoTypeError, video_type_registrar.video_type_for_url,
                          'http://youtube.com/v=100500')

class BrightcoveVideoTypeTest(TestCase):
    player_id = '1234'
    video_id = '5678'

    @test_utils.patch_for_test('videos.types.brightcove.BrightcoveVideoType._resolve_url_redirects')
    def setUp(self, resolve_url_redirects):
        TestCase.setUp(self)
        self.resolve_url_redirects = resolve_url_redirects
        resolve_url_redirects.side_effect = lambda url: url

    def check_url(self):
            self.assertEquals(vu.type, 'R')
            self.assertEquals(vu.brightcove_id(), self.video_id)

    def test_type(self):
        self.assertEqual(BrightcoveVideoType.abbreviation,
                         VIDEO_TYPE_BRIGHTCOVE)

    def make_url(self, url):
        return url.format(video_id=self.video_id, player_id=self.player_id)

    def check_url(self, url):
        self.assertTrue(BrightcoveVideoType.matches_video_url(url))
        vt = BrightcoveVideoType(url)
        self.assertEquals(vt.video_id, self.video_id)

    def test_urls(self):
        # test URLs with the video_id in the path
        self.check_url(self.make_url(
            'http://link.brightcove.com'
            '/services/link/bcpid{player_id}/bctid{video_id}'))
        self.check_url(self.make_url(
            'http://bcove.me'
            '/services/link/bcpid{player_id}/bctid{video_id}'))
        # test URLs with the video_id in the query
        self.check_url(self.make_url(
            'http://link.brightcove.com'
            '/services/link/bcpid{player_id}'
            '?bckey=foo&bctid={video_id}'))

    def test_redirection(self):
        # test URLs in bcove.me that redirect to another brightcove URL
        self.resolve_url_redirects.side_effect = lambda url: self.make_url(
            'http://link.brightcove.com/'
            'services/link/bcpid{player_id}/bctid{video_id}')
        self.check_url('http://bcove.me/shortpath')

class KalturaVideoTypeTest(TestCase):
    def test_type(self):
        url = 'http://cdnbakmi.kaltura.com/p/1492321/sp/149232100/serveFlavor/entryId/1_zr7niumr/flavorId/1_djpnqf7y/name/a.mp4'

        video, created = Video.get_or_create_for_url(url)
        vu = video.videourl_set.get()
        self.assertEquals(vu.type, 'K')
        self.assertEquals(vu.kaltura_id(), '1_zr7niumr')

