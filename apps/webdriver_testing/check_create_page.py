# -*- coding: utf-8 -*-

from utils.factories import *
from webdriver_testing.pages.site_pages import create_page
from webdriver_testing.pages.site_pages import watch_page
from webdriver_testing.webdriver_base import WebdriverTestCase
from webdriver_testing.pages.site_pages import video_page
from videos.models import VideoUrl
from videos.models import VideoFeed
from django.core import management


class TestCaseCreateVideos(WebdriverTestCase):
    """ TestSuite for video submission tests. """
    NEW_BROWSER_PER_TEST_CASE = False

    @classmethod
    def setUpClass(cls):
        super(TestCaseCreateVideos, cls).setUpClass()
        cls.create_pg = create_page.CreatePage(cls)
        cls.video_pg = video_page.VideoPage(cls)
        cls.create_pg.open_create_page()
        user = UserFactory()
        cls.create_pg.log_in(user.username, 'password')    

    def setUp(self):
        self.create_pg.open_create_page()

    def test_create_youtube(self):
        """Add a youtube video.

        """
        url = 'http://www.youtube.com/watch?v=WqJineyEszo'
        self.create_pg.submit_video(url)
        self.assertTrue(self.create_pg.submit_success())
        self.assertTrue(self.video_pg.displays_add_subtitles())

    def test_create_link_brightcove(self):
        """Add a brightcove video that resolves to link.bright...

        """
        url = 'http://bcove.me/8yxc6sxy'
        self.create_pg.submit_video(url)
        self.assertTrue(self.create_pg.submit_success())
        self.assertTrue(self.video_pg.displays_add_subtitles())


    def test_create_bcove_me(self):
        """Add a brightcove that resolves to bcove.me/...

        """
        url = 'http://bcove.me/1ub2ar8x'
        self.create_pg.submit_video(url)
        self.assertTrue(self.create_pg.submit_success())
        self.assertTrue(self.video_pg.displays_add_subtitles())



    def test_create_dailymotion(self):
        """Add a dailymotion video.

        """

        url = ('http://www.dailymotion.com/video/'
               'xlh9h1_fim-syndicat-des-apiculteurs-de-metz-environs_news')
        self.create_pg.submit_video(url)
        self.assertTrue(self.create_pg.submit_success())
        self.assertTrue(self.video_pg.displays_add_subtitles())

    def test_create_vimeo(self):
        """Add a vimeo video.

        """

        url = "http://vimeo.com/26487510"
        self.create_pg.submit_video(url)
        self.assertTrue(self.create_pg.submit_success())
        self.assertTrue(self.video_pg.displays_add_subtitles())

    def test_create_ogg(self):
        """Add an ogg video video.

        """

        url = "http://qa.pculture.org/amara_tests/Birds_short.oggtheora.ogg"
        self.create_pg.submit_video(url)
        self.assertTrue(self.create_pg.submit_success())
        self.assertTrue(self.video_pg.displays_add_subtitles())

    def test_create_mp4(self):
        """Add a an mp4 video.

        """

        url = "http://qa.pculture.org/amara_tests/Birds_short.mp4"
        self.create_pg.submit_video(url)
        self.assertTrue(self.create_pg.submit_success())
        self.assertTrue(self.video_pg.displays_add_subtitles())

    def test_create_with_params(self):

        """Add a an mp4 with params in the url.

        """

        url = ("http://s3.us.archive.org/nextdayvideo/enthought/scipy_2012/"
              "Parallel_High_Performance_Statistical_Bootstrapping_in_Python.mp4"
              "?Signature=Ku0vNWttnyZ4leEpRdGzq59nz0I%3D&Expires=1346740237"
              "&AWSAccessKeyId=FEWGReWX3QbNk0h3")
        self.create_pg.submit_video(url)
        self.assertTrue(self.create_pg.submit_success())
        self.assertTrue(self.video_pg.displays_add_subtitles())

    def test_create_webm(self):
        """Add a webM video.

        """

        url = "http://qa.pculture.org/amara_tests/Birds_short.webmsd.webm"
        self.create_pg.submit_video(url)
        self.assertTrue(self.create_pg.submit_success())
        self.assertTrue(self.video_pg.displays_add_subtitles())

    def test_create_youtu_be_url(self):
        """Add a youtube video with youtu.be url.

        """

        url = "http://youtu.be/q26umaF242I"
        self.create_pg.submit_video(url)
        self.assertTrue(self.create_pg.submit_success())
        self.assertTrue(self.video_pg.displays_add_subtitles())
