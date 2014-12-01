#!/usr/bin/env python

from webdriver_testing.pages import Page
import time

class EditorDialogs(Page):

    _CONTINUE = 'div.unisubs-modal-lang a.unisubs-green-button'
    _DIALOG = 'div.unisubs-modal-widget-content'
    _WARNING = 'div.unisubs-modal-lang-content' #Resume editing
    #DIALOG TYPES
    _HOW_TO = 'div.unisubs-howtopanel'
    _TYPING = _DIALOG + '.unisubs-modal-widget-transcribe'
    _SYNCING = _DIALOG + '.unisubs-modal-widget-sync'
    _TITLE_DESCRIPTION = '.unisubs-help-heading'  #NOT GOOD
    _REVIEW = _DIALOG + '.unisubs-model-widget-review'
    _GUIDELINES = 'div.unisubs-guidelinespanel'
    _GUIDELINE_TEXT = _GUIDELINES + ' div p'
    _HEADING = 'div.unisubs-modal-lang h3'


    _DONE = 'a.unisubs-done span'
    _CHECKBOX = 'span.goog-checkbox'
    _CHECKBOX_CHECKED = 'span.goog-checkbox-checked'
    _CLOSE = 'span.unisubs-modal-widget-title-close'
    _CLOSE_LANG_MODAL = 'span.unisubs-modal-lang-title-close'

    _COMPLETED_DIALOG = 'div.unisubs-modal-completed'

    _SAVED_OK = 'div.unisubs-modal-completed a.unisubs-green-button'

    def wait_for_dialog_present(self):
        self.wait_for_element_present(self._DIALOG)


    def warning_dialog_title(self):
        self.wait_for_element_present(self._WARNING)
        title = self.get_text_by_css(self._WARNING + ' h3')
        return title

    def close_dialog(self):
        self.logger.info('closing the dialog')
        self.click_by_css(self._CLOSE)

    def close_lang_dialog(self):
        self.logger.info('closing the language dialog')
        self.click_by_css(self._CLOSE_LANG_MODAL)
    
    def continue_to_next_step(self):
        self.logger.info('clicking done to continue to the next step')
        self.wait_for_element_present(self._DONE, 30)
        self.click_by_css(self._DONE)

    def continue_past_help(self, skip=True):
        self.logger.info('Checking for help video, and continuing past')
        time.sleep(5)
        if self.is_element_present(self._HOW_TO):
            if skip:
                self.click_by_css(self._CHECKBOX)
            self.continue_to_next_step()

    def click_saved_ok(self):
        self.logger.info('clicking the subtitles saved confirmation box')
        if self.check_if_element_present(self._SAVED_OK, wait_time=5):
            self.click_by_css(self._SAVED_OK)
            self.wait_for_element_not_present(self._SAVED_OK)

    def resume_dialog_ok(self):
        self.logger.info('clicking OK in the resume dialog')
        self.wait_for_element_present(self._CONTINUE)
        elements_found = self.get_elements_list(self._CONTINUE)
        for el in elements_found:
            if el.text == 'OK':
                el.click()

    def click_dialog_continue(self):
        self.logger.info('clicking Continue in the dialog')
        self.wait_for_element_present(self._CONTINUE)
        self.click_by_css(self._CONTINUE)

    def mark_subs_complete(self, complete=True):
        self.logger.info('checking for the mark subs complete dialog')
        time.sleep(3)
        if self.is_element_visible(self._CHECKBOX):
            if complete == True:
                self.logger.info('Marking subs as complete')
                if not self.is_element_present(self._CHECKBOX_CHECKED):
                    self.click_by_css(self._CHECKBOX)
        self.click_by_css(self._SAVED_OK)
        

    def incomplete_alert_text(self):
        self.logger.info('Accepting the subs incomplete dialog')
        a = self.browser.switch_to_alert()
        alert_text = a.text
        a.accept()
        return alert_text


class CreateLanguageSelection(EditorDialogs):
    _DIALOG_NAME = 'Create subtitles'
    _ORIGINAL_LANG = 'select.original-language'
    _TRANSCRIBE_LANG = 'select.to-language'
    _SOURCE_LANG = 'select.from-language'

    def lang_selection_dialog_present(self):
        self.logger.info('checking for lang selection dialog')
        self.wait_for_element_present(self._HEADING)
        if self._DIALOG_NAME in self.get_text_by_css(self._HEADING):
            return True

    def _set_video_language(self, language):
        """Choose the videos original language.

        Language should be the fully written language'
        ex: French, Canadian 
        """
        self.logger.info('setting the primary audio language: %s' % language) 
        self.select_option_by_text(self._ORIGINAL_LANG, language)
        
    def _set_new_language(self, language):
        """Choose the language that is being transcribed.

        Language should be the fully written language'
        ex: French, Canadian 
        """
        self.logger.info('setting transcribe lang: %s' % language)
        self.select_option_by_text(self._TRANSCRIBE_LANG, language)
   
    def _set_translation_source(self, language):
        """Choose the language that is being transcribed.

        Language should be the fully written language'
        ex: French, Canadian 
        """
        self.logger.info('setting from lang: %s' % language)
        self.select_option_by_text(self._SOURCE_LANG, language)

    def _submit_choices(self):
        self.logger.info('submitting dialog choices')
        self.click_by_css(self._CONTINUE)

    def create_original_subs(self, video_language, new_language):
        assert self.lang_selection_dialog_present()
        self._set_video_language(video_language)
        self._set_new_language(new_language)
        self._submit_choices()

    def lang_selection(self, **kwargs):
        self.logger.info('Specifying the languages')
        assert self.lang_selection_dialog_present()
        if 'video_language' in kwargs:
            self._set_video_language(kwargs['video_language'])
        if 'new_language' in kwargs:
            self._set_new_language(kwargs['new_language'])
        if 'translation_source' in kwargs:
            self._set_translation_source(kwargs['translation_source'])
        self._submit_choices()

