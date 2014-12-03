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

import os
import logging
import time

from django.test import LiveServerTestCase
from django.test.testcases import (TestCase)
from selenium import webdriver
from django.conf import settings
from django.contrib.sites.models import Site
from django.core import management

from utils import test_utils

class WebdriverTestCase(LiveServerTestCase, TestCase):
    # Subclasses can set this to False to reuse the same browser from test-case
    # to test-case.
    NEW_BROWSER_PER_TEST_CASE = True

    # Selenium browser to use in the tests
    browser = None

    @classmethod
    def setUpClass(cls):
        super(WebdriverTestCase, cls).setUpClass()
        management.call_command('flush', interactive=False)
        site_obj = Site.objects.get_current()
        Site.objects.clear_cache()
        site_obj.domain = ('%s:%s' % (cls.server_thread.host,
                                      cls.server_thread.port))
        site_obj.save()
        cls.base_url = ('http://%s/' % site_obj.domain)
        cls.logger = logging.getLogger('test_steps')
        cls.logger.setLevel(logging.INFO)
        if not cls.NEW_BROWSER_PER_TEST_CASE:
            cls.create_browser(cls.__name__)

    @classmethod
    def tearDownClass(cls):
        cls.browser.execute_script("window.stop()")
        if not cls.NEW_BROWSER_PER_TEST_CASE:
            cls.destroy_browser()
        #destroy the selenium browser before teardown to avoid liveserver
        #shutdown errors.  See https://code.djangoproject.com/ticket/19051
        super(WebdriverTestCase, cls).tearDownClass()

    def setUp(self):
        super(WebdriverTestCase, self).setUp()
        #Set up logging to capture the test steps.
        self.logger.info('testcase: %s' % self.id())
        self.logger.info('description: %s' % self.shortDescription())
        
        #Match the Site port with the liveserver port so search redirects work.
        if self.NEW_BROWSER_PER_TEST_CASE:
            self.__class__.create_browser(self.shortDescription())
        
    def tearDown(self):
        self.browser.execute_script("window.stop()")
        if self.NEW_BROWSER_PER_TEST_CASE:
            self.__class__.destroy_browser()

    @classmethod
    def create_browser(cls, suite_or_test):
        test_utils.start_xvfb()
        #Otherwise just running locally - setup the browser to use.
        test_browser = os.environ.get('TEST_BROWSER', 'Firefox')
        cls.browser = getattr(webdriver, test_browser)()
                    
    @classmethod
    def destroy_browser(cls):
        if cls.browser is not None:
            cls.browser.quit()
            cls.browser = None
