#!/usr/bin/env python
import time

from webdriver_testing.pages.site_pages.teams import ATeamPage

class MembersTab(ATeamPage):

    _URL = "teams/%s/members/"
    _USERNAME = "ul.members.listing li h3 a"
    _USER_LANGS = "ul.members.listing li h3 span.descriptor"
    _ROLE = "ul.members.listing li p"
    _ACTIONS = "ul.members.listing li ul.actions li"
    _INVITE_MEMBERS = "div.tools a.button[href*='members/invite']"
    _EDIT_USER = "a.edit-role"
    _DELETE_USER = 'ul.admin-controls li a.delete'
    _SORT_FILTER = "a#sort-filter"
    _SEARCH = 'form.search input[name="q"]'

    #EDIT USER MODAL
    _ROLE_PULLDOWN = "select#roles"
    _ROLE_LANG_PULLDOWN = "div#language-restriction select#lang"
    _ROLE_PROJ_PULLDOWN = "div#project-restriction select#proj"
    _SAVE_EDITS = "a.action-save"
    _CANCEL_EDITS = ".modal-footer .action-close"

    #INVITATION FORM 
    _INVITEE_USERNAME_PULLDOWN = "div#uid_chzn a"
    _INVITEE_USERNAME = 'select[name="user_id"]'
    _INVITEE_MESSAGE = "textarea#id_message"
    _INVITEE_ROLE = "select#id_role"
    _INVITATION_SEND = "div.submit button"

    def open_members_page(self, team):
        """Open the team with the provided team slug.

        """
        self.open_page(self._URL % team)
        self.wait_for_element_present(self._SORT_FILTER)


    def user_link(self):
        """Return the url of the first user on the page.

        """
        return self.get_element_attribute(self._USERNAME, 'href')

    def user_languages(self):
        """Return the languages of the first user on the page.

        """
        language_list = []
        els = self.browser.find_elements_by_css_selector(self._USER_LANGS)
        for el in els:
            language_list.append(el.text)
        return language_list

    def user_role(self):
        """Return the of the user role of teh first user on the page.

        """
        
        return self.get_text_by_css(self._ROLE)

    def displays_invite(self):
        return self.is_element_present(self._INVITE_MEMBERS)


    def invite_user_via_form(self, user, message, role):
        """Invite a user to a team via the invite form.

        """
        
        self.click_by_css(self._INVITE_MEMBERS)
        self.wait_for_element_present(self._INVITEE_USERNAME_PULLDOWN)
        self.click_by_css(self._INVITEE_USERNAME_PULLDOWN)
        self.type_by_css('div.chzn-search input', user.username)
        if user.first_name:
            user = "{0} ({1} {2})".format(user.username,
                                          user.first_name,
                                          user.last_name)
        else:
            user = "{0} ({0})".format(user.username)
       
        self.select_from_chosen(self._INVITEE_USERNAME, 
                                user)
        self.type_by_css(self._INVITEE_MESSAGE, message)
        self.select_option_by_text(self._INVITEE_ROLE, role)
        self.submit_by_css(self._INVITATION_SEND)


    def member_search(self, search):
        self.clear_text(self._SEARCH)
        self.submit_form_text_by_css(self._SEARCH, search)

    def lang_search(self, team_slug, lang):
        """Open the url of language search term.

        """
        team_url = self._URL % team_slug
        search_url = "%s?lang=%s" % (team_url, lang)
        self.open_page(search_url)

    def delete_user(self):
        """Edit a users roles via the  form.

        """
        self.hover_by_css(self._USERNAME)
        self.click_by_css(self._DELETE_USER)
        self.handle_js_alert('accept')

    def edit_user(self, role=None, languages=[], projects=[]):
        """Edit a users roles via the  form.

        """
        self.hover_by_css(self._ROLE)
        self.click_by_css(self._EDIT_USER)
        time.sleep(2)
        if role:
            self.select_option_by_text(self._ROLE_PULLDOWN, role)
        if not languages == []:
            self._language_restrictions(languages)
        if not projects == []:
            self._project_restrictions(projects)
        self.click_by_css(self._SAVE_EDITS)
        time.sleep(2)

    def _language_restrictions(self, languages):
        """Restrict languages via the edit user form.

        """
        self.click_by_css("div#lang_chzn")
        self.select_from_chosen(self._ROLE_LANG_PULLDOWN, languages)

    def _project_restrictions(self, projects):
        """Restrict projects via the edit user form.

        """
        self.click_by_css("div#proj_chzn")
        self.select_from_chosen(self._ROLE_PROJ_PULLDOWN, projects)

    def delete_user_link(self):
        return self.is_element_present(self._DELETE_USER)
