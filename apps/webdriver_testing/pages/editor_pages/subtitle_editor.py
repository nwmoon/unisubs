from dialogs import EditorDialogs
import codecs
import os
import sys
import time

class SubtitleEditor(EditorDialogs):

    _EDITOR = 'div.unisubs-modal-widget'
    _DIALOG_HEADING = 'div.unisubs-help-heading h2'

    #UNISUBS ON-VIDEO CONTROLS
    _VIDEO_PLAYBACK = 'div.unisubs-videoControls'
    _PLAY = 'span.unisubs-playPause.play'
    _PAUSE = 'span.unisubs-playPause.pause'
    _BUFFERED = 'div.unisubs-buffered' # width 250 is 100% buffered


    #SUBS ENTRY AND DISPLAY (LEFT SIDE)
    _TEXT_INPUT = 'textarea.goog-textarea.trans'
    _ACTIVE_SUB_EDIT = 'span.unisubs-title textarea'
    _TRANSLATE_INPUT = 'textarea.unisubs-translateField'
    _SUBS = 'ul.unisubs-titlesList li span.unisubs-title span:nth-child(1)'
    _TIMINGS = 'ul.unisubs-titlesList li span.unisubs-timestamp'
    _REVIEW_TIMINGS = 'span.unisubs-timestamp-time'
    _CURRENT_CAPTION = 'span.unisubs-captionSpan'

    _TRANSCRIBE_PAGE_TIMINGS = 'span.unisubs-timestamp-time-fixed'

    #CONTROL BUTTON (RIGHT SIDE)
    _SYNC = 'div.unisubs-begin span:nth-child(2)'
    _PLAY_PAUSE = 'div.unisubs-play span'
    _SKIP_BACK = 'div.unisubs-skip span.unisubs-control'
    _RESTART = 'a.unisubs-restart'
    _PREVIOUS_STEP = 'a.unisubs-backTo'

    #EXTRA OPTIONS
    _SAVE_AND_EXIT = 'div.unisubs-saveandexit a span'
    _DOWNLOAD_SUBTITLES = 'a.unisubs-download-subs'
    _DOWNLOAD_FORMAT = 'select.copy-dialog-select'
    _NEW_EDITOR_BETA = 'div.unisubs-saveandopeninneweditor a span'

    #REVIEW DIALOG
    _REVIEW_DONE = 'a.unisubs-done'

    #TRANSLATION DIALOG
    _TRANSLATION_SOURCE = "span.unisubs-title"


    def type_subs(self, subs_file=None):
        self.logger.info('typing in subtitles')
        typed_sub_list = []
        if not subs_file:
            subs_file = os.path.join(os.path.dirname
                (os.path.abspath(__file__)), 'default_sub_text.txt')
        for i, line in enumerate(codecs.open(subs_file, encoding='utf-8')):
            self.type_by_css(self._TEXT_INPUT, line)
            typed_sub_list.append(line.strip())
        return typed_sub_list

    def type_translation(self, subs_file=None):
        self.logger.info('typing in translation')
        self.wait_for_element_present(self._TRANSLATE_INPUT)
        if not subs_file:
            subs_file = os.path.join(os.path.dirname
                (os.path.abspath(__file__)), 'default_sub_text.txt')
        input_elements = self.browser.find_elements_by_css_selector(
                self._TRANSLATE_INPUT)
        for i, line in enumerate(codecs.open(subs_file, encoding='utf-8')):
            input_elements[i].send_keys(line)

    def translation_source(self):
        source_list = []
        els = self.get_elements_list(self._TRANSLATION_SOURCE)
        for el in els:
            source_list.append(el.text)
        return source_list
        


    def edit_subs(self, subs_file=None):
        self.logger.info('editing subtitles')
        typed_sub_list = []
        if not subs_file:
            subs_file = os.path.join(os.path.dirname
                (os.path.abspath(__file__)), 'default_sub_text.txt')

        existing_subs = self.get_elements_list(self._SUBS)
        for i, line in enumerate(codecs.open(subs_file, encoding='utf-8')):
            existing_subs[i].click()
            self.clear_text(self._ACTIVE_SUB_EDIT)
            self.type_by_css(self._ACTIVE_SUB_EDIT, line + '\n')
            typed_sub_list.append(line.strip())
        return typed_sub_list


    def play(self):
        self.logger.info('starting playback')
        self.wait_for_element_present(self._VIDEO_PLAYBACK)
        if self.is_element_present(self._PLAY):
            self.click_by_css(self._PLAY)

    def pause(self):
        self.logger.info('pausing playback')
        self.wait_for_element_present(self._VIDEO_PLAYBACK)
        if self.is_element_present(self._PAUSE):
            self.click_by_css(self._PAUSE)

    def buffer_video(self):
        """Start and Stop playback to get the video buffered up to about 30%'
     
        """
        self.logger.info('buffering up the video...')
        self.play()
        self.wait_for_element_present(self._PAUSE)
        time.sleep(1)
        self.pause()
        start_time = time.time()
        while time.time() - start_time < 30:
            if (self.is_element_present(self._BUFFERED) and 
                    self.get_size_by_css(self._BUFFERED)['width'] > 90):
                break 
            else:
                time.sleep(0.1)

    def sync_subs(self, num_subs):
        """Syncs the given number of subtitles.

        """
        self.buffer_video()
        self.play()
        time.sleep(2)
        self.click_by_css(self._SYNC)

        for x in range(num_subs):
            time.sleep(2)
            self.logger.info('syncing') 
            self.click_by_css(self._SYNC)
        self.pause()

    def sub_timings(self, check_step=None):
        self.logger.info('getting the list of subtitle times')
        if check_step:
            timing_element = self._REVIEW_TIMINGS
        else:
            timing_element = self._TIMINGS
        timing_list = []
        self.wait_for_element_present(timing_element)
        timing_els = self.browser.find_elements_by_css_selector(
            timing_element)
        for el in timing_els:
            timing_list.append(el.text.strip())
        self.logger.info(timing_list)
        return timing_list

            
    def save_and_exit(self):
        self.logger.info('clicking save and exit from the dialog')
        self.page_down(self._SAVE_AND_EXIT)
        self.click_by_css(self._SAVE_AND_EXIT)
        self.mark_subs_complete()
        self.click_saved_ok()

    def save_translation(self):
        self.logger.info('clicking save and exit from the translation dialog')
        self.page_down(self._SAVE_AND_EXIT)
        self.click_by_css(self._SAVE_AND_EXIT)
        self.click_saved_ok()

    def subtitles_list(self):
        self.logger.info('getting the list of current subtitles')
        time.sleep(3)
        self.wait_for_element_present(self._SUBS)
        sub_list = []
        subtitle_els = self.browser.find_elements_by_css_selector(self._SUBS)
        for el in subtitle_els:
            sub_list.append(el.text.strip())
        return sub_list

    def download_subtitles(self, sub_format='SRT'):
        self.logger.info('downloading %s subtitles ' % sub_format)
        self.click_by_css(self._DOWNLOAD_SUBTITLES)
        self.select_option_by_text(self._DOWNLOAD_FORMAT, sub_format)
        # don't ever wait more than 15 seconds for this
        # but keep pooling for a terminating value
        start_time = time.time()
        while time.time() - start_time < 15:
            time.sleep(.2)
            stored_subs = self.browser.execute_script(
            "return document.getElementsByTagName('textarea')[0].value")
            # server errored out
            if stored_subs == "Something went wrong, we're terribly sorry.":
                self.record_error('Call to convert formats failed')
            # server hasn't returned yet
            elif stored_subs and stored_subs.startswith("Processing.") is False:
                break
        else:
            self.record_error("> 15 seconds passed, and subs weren't converted")
        #self.close_lang_dialog()
        return stored_subs

    def submit(self, complete=True):
        self.logger.info('submitting subtitles')
        self.continue_to_next_step()
        self.mark_subs_complete(complete)
        self.click_saved_ok()

    def dialog_title(self):
        self.wait_for_element_present(self._DIALOG_HEADING, 30)
        return self.get_text_by_css(self._DIALOG_HEADING) 

    def complete_review(self, result='Accept'):
        """Accept or Send Back the transcript. """
        self.logger.info('Review draft and %s' % result)
        done_buttons = self.browser.find_elements_by_css_selector(self._REVIEW_DONE)
        for el in done_buttons:
            if el.text == result:
                el.click()
                return

    def complete_approve(self, result='Approve'):
        """Approve or Send Back the transcript. """
        self.logger.info('Approve draft and %s' % result)
        done_buttons = self.browser.find_elements_by_css_selector(self._REVIEW_DONE)
        for el in done_buttons:
            if el.text == result:
                el.click()
                return

    def open_in_beta_editor(self, mark_complete=True, click_saved=True):
        self.click_by_css(self._NEW_EDITOR_BETA)
        if mark_complete:
            self.mark_subs_complete(complete=False)
        if click_saved:
            self.click_saved_ok()

        
