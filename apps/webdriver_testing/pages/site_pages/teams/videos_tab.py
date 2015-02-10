#!/usr/bin/env python
from webdriver_testing.pages.site_pages.teams import ATeamPage
import time

class VideosTab(ATeamPage):
    """Actions for the Videos tab of a Team Page.

    """
    _URL = 'teams/%s/videos/'
    _SEARCH = 'form.search input[name="q"]'
    _SEARCHING_INDICATOR = "img.placeholder"
    _NO_RESULTS = 'p.empty'
    NO_VIDEOS_TEXT = 'Sorry, no videos here ...'

    _VIDEO = 'ul.videos li'
    _VIDEO_TITLE = 'div.thumb a' # title is an attribute of a
    _VIDEO_THUMB = 'div.thumb a img'
    _VIDEO_LANGS = '.languages'
    _VIDEO_TASK_LINK = '.callout' # href has the url
    _ADD_VIDEO = 'a[href*="add/video"]'
    _MOVE_VIDEOS = 'a[href*="move-videos"]'
    _CLEAR_FILTERS = 'a.cancel'
    _FILTERS = 'a#sort-filter span'
    _FILTER_OPEN = 'a#sort-filter span.open'
    _ADMIN_LINKS = 'ul.admin-controls li a'

    #ADD VIDEO FORM
    _VIDEO_URL = 'input#id_video_url'
    _PROJECT = 'select#id_project'
    _THUMB = 'input#id_thumbnail'
    _SUBMIT = 'div.submit button'

   #ERRORS
    _ERROR = '.errorlist li'
 
    #REMOVE VIDEO FORM 
    _REMOVE_OPTION = "input[value='%s']"  # % team-removal or total-destruction
    _REMOVE = "div#remove-modal input[value='Remove']"

    #EDIT VIDEO OPTIONS - thumb and project are the same as submit form
    _EDIT_TEAM = 'select#id_team'
    _MOVE_VIDEO = 'div.submit a#move-video'
    _SUBMIT_MOVE_CONFIRM = 'div.modal-footer input.btn.danger'
    _NEW_THUMB_LINK = "form a[href*='user-data']"

    #FILTER and SORT
    #_LANG_FILTER = 'div.filters div.filter-chunk div'
    _LANG_FILTER = 'select#lang'
    _LANG_MODE_FILTER = 'select#lang_mode'
    _SORT_FILTER = 'select[name="sort"]'
    _PROJECT_FILTER = 'select#project'
    _PRIMARY_AUDIO_FILTER = 'select#primary_audio_lang'
    _UPDATE_FILTER = 'button#update'

    #BULK MOVE VIDEOS
    _BULK_SELECT = "a.bulk-select" 
    _BULK_TEAM_PULLDOWN = "div#id_team_chzn a"
    _BULK_PROJECTS = "select#projects-select"
    _MOVE_SELECTED = "button[name='move']"

    def open_videos_tab(self, team):
        """Open the team with the provided team slug.

        """
        self.logger.info('Opening the videos tab for the team %s' %team)
        self.open_page(self._URL % team)

    def search(self, search_text):
        self.logger.info('Searching for videos matching %s' % search_text)
        self.wait_for_element_present(self._SEARCH)
        self.submit_form_text_by_css(self._SEARCH, search_text)
        self.wait_for_element_not_visible(self._SEARCHING_INDICATOR)


    def add_video(self, url, thumb=None, project=None):
        """Submits a video for the team via url.

        """
        self.logger.info('Adding the video %s to the team' % url)
        self.click_by_css(self._ADD_VIDEO)
        self.type_by_css(self._VIDEO_URL, url)
        if thumb:
            self.type_by_css(self._THUMB, thumb)
        if project:
            self.select_option_by_text(self._PROJECT, project)
        self.click_by_css(self._SUBMIT) 

    def _open_filters(self):
        curr_url = self.current_url()
        if 'project=' in curr_url:
            self.logger.info('shoud find filter open')
        elif self.is_element_visible(self._FILTER_OPEN):
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
 
    def project_filter(self, project):
        """Filter the displayed videos by project

        Valid choices are the full project name 
        """
        self.logger.info('Filtering videos by project %s ' % project)
        self._open_filters()
        self.click_by_css('div#project_chzn a.chzn-single')
        self.select_from_chosen(self._PROJECT_FILTER, project)

    def primary_audio_filter(self, setting):
        """Filter the displayed videos by primary audio set 

        This is only for bulk move videos page.
        """
        self._open_filters()
        self.click_by_css('div#primary_audio_lang_chzn a.chzn-single')
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
        

    def _video_element(self, video):
        """Return the webdriver object for a video based on the title.

        """
        self.wait_for_element_present(self._VIDEO_THUMB)
        time.sleep(2)  #Make sure all the vids have a chance to load.
        video_els = self.browser.find_elements_by_css_selector(
                      self._VIDEO)

        for el in video_els:
            try:
                title_el = el.find_element_by_css_selector(self._VIDEO_TITLE)
                if title_el.get_attribute('title') == video:
                    return el
            except:
                continue

    def _hover_video(self, video=None): 
        """Hover over a video with the given title, or the first one.

        """
        if not video: # choose the first one present
            self.hover_by_css(self._VIDEO_THUMB)
        else:
            vid_element = self._video_element(video)
            self.hover_by_element(vid_element, self._VIDEO_THUMB)

 
    def _click_video_action(self, action, video):
        """Click the action link for the video title.

        Current options are 'Tasks', 'Edit', and 'Remove'
        Have to find the element, then click as clicking by link text
        hangs on jenkins.
        """
        vid_element = self._video_element(video)
        link_els = self.get_sub_elements_list(vid_element, self._ADMIN_LINKS)
        for el in link_els:
            if el.text == action:
                el.click()
                break
        else:
            self.record_error("Can not find the requested action link")


    def _video_actions_present(self, video):
        """Get the list of actions available for a video.

        Current options are 'Tasks', 'Edit', and 'Remove'
        """
        vid_element = self._video_element(video)
        link_els= self.get_sub_elements_list(vid_element, self._ADMIN_LINKS)
        link_list = []
        for el in link_els:
            link_list.append(el.text)
        return link_list

    def video_has_link(self, video, link_text):
        """Check if link text displayed in the admin-controls links.

        """
        self.logger.info('Checking video {0} for the {1} link'.format(
                          video, link_text))
        links = self._video_actions_present(video)
        self.logger.info('Got the links %s' % links)
        if link_text in links:
            return True 


    def remove_video(self, video=None, removal_action=None):
        """Remove the video from the team or site.

        """
        self.logger.info('Removing the video %s' % video)
        self._click_video_action('Remove', video)
        if removal_action:
            self.logger.info('Using the %s remove option' % removal_action)
            self.click_by_css(self._REMOVE_OPTION % removal_action)
        self.click_by_css(self._REMOVE)
        time.sleep(3)
        self.handle_js_alert("accept")

    def edit_video(self, video=None, project=None, team=None, thumb=None):
        self.logger.info('Editing the video %s' % video)
        self._click_video_action('Edit', video)
        time.sleep(3)
        if team:
            self.logger.info('Changing the team to %s' % team)
            self.click_by_css('a.chzn-single span')
            self.select_from_chosen(self._EDIT_TEAM, [team])
            self.click_by_css(self._MOVE_VIDEO)
            self.click_by_css(self._SUBMIT_MOVE_CONFIRM)

        elif project or thumb:
            if project:
                self.logger.info('Changing the project to %s' % project)

                self.click_by_css('a.chzn-single span')
                self.select_from_chosen(self._PROJECT, [project])
            if thumb:
                self.logger.info('Changing the thumbnail')
                self.type_by_css(self._THUMB, thumb)
            time.sleep(3)
            self.wait_for_element_visible('form.edit-video div button')
            self.click_by_css('form.edit-video div button')
        else: #cancel out of the dialog with no actions
            self.logger.info('Made no changes.')


    def open_video_tasks(self, video=None):
        """Open the task page for a video given the title.

        """
        self.logger.info('Opening tasks for video %s' % video)
        self._click_video_action('Tasks', video)


    def team_video_id(self, video):
        self.logger.info('Getting the task video id')
        self._hover_video(video)        
        task_url = self.get_element_attribute(self._VIDEO_TASK_LINK, 'href')
        return task_url.split('?')[1].split('=')[1]


    def displayed_tasks(self, video):
        """Return the text for the number of tasks displayed on the video.

        """
        self.logger.info('Getting the list of displayed tasks for %s' % video)
        video_el = self._video_element(video)
        tasks = video_el.find_element_by_css_selector(
                self._VIDEO_TASK_LINK).text
        return tasks

    def displayed_languages(self, video):
        """Return number of tasks or languages displayed on the video.

        """
        self.logger.info('Getting number of tasks of language for %s' % video)
        video_el = self._video_element(video)
        langs = video_el.find_element_by_css_selector(
                self._VIDEO_LANGS).text
        return langs
 
    def video_present(self, video):
        self.logger.info('Checking if video %s is displayed' % video)
        self.wait_for_element_present(self._VIDEO_THUMB)
        video_el = self._video_element(video)
        if video_el:
            return True

    def video_url(self, video):
        self.logger.info('Gtting the video url for video %s' % video)
        self.wait_for_element_present(self._VIDEO_THUMB)
        video_el = self._video_element(video)
        return video_el.get_attribute('href')       

    def open_video(self, video):
        self.logger.info('Opening the video page for %s' % video)
        self.wait_for_element_present(self._VIDEO_THUMB)
        video_el = self._video_element(video)
        video_el.click() 

    def first_video_listed(self):
        self.logger.info('Getting the title of first video on page')
        first_video = self.browser.find_element_by_css_selector(
            self._VIDEO_TITLE)
        return first_video.get_attribute('title')
        

    def search_no_result(self):
        self.logger.info('Getting the no search results text displayed')
        return self.get_text_by_css(self._NO_RESULTS)

       
    def error_message(self):
        self.logger.info('Getting the displayed error text')
        return self.get_text_by_css(self._ERROR)

    def new_thumb_location(self):
        self.logger.info('Getting the link of new thumnb')
        return self.get_text_by_css(self._NEW_THUMB_LINK)

    def num_videos(self):
        self.logger.info('Getting the number of videos on the page')
        video_els = self.browser.find_elements_by_css_selector(self._VIDEO_THUMB)
        return len(video_els)

    def videos_displayed(self):
        self.logger.info('Waiting for videos to display on page.')
        self.wait_for_element_present(self._VIDEO_THUMB)

    def open_bulk_move(self):
        self.click_by_css(self._MOVE_VIDEOS)

    def bulk_select(self):
        self.wait_for_element_present(self._BULK_SELECT)
        self.click_by_css(self._BULK_SELECT)
        
    def bulk_team(self, team):
        self.click_by_css(self._BULK_TEAM_PULLDOWN)
        self.select_from_chosen(self._EDIT_TEAM, team)

    def bulk_project(self, project):
        self.select_option_by_text(self._BULK_PROJECTS, project)

    def submit_bulk_move(self):
        self.click_by_css(self._MOVE_SELECTED) 
        time.sleep(3)

