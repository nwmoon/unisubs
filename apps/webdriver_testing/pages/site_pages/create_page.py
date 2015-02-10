#!/usr/bin/env python

import time
from webdriver_testing.pages.site_pages import UnisubsPage


class CreatePage(UnisubsPage):
    """
     Video Page contains the common elements in the video page.
    """

    _SINGLE_URL_ENTRY_BOX = "input.main_video_form_field"
    _INPUT_PREFOCUS = "input#submit_video_field.prefocus"
    _URL = "videos/create/"
    _SUBMIT_BUTTON = "button.blue-green-button"
    _YOUTUBE_USER_FIELD = "li input#id_usernames"
    _YOUTUBE_PAGE_FIELD = "li input#id_youtube_user_url"
    _FEED_URL = "li input#id_feed_url"
    _SUBMIT_ERROR = "ul.errorlist li"

    def open_create_page(self):
        self.logger.info('Opening the create page: %s' %self._URL)
        self.open_page(self._URL)

    def submit_video(self, video_url):
        self.logger.info('Submitting the video: %s' %video_url)
        self.wait_for_element_present(self._INPUT_PREFOCUS)
        self.submit_form_text_by_css(self._SINGLE_URL_ENTRY_BOX, video_url)
        self.check_if_element_present('div#messages', wait_time=15)

    def _open_multi_submit(self):
        self.logger.info('Displaying the multi-submit form')
        self.click_by_css(self._MULTI_SUBMIT_LINK)
        self.page_down(self._HIDE_MULTI)
        self.wait_for_element_present(self._YOUTUBE_USER_FIELD)

    def submit_youtube_users_videos(self, youtube_usernames):
        """Submit 1 or several youtube user names.
        Type 1 or several youtube user names in hte Youtube usernames field.

        """
        self.logger.info('Submitting youtube users videos: '
                         '%s' %youtube_usernames)
        self._open_multi_submit()
        self.type_by_css(self._YOUTUBE_USER_FIELD, youtube_usernames)
        self.submit_by_css(self._SUBMIT_MULTI)

    def submit_youtube_user_page(self, youtube_user_url):
        """Submit videos from youtube user page url.

        """
        self._open_multi_submit()
        self.logger.info('Submitting youtube user page %s' %youtube_user_url)
        self.type_by_css(self._YOUTUBE_PAGE_FIELD, youtube_user_url)
        self.submit_by_css(self._SUBMIT_MULTI)

    def submit_feed_url(self, feed_url):
        """Submit videos from a supported feed type.

        """
        self._open_multi_submit()
        self.logger.info('Submitting the feed %s' % feed_url)
        self.type_by_css(self._FEED_URL, feed_url)
        self.submit_by_css(self._SUBMIT_MULTI)

    def multi_submit_successful(self):
        self.logger.info("Checking if multi submit successful")
        self.wait_for_element_present(self._SUCCESS_MESSAGE, wait_time=20)
        if self.is_text_present(self._SUCCESS_MESSAGE,
                                ("The videos are being added in the "
                                 "background. If you are logged in, you "
                                 "will receive a message when it's done")):
            return True
        else:
            self.logger.info(self.get_text_by_css(self._SUCCESS_MESSAGE))

    def multi_submit_failed(self):
        self.logger.info("Checking if multi submit failed")
        if self.is_element_present(self._ERROR_MESSAGE):
            return True

    def submit_success(self, expected_error=False):
        self.logger.info("Verifying video submit successful")
        error_present = self.is_element_visible(self._SUBMIT_ERROR)
        if expected_error == False and error_present:
            error_msg = self.get_text_by_css(self._SUBMIT_ERROR)
            raise ValueError("Submit failed: site says %s" % error_msg)
        elif expected_error == True and error_present:
            return error_msg
        else:
            return True
        #FIXME - you can do better verfication than this
