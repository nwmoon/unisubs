#!/usr/bin/env python
import time
from nose.tools import assert_true, assert_false
from webdriver_testing.pages.site_pages import UnisubsPage

class TeamsDirPage(UnisubsPage):
    """
     Search page is the main search page stub.  Watch Page and Search Results page
    """

    _URL = "teams/"
    _SEARCH = "form.search input[name='q']"
    _SORT = "span.sort_label"
    _SORT_OPTION = "div.sort_button ul li a[href*='%s']"
    _TEAM = "ul.listing li"
    _TEAM_LINK = 'h3 a[href*=%s]'
    _TEAM_NAME = 'a'
    _TEAM_MEMBERS = 'ul.actions h4'
    _TEAM_VIDEOS = 'ul.actions li:nth-child(2)'
    _TEAM_DESCRIPTION = 'p'
    _TEAM_DESCRIPTOR = '.descriptor'
    _NO_MATCHES = 'p.empty'
    _NO_MATCH_TEXT = 'Sorry, no teams found.'
    _TEAM_BY_POSITION = "ul.listing li:nth-child(%d)"

    _INVITE_ERROR = 'div#error h1'



    #YOUR TEAMS TAB
    _YOUR_URL = "teams/my/"
    _LEAVE_URL = "teams/leave_team/%s/"
    _LEAVE = "a#leave"

    def open_teams_page(self):
        self.open_page(self._URL)


    def _team_elem(self, team):
        """Given the team's text name, return the css locator string.

        """
        self.wait_for_element_present(self._TEAM + " " + self._TEAM_NAME)
        teams = self.browser.find_elements_by_css_selector(self._TEAM)
        for el in teams:
            team_el = el.find_element_by_css_selector(self._TEAM_NAME)
            print teams.index(el)
            if team == team_el.text:
                return self._TEAM_BY_POSITION % (teams.index(el) + 1)

    def team_search(self, search_term):
        self.clear_text(self._SEARCH)
        self.submit_form_text_by_css(self._SEARCH, search_term)

    def search_has_no_matches(self):
        if self.is_text_present(self._NO_MATCHES, self._NO_MATCH_TEXT):
            return True

    def sort(self, order):
        """Sort the teams.

        """

        sort_orders = ['date', 'name', 'members']
        assert_true(order in sort_orders,
                    "unknown value for order, expected one of %s" % sort_orders)

        self.open_page("teams/?o=%s" % order)

    def first_team(self):
        return self.teams_on_page()[0]

    def last_team(self):
        return self.teams_on_page()[-1:][0]

    def all_team_elements(self):
        team_elements = self.browser.find_elements_by_css_selector(self._TEAM)
        return team_elements

    def team_el(self, team):
        team_elements = self.all_team_elements()
        for el in team_elements:
            if el.find_element_by_css_selector(self._TEAM_NAME).text == team:
                return el
        else:
            self.fail("Did not find the team named %s on the page" % team)

    def members(self, team):
        """Return the number of members displayed for a team.

        """
        element = self.team_el(team)
        members = element.find_element_by_css_selector(self._TEAM_MEMBERS).text
        return int(members.split()[0])

    def videos(self, team):
        """Return the number of videos displayed for a team.

        """

        element = self.team_el(team)
        videos = element.find_element_by_css_selector(self._TEAM_VIDEOS).text
        return int(videos.split()[0])

    def teams_on_page(self):
        """Return a list of teams displayed on the page.

        """
        teams_list = []
        team_name_els = self.browser.find_elements_by_css_selector(
            " ".join([self._TEAM, self._TEAM_NAME]))
        for el in team_name_els:
            teams_list.append(el.text)
        return teams_list

    def team_displayed(self, team):
        team_list = self.teams_on_page()
        if team in team_list:
            return True
        else:
            return "Team {0} not found in the list of teams {1}".format(team, 
                team_list)


    def marked_private(self, team):
        """Return True if a team is marked private.

        """
        self.team_search(team)
        descriptor_text = self.get_text_by_css(self._TEAM_DESCRIPTOR)
        if descriptor_text == "Private":
            return True

    def open_team_with_link(self, team_slug):
        """Open a specific team page, given the team slug.

        """
        self.click_by_css(self._TEAM_LINK % team_slug)

    # YOUR TEAMS TAB SPECIFIC


    def open_my_teams_page(self):
        """Open the teams/my/ url.

        """
        self.open_page(self._YOUR_URL)

    def open_my_team(self, team=None):
        if self._YOUR_URL not in self.browser.current_url:
            self.open_my_teams_page()
        if not team:
            first_team = self._TEAM, self._TEAM_NAME
            self.click_by_css(first_team)
        else:
            team_el = self._team_elem(team)
            team = team_el.find_element_by_css_selector(self._TEAM_NAME)
            team.click()

    def leave_team(self, team_stub):
        self.open_page(self._LEAVE_URL % team_stub)

    def leave_team_successful(self):
        self.wait_for_element_present(self._SUCCESS_MESSAGE)
        if self.is_text_present(self._SUCCESS_MESSAGE, 
                'You have left this team.'):
            return True

    def leave_team_failed(self):
        if self.is_text_present(self._ERROR_MESSAGE, 
                'You are the last owner of this team.'):

            return True

    def _hover_team(self, team):
        team_el = self._team_elem(team)
        self.hover_by_css(team_el)

    def leave_present(self, team):
        leave_link = False
        self._hover_team(team)
        if self.is_element_visible(self._LEAVE):
            leave_link = True
        return leave_link

    def click_leave_link(self, team):
        self.click_item_after_hover(self._team_elem(team), self._LEAVE)
        self.handle_js_alert('accept')

    def invite_error(self):
        return self.get_text_by_css(self._INVITE_ERROR)




