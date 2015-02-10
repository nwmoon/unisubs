# -*- coding: utf-8 -*-
from caching.tests.utils import assert_invalidates_model_cache
from webdriver_testing.webdriver_base import WebdriverTestCase
from webdriver_testing.pages.site_pages.teams_dir_page import TeamsDirPage
from teams.models import TeamMember
from utils.factories import *

class TestCaseLeaveTeam(WebdriverTestCase):
    NEW_BROWSER_PER_TEST_CASE = False

    @classmethod
    def setUpClass(cls):
        super(TestCaseLeaveTeam, cls).setUpClass()

        cls.team_dir_pg = TeamsDirPage(cls)
        cls.owner = UserFactory()
        cls.admin = UserFactory()
        cls.manager = UserFactory()
        cls.member = UserFactory()
        cls.team = TeamFactory(
            admin = cls.admin,
            manager = cls.manager,
            member = cls.member,
            membership_policy=2,  # manager invite-only
            )
        TeamMemberFactory(team=cls.team, user=cls.owner)
        cls.team_dir_pg.open_teams_page()


    def test_leave_contributor(self):
        """A contributor can leave a team.

        """
        self.team_dir_pg.log_in(self.member.username, 'password')
        with assert_invalidates_model_cache(self.team):
            self.team_dir_pg.leave_team(self.team.slug)
        self.assertTrue(self.team_dir_pg.leave_team_successful())

    def test_leave_second_to_last_owner(self):
        """Second to last owner can leave the team.

        """
        owner2 = TeamMemberFactory(team = self.team).user

        self.team_dir_pg.log_in(owner2.username, 'password')
        self.team_dir_pg.leave_team(self.team.slug)
        self.assertTrue(self.team_dir_pg.leave_team_successful())

    def test_leave_admin(self):
        """An admin can leave the team.

        """
        self.team_dir_pg.log_in(self.admin.username, 'password')
        self.team_dir_pg.leave_team(self.team.slug)
        self.assertTrue(self.team_dir_pg.leave_team_successful())

    def test_leave_last_owner(self):
        """The last owner can not leave the team.

        """
        self.team_dir_pg.log_in(self.owner.username, 'password')
        self.team_dir_pg.leave_team(self.team.slug)
        self.assertTrue(self.team_dir_pg.leave_team_failed())

    def test_leave_last_owner_ui(self):
        """The last owner has no leave button on hover.
        """
        self.team_dir_pg.log_in(self.owner.username, 'password')
        self.team_dir_pg.open_my_teams_page()
        self.assertFalse(self.team_dir_pg.leave_present(self.team.name))

    def test_leave_ui(self):
        """A contributor leaves team by clicking leave link.

        """
        contributor = TeamMemberFactory(team = self.team).user

        self.team_dir_pg.log_in(contributor.username, 'password')
        self.team_dir_pg.open_my_teams_page()
        self.team_dir_pg.click_leave_link(self.team.name)
        self.assertTrue(self.team_dir_pg.leave_team_successful())

