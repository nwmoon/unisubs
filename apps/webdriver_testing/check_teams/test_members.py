# -*- coding: utf-8 -*-
import time

from webdriver_testing.webdriver_base import WebdriverTestCase
from webdriver_testing.pages.site_pages.teams_dir_page import TeamsDirPage
from webdriver_testing.pages.site_pages.teams import members_tab
from webdriver_testing.pages.site_pages import user_messages_page
from utils.factories import *
from teams.models import TeamMember

class TestCaseMembersTab(WebdriverTestCase):
    """Verify edit of member roles and restrictions.  """
    NEW_BROWSER_PER_TEST_CASE = False

    @classmethod
    def setUpClass(cls):
        super(TestCaseMembersTab, cls).setUpClass()
        cls.team_dir_pg = TeamsDirPage(cls)
        cls.user_message_pg = user_messages_page.UserMessagesPage(cls)
        cls.members_tab = members_tab.MembersTab(cls)
        cls.user = UserFactory()
        cls.admin = UserFactory()
        cls.manager = UserFactory()
        cls.member = UserFactory()
        cls.team = TeamFactory(admin=cls.admin,
                               manager=cls.manager,
                               member=cls.member)
        cls.promoted_manager = TeamMemberFactory(role=TeamMember.ROLE_CONTRIBUTOR,
                               team=cls.team).user
        cls.promoted_admin = TeamMemberFactory(role=TeamMember.ROLE_CONTRIBUTOR,
                             team=cls.team).user
        cls.project = ProjectFactory(team=cls.team)
        cls.members_tab.open_members_page(cls.team.slug)


    def test_invitation_form(self):
        """Send an invitation via the form on the members tab.

        """
        self.members_tab.log_in(self.admin.username, 'password')
        self.members_tab.open_members_page(self.team.slug)
        self.members_tab.invite_user_via_form(user = self.user,
                                              message = 'Join my team',
                                              role = 'Contributor')
        self.members_tab.log_in(self.user.username, 'password')
        self.assertEqual(1, self.user.team_invitations.count())
        self.assertEqual(1, self.team.invitations.count())
        #Verify the user gets the message displayed.
        self.user_message_pg.open_messages()
        self.assertTrue('has invited you' in 
            self.user_message_pg.message_text())


    def test_assign_manager(self):
        """Asign a manager with no restrictions.

           Verify the display of the roles in the members tab.
        """
 
        self.members_tab.log_in(self.admin.username, 'password')
        self.members_tab.member_search(self.promoted_manager.username)
        self.members_tab.edit_user(role="Manager")
        self.members_tab.member_search(self.promoted_manager.username)
        self.assertEqual(self.members_tab.user_role(), 'Manager')

    def test_assign_manager_lang_restrictions(self):
        self.members_tab.log_in(self.admin.username, 'password')
        self.members_tab.member_search(self.promoted_manager.username)
        self.members_tab.edit_user(
            role="Manager", languages = 'English')
        self.members_tab.member_search(self.promoted_manager.username)

        self.assertEqual(self.members_tab.user_role(), 
                      'Manager for English language')

    def test_assign_manager_project_lang_restrictions(self):
        """Assign a manager with project restrictions.

           Verify the display of the roles in the members tab.
        """
        self.members_tab.log_in(self.admin.username, 'password')
        self.members_tab.member_search(self.promoted_manager.username)
        self.members_tab.edit_user(
            role="Manager", projects=self.project.name,
            languages=['French'])
        self.members_tab.member_search(self.promoted_manager.username)
        self.assertEqual(self.members_tab.user_role(), ('Manager for %s project '
                    'and for French language' % self.project.name))


    def test_assign_manager_project_restrictions(self):
        """Assign a manager with project restrictions.

           Verify the display of the roles in the members tab.
        """

        owner = TeamMemberFactory(team=self.team).user
        self.members_tab.log_in(owner.username, 'password')
        self.members_tab.member_search(self.promoted_manager.username)
        self.members_tab.edit_user(
            role="Manager", projects=self.project.name)
        self.members_tab.member_search(self.promoted_manager.username)
        self.assertEqual(self.members_tab.user_role(), 
                      'Manager for %s project' % self.project.name)


    def test_assign_admin(self):
        """Assign another admin with no restrictions.

           Verify the display of the roles in the members tab.
        """
        owner = TeamMemberFactory(team=self.team).user
        self.members_tab.log_in(owner.username, 'password')
        self.members_tab.member_search(self.promoted_admin.username)
        self.members_tab.edit_user(role="Admin")
        self.members_tab.member_search(self.promoted_admin.username)
        self.assertEqual(self.members_tab.user_role(), 
                      'Admin')


    def test_assign_admin_project_restrictions(self):
        """Assign an admin with project restrictions.

           Verify the display of the roles in the members tab.
        """
        owner = TeamMemberFactory(team=self.team).user
        self.members_tab.log_in(owner.username, 'password')
        self.members_tab.member_search(self.promoted_admin.username)
        self.members_tab.edit_user(
            role="Admin", projects=self.project.name)
        self.members_tab.member_search(self.promoted_admin.username)
        self.assertEqual(self.members_tab.user_role(), 
                      'Admin for %s project' % self.project.name)

    def test_admin_invite_owner(self):
        """Admin invite team, owner sees invite button."""
        owner = TeamMemberFactory(team=self.team).user
        self.team.membership_policy = 5
        self.team.save()
        self.members_tab.log_in(owner.username, 'password')
        self.members_tab.open_members_page(self.team.slug)
        self.assertTrue(self.members_tab.displays_invite())

    def test_admin_invite_admin(self):
        """Admin invite team, admin sees invite button. """
        self.team.membership_policy = 5
        self.team.save()
        self.members_tab.log_in(self.admin.username, 'password')
        self.members_tab.open_members_page(self.team.slug)
        self.assertTrue(self.members_tab.displays_invite())

    def test_admin_invite_manager(self):
        """Admin invite team, manager does not see invite button."""
        self.team.membership_policy = 5
        self.team.save()
        self.members_tab.log_in(self.manager.username, 'password')
        self.members_tab.open_members_page(self.team.slug)
        self.assertFalse(self.members_tab.displays_invite())

 
    def test_admin_invite_member(self):
        """Admin invite team, member does not see invite button."""

        self.team.membership_policy = 5
        self.team.save()
        self.members_tab.log_in(self.member.username, 'password')
        self.members_tab.open_members_page(self.team.slug)
        self.assertFalse(self.members_tab.displays_invite())

    def test_manager_invite_admin(self):
        """Manager invite team, admin sees invite button. """

        self.team.membership_policy = 2
        self.team.save()
        self.members_tab.log_in(self.admin.username, 'password')
        self.members_tab.open_members_page(self.team.slug)
        self.assertTrue(self.members_tab.displays_invite())

    def test_manager_invite_manager(self):
        """Manager invite team, manager sees invite button. """
        self.team.membership_policy = 2
        self.team.save()
        self.members_tab.log_in(self.manager.username, 'password')
        self.members_tab.open_members_page(self.team.slug)
        self.assertTrue(self.members_tab.displays_invite())

    def test_manager_invite_member(self):
        """Manager invite team, member does not see invite button. """
        self.team.membership_policy = 2
        self.team.save()
        self.members_tab.log_in(self.member.username, 'password')
        self.members_tab.open_members_page(self.team.slug)
        self.assertFalse(self.members_tab.displays_invite())

    def test_all_invite_admin(self):
        """All invite team, admin sees invite button. """

        self.team.membership_policy = 3
        self.team.save()
        self.members_tab.log_in(self.admin.username, 'password')
        self.members_tab.open_members_page(self.team.slug)
        self.assertTrue(self.members_tab.displays_invite())

    def test_all_invite_manager(self):
        """All invite team, manager sees invite button. """
        self.team.membership_policy = 3
        self.team.save()
        self.members_tab.log_in(self.manager.username, 'password')
        self.members_tab.open_members_page(self.team.slug)
        self.assertTrue(self.members_tab.displays_invite())

    def test_all_invite_member(self):
        """All invite team, member sees invite button. """
        self.team.membership_policy = 3
        self.team.save()
        self.members_tab.log_in(self.member.username, 'password')
        self.members_tab.open_members_page(self.team.slug)
        self.assertTrue(self.members_tab.displays_invite())

    def test_open_invite_member(self):
        """Open team any member sees invite button. """
        self.team.membership_policy = 4
        self.team.save()
        self.members_tab.log_in(self.member.username, 'password')
        self.members_tab.open_members_page(self.team.slug)
        self.assertTrue(self.members_tab.displays_invite())

    def test_application_invite_admin(self):
        """In application-only team only admin sees invite button. """
        self.team.membership_policy = 1
        self.team.save()
        self.members_tab.log_in(self.admin.username, 'password')
        self.members_tab.open_members_page(self.team.slug)
        self.assertTrue(self.members_tab.displays_invite())

    def test_application_invite_manager(self):
        """In application-only team only manager does not see invite button. """
        self.team.membership_policy = 1
        self.team.save()
        self.members_tab.log_in(self.manager.username, 'password')
        self.members_tab.open_members_page(self.team.slug)
        self.assertFalse(self.members_tab.displays_invite())

    def test_application_invite_member(self):
        """In application-only team only member does not see invite button. """
        self.team.membership_policy = 1
        self.team.save()
        self.members_tab.log_in(self.member.username, 'password')
        self.members_tab.open_members_page(self.team.slug)
        self.assertFalse(self.members_tab.displays_invite())

    def test_delete_user_admin(self):
        """Admin can delete managers and contributors. """
        self.members_tab.log_in(self.admin.username, 'password')
        self.members_tab.member_search(self.member.username)
        self.assertTrue(self.members_tab.delete_user_link)
