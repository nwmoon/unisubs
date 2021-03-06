# -*- coding: utf-8 -*-

from webdriver_testing.pages.site_pages.teams import add_feed_page
from webdriver_testing.pages.site_pages.teams import feeds_page
from webdriver_testing.webdriver_base import WebdriverTestCase
from webdriver_testing.data_factories import UserFactory
from webdriver_testing.data_factories import TeamMemberFactory
from videos.models import VideoFeed




class TestCaseAddFeeds(WebdriverTestCase):
    """ TestSuite for adding video feeds. """
    NEW_BROWSER_PER_TEST_CASE = False

    @classmethod
    def setUpClass(cls):
        super(TestCaseAddFeeds, cls).setUpClass()
        cls.user = UserFactory.create()
        cls.team = TeamMemberFactory.create(
            user = cls.user).team

        cls.feed_pg = add_feed_page.AddFeedPage(cls)
        cls.feed_pg.open_feed_page(cls.team.slug)
        cls.feed_pg.log_in(cls.user.username, 'password')
        cls.feeds_pg = feeds_page.FeedsPage(cls)

    def setUp(self):
        self.feed_pg.open_feed_page(self.team.slug)

    def test_duplicate_youtube_user(self):
        """Add a youtube user feed

        """
        youtube_user = 'latestvideoss'
        self.feed_pg.submit_youtube_users_videos(youtube_user)
        self.assertTrue(self.feed_pg.submit_successful())
        self.feed_pg.open_feed_page(self.team.slug)
        self.feed_pg.submit_youtube_users_videos(youtube_user)
        expected_error = ('Feed for https://gdata.youtube.com/feeds/api/users'
                          '/latestvideoss/uploads already exists')
        self.assertEqual(expected_error, self.feed_pg.submit_error())

    def test_vimeo(self):
        """Add a vimeo feed

        """
        url = "http://vimeo.com/amaravideos/videos/rss"
        self.feed_pg.submit_feed_url(url)
        self.assertTrue(self.feed_pg.submit_successful())
        feed = VideoFeed.objects.get(url=url)
        feed.update()
        self.feeds_pg.open_feed_details(self.team.slug, feed.id)
        self.assertEqual(1, self.feeds_pg.num_videos()) 

    def test_youtube_feed(self):
        """Add a youtube feed

        """
        url = "http://gdata.youtube.com/feeds/api/users/amaratestuser/uploads"
        self.feed_pg.submit_feed_url(url)
        self.assertTrue(self.feed_pg.submit_successful())

        feed = VideoFeed.objects.get(url=url)
        feed.update()
        self.feeds_pg.open_feed_details(self.team.slug, feed.id)
        self.assertEqual(3, self.feeds_pg.num_videos()) 


    def test_brightcove_feed(self):
        """Add a brightcove new videos feed

        """
        url = ("http://link.brightcove.com/services/mrss/"
              "player3091474522001/2903498771001/tags/tag%20with%20spaces")
        self.feed_pg.submit_feed_url(url)
        self.assertTrue(self.feed_pg.submit_successful())
        feed = VideoFeed.objects.get(url=url)
        feed.update()
        self.feeds_pg.open_feed_details(self.team.slug, feed.id)
        self.assertEqual(1, self.feeds_pg.num_videos()) 

    def test_kaltura_yahoo_feed(self):
        """Add a kaltura yahoo feed

        """
        url = "http://qa.pculture.org/feeds_test/kaltura_yahoo_feed.rss"
        self.feed_pg.submit_feed_url(url)
        self.assertTrue(self.feed_pg.submit_successful())
        feed = VideoFeed.objects.get(url=url)
        feed.update()
        self.feeds_pg.open_feed_details(self.team.slug, feed.id)
        self.assertEqual(3, self.feeds_pg.num_videos()) 

    def test_kaltura_itunes_feed(self):
        """Add a kaltura itunes feed

        """
        url = "http://qa.pculture.org/feeds_test/kaltura_itunes_feed.rss"
        self.feed_pg.submit_feed_url(url)
        self.assertTrue(self.feed_pg.submit_successful())
        feed = VideoFeed.objects.get(url=url)
        feed.update()
        self.feeds_pg.open_feed_details(self.team.slug, feed.id)
        self.assertEqual(3, self.feeds_pg.num_videos()) 
