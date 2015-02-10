#!/usr/bin/env python
from webdriver_testing.pages.site_pages.teams import ATeamPage

class MessagesTab(ATeamPage):
    """Actions for the Messages tab of the Team Settings Page.

    """

    _URL = 'teams/%s/settings/guidelines/'  #provide the team slug

    #MESSAGES FIELDS
    _INVITATION_MESSAGE = 'textarea#id_messages_invite'
    _APPLICATION_MESSAGE = 'textarea#id_messages_application'
    _NEW_MANAGER_MESSAGE = 'textarea#id_messages_manager'
    _NEW_ADMIN_MESSAGE = 'textarea#id_messages_admin'
    _NEW_MEMBER_MESSAGE = 'textarea#id_messages_joins'
    _MESSAGES = ['INVITATION', 'APPLICATION', 'NEW_MANAGER', 'NEW_ADMIN', 'NEW_MEMBER'] 
    
    #GUIDELINES FIELDS
    _SUBTITLE_GUIDELINES = 'textarea#id_guidelines_subtitle'
    _TRANSLATE_GUIDELINES = 'textarea#id_guidelines_translate'
    _REVIEW_GUIDELINES = 'textarea#id_guidelines_review'
    _GUIDELINES = ['SUBTITLE', 'TRANSLATE', 'REVIEW']

    _SAVE_CHANGES = 'div.submit input.submit'


    def open_messages_tab(self, team):
        """Open the messages tag for the given team slug.

        """
        self.open_page(self._URL % team)
        self.wait_for_element_present(self._INVITATION_MESSAGE)

   
    def _customize_messages(self, **messages):
        """Enter the message text in the message field.

        """
        for message_field, text in messages.iteritems():
            field = getattr(self, '_'.join(['', message_field, 'MESSAGE']))
            self.type_by_css(field, text)

    def _stored_message_text(self):
        """Return the stored text for all message fields'

        """
        current_messages = dict()
        for message_field in self._MESSAGES:
            css_field = getattr(self, 
                '_'.join(['', message_field, 'MESSAGE']))
            displayed_text = self.get_text_by_css(css_field)
            current_messages[message_field] = displayed_text
        return current_messages

    def _stored_guideline_text(self):
        """Return the stored text for all guidelines fields'

        """

        current_guidelines = dict()
        for guideline_field in self._GUIDELINES:
            css_field = getattr(self, 
                '_'.join(['', guideline_field, 'GUIDELINES']))
            displayed_text = self.get_text_by_css(css_field)
            current_guidelines[guideline_field] = displayed_text
        return current_guidelines
 
    def _customize_guidelines(self, **guidelines):
        """Enter the message text in the message field.

        """

        for guideline_field, text in guidelines.iteritems():
            field = getattr(self, 
                '_'.join(['', guideline_field, 'GUIDELINES']))
            self.type_by_css(field, text)

    def edit_messages(self, messages):
        """Edit the text of the messages fields and save.

           Messages should be a dict of the fields and text.
        """

        self._customize_messages(**messages)
        self.submit_by_css(self._SAVE_CHANGES)

    def edit_guidelines(self, guidelines):
        """Edit the text of the guidelines fields and save.

           Guidelines should be a dict of the fields and text.
        """

        self._customize_guidelines(**guidelines)
        self.click_by_css(self._SAVE_CHANGES)

    def stored_messages(self):
        """Return a dict of the currenlty configured messages.

        """
        messages = self._stored_message_text()
        return messages

    def stored_guidelines(self):
        """Return a dict of the currently configured guidelines.

        """
        guidelines = self._stored_guideline_text()
        return guidelines


