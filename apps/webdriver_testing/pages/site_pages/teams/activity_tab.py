#!/usr/bin/env python
from webdriver_testing.pages.site_pages.teams import ATeamPage
import time

class ActivityTab(ATeamPage):
    """Actions for the Videos tab of a Team Page.

    """
    _URL = 'teams/%s/activity/'
    _TEAM_ACTIVITY_URL = 'teams/%s/activity/team/'

    #FILTER and SORT
    #_LANG_FILTER = 'div.filters div.filter-chunk div'
    _ACTIVITY_FILTER = 'select#id_activity_type'
    _SUBTITLE_LANG_FILTER = 'select#id_subtitles_language'
    _SORT_FILTER = 'select#sort'
    _PRIMARY_AUDIO_FILTER = 'select#video_language'
    _UPDATE_FILTER = 'button#update'
    _ACTIVITY = 'ul.activity li'

    def open_activity_tab(self, team):
        """Open the team with the provided team slug.

        """
        self.open_page(self._URL % team)
    def open_team_activity_tab(self, team):
        """Open the team with the provided team slug.

        """
        self.open_page(self._TEAM_ACTIVITY_URL % team)

    def _open_filters(self):
        if self.is_element_visible(self._FILTER_OPEN):
            self.logger.info('filter is open')
        else:
            self.logger.info('Opening the filter options')
            self.click_by_css(self._FILTERS)
            self.wait_for_element_present(self._FILTER_OPEN)
            self.wait_for_element_visible('div.filter-chunk')

    def clear_filters(self):
        self.logger.info('Clearing out current filters')
        self.click_by_css(self._CLEAR_FILTERS)


    def update_filters(self):
        self.click_by_css(self._UPDATE_FILTER) 
 

    def activity_type_filter(self, setting):
        """Filter the displayed videos by primary audio set 

        This is only for bulk move videos page.
        """
        self.click_by_css("div#id_activity_type_chzn")
        self.select_from_chosen(self._ACTIVITY_FILTER, setting)

    def primary_audio_filter(self, setting):
        """Filter the displayed videos by primary audio set 

        This is only for bulk move videos page.
        """
        self.click_by_css('div#video_language_chzn')
        self.select_from_chosen(self._PRIMARY_AUDIO_FILTER, setting)


    def sub_lang_filter(self, language, has=True):
        """Filter the displayed videos by subtitle language'

        Valid choices are the full language name spelled out.
        ex: English, or Serbian, Latin
        """
        self.logger.info('Filtering videos by language %s ' % language)
        self._open_filters()
        self.click_by_css('div#lang_chzn a.chzn-single')
        self.select_from_chosen(self._LANG_FILTER, language)
        if not has:
            self.click_by_css('div#lang_mode_chzn a.chzn-single')
            self.select_from_chosen(self._LANG_MODE_FILTER, "doesn't have" )

            

    def video_sort(self, sort_option):
        """Sort videos via the pulldown.

        Valid options are:  name, a-z
                            name, z-a
                            time, newest
                            time, oldest
                            most subtitles
                            least subtitles

        """
        self.logger.info('Sorting videos by %s' %sort_option)
        self._open_filters() 
        filter_chunks = self.browser.find_elements_by_css_selector('div.filter-chunk')
        span_chunk = filter_chunks[-1].find_element_by_css_selector('div a.chzn-single span')
        span_chunk.click()
        self.select_from_chosen(self._SORT_FILTER, sort_option)
       

    def activity_list(self):
        els = self.get_elements_list(self._ACTIVITY)
        return [el.text for el in els]

