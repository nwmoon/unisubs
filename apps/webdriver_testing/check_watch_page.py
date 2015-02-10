#!/usr/bin/python
# -*- coding: utf-8 -*-

from utils.factories import *
from webdriver_testing.webdriver_base import WebdriverTestCase
from webdriver_testing.pages.site_pages import watch_page
from webdriver_testing.pages.site_pages import video_page
from webdriver_testing.pages.site_pages import search_results_page
from webdriver_testing.data_factories import UserLangFactory
from webdriver_testing import data_helpers
from django.core import management
import datetime
import time
import os

class TestCaseWatchPageSearch(WebdriverTestCase):
    """TestSuite for site video searches.  """
    NEW_BROWSER_PER_TEST_CASE = False

    @classmethod
    def setUpClass(cls):
        super(TestCaseWatchPageSearch, cls).setUpClass()
        management.call_command('update_index', interactive=False)
        cls.watch_pg = watch_page.WatchPage(cls)
        cls.data = data_helpers.DataHelpers()
        video = YouTubeVideoFactory(video_url = 'http://www.youtube.com/watch?v=WqJineyEszo',
                                    title = ('X Factor Audition - Stop Looking At My '
                                    'Mom Rap - Brian Bradley'),
                                     primary_audio_language_code = 'en'
                                    )
        data = {
                'language_code': 'en',
                'subtitles': ('apps/webdriver_testing/subtitle_data/'
                              'Timed_text.en.srt'),
                'complete': True,
                'video': video
               }
        cls.data.add_subs(**data)
        cls.user = UserFactory()        
        cls.data.create_videos_with_subs()
        VideoFactory.create(title = u'不过这四个问题')
        video = VideoFactory.create(title = "my test vid")
        data = {
                'language_code': 'zh-cn',
                'subtitles': ('apps/webdriver_testing/subtitle_data/'
                              'Timed_text.zh-cn.sbv'),
                'complete': True
               }
        test_video = cls.data.create_video_with_subs(cls.user, **data)
        management.call_command('update_index', interactive=False)



    def setUp(self):
        super(TestCaseWatchPageSearch, self).setUp()
        self.watch_pg.open_watch_page()
        
    def test_search__simple(self):
        """Search for text contained in video title.

        """
        test_text = 'X factor'
        results_pg = self.watch_pg.basic_search(test_text)
        self.assertTrue(results_pg.search_has_results())

    def test_search_subs_nonascii(self):
        """Search for sub content with non-ascii char strings.
 
        """
        test_text = u'不过这四个问题'
        results_pg = self.watch_pg.basic_search(test_text)
        self.assertTrue(results_pg.search_has_results())

    def test_search__title_nonascii(self):
        """Search title content with non-ascii char strings.
 
        """
        
        #Search for: chinese chars by opening entering the text 
        #via javascript because webdriver can't type those characters.
        self.browser.execute_script("document.getElementsByName"
                               "('q')[1].value='不过这四个问题'")
        results_pg = self.watch_pg.advanced_search()
        self.assertTrue(results_pg.search_has_results())
       

    def test_search_sub_content(self):
        """Search contents in subtitle text.

        """
        test_text = '[Zeus]'
        results_pg = self.watch_pg.basic_search(test_text)
        self.assertTrue(results_pg.search_has_results())

    def test_search_video_lang(self):
        """Search for videos by video language.
 
        """
        results_pg = self.watch_pg.advanced_search(orig_lang='en')
        self.assertTrue(results_pg.page_has_video(
            'original english with incomplete pt'))
        self.assertEqual(2, len(results_pg.page_videos()))

    def test_search__trans_lang(self):
        """Search for videos by translations language.
 
        """
        results_pg = self.watch_pg.advanced_search(trans_lang='pt')
        self.assertTrue(results_pg.page_has_video(
            'original english with incomplete pt'))
        self.assertEqual(1, len(results_pg.page_videos()))

    def test_search__trans_and_video_lang(self):
        """Search for videos by video lang and translations language.
 
        """
        results_pg = self.watch_pg.advanced_search(orig_lang = 'en', 
            trans_lang='pt')
        self.assertTrue(results_pg.page_has_video(
            'original english with incomplete pt'))
        self.assertEqual(1, len(results_pg.page_videos()))

    def test_search__text_trans_video(self):
        """Search for videos by text, video lang and translation.
 
        """
        self.browser.execute_script("document.getElementsByName('q')[1].value='subs'")
        results_pg = self.watch_pg.advanced_search(
            orig_lang = 'ar', 
            trans_lang='en')
        self.assertTrue(results_pg.page_has_video(
            'original ar with en complete subs'))
        self.assertEqual(1, len(results_pg.page_videos()))

    def test_result__language_menu(self):
        user = UserFactory()
        user_speaks = ['en', 'pt', 'ru', 'ar']
        for lang in user_speaks:
            UserLangFactory(user = user,
                            language = lang)
        self.watch_pg.log_in(user.username, 'password')
        test_text = 'english'
        title = 'original english with incomplete'
        results_pg = self.watch_pg.basic_search(test_text)
        expected_langs = ['English', 'Portuguese']
        if results_pg.search_has_results():
            self.assertEqual(expected_langs, results_pg.pulldown_languages(title))
        else: 
            self.fail('Video search returned no results') 


class TestCaseWatchPageListings(WebdriverTestCase):
    """TestSuite for watch page latest videos section.  """
    NEW_BROWSER_PER_TEST_CASE = False

    @classmethod
    def setUpClass(cls):
        super(TestCaseWatchPageListings, cls).setUpClass()
        management.call_command('clear_index', interactive=False)

        cls.watch_pg = watch_page.WatchPage(cls)
        cls.data = data_helpers.DataHelpers()
        cls.user = UserFactory()
        cls.video = cls.data.create_videos_with_subs()

        #create a video and mark as featured.
        cls.feature_vid = cls.data.create_video_with_subs(cls.user)
        cls.feature_vid.featured=datetime.datetime.now()
        cls.feature_vid.save()
       
        #update solr index
        management.call_command('update_index', interactive=False)

    def setUp(self):
        super(TestCaseWatchPageListings, self).setUp()
        #Open the watch page as a test starting point.
        self.watch_pg.open_watch_page()

    def test_latest_section(self):
        """Latest section displays the expected videos.

        """
        video_list = self.watch_pg.section_videos(section='latest')
        self.assertIn(cls.video.title, video_list)


    def test_latest_page(self):
        """Latest page opens when 'More' clicked and displays videos.

        """
        self.watch_pg.display_more(section='latest')
        self.watch_pg.search_complete()
        video_list = self.watch_pg.section_videos(section='featured')
        self.assertIn(cls.video.title, video_list)

    def test_featured_section(self):
        """Featured section only displays featured videos.

        """
        video_list = self.watch_pg.section_videos(section='featured')
        self.assertEqual([self.feature_vid.title], video_list)

    def test_featured_page(self):
        """Featured page opens when 'More' clicked and displays videos.

        """
        self.watch_pg.display_more(section='featured')
        video_list = self.watch_pg.section_videos(section='featured')
        self.assertEqual([self.feature_vid.title], video_list)
