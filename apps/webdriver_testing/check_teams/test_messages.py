# -*- coding: utf-8 -*-
from django.core import mail
import time

from teams import tasks
from webdriver_testing.webdriver_base import WebdriverTestCase
from webdriver_testing.pages.site_pages.teams import ATeamPage
from webdriver_testing.pages.site_pages.teams import messages_tab
from webdriver_testing.pages.site_pages.teams import members_tab
from webdriver_testing.pages.site_pages import user_messages_page
from webdriver_testing.pages.site_pages import new_message_page
from webdriver_testing.data_factories import *
from webdriver_testing import data_helpers

class TestCaseMessageUsers(WebdriverTestCase):
    """Team admin can send bulk messages to members.  """
    NEW_BROWSER_PER_TEST_CASE = False

    @classmethod
    def setUpClass(cls):
        super(TestCaseMessageUsers, cls).setUpClass()

        cls.user_message_pg = user_messages_page.UserMessagesPage(cls)
        cls.new_message_pg = new_message_page.NewMessagePage(cls)
        cls.data_utils = data_helpers.DataHelpers()
        cls.team_owner1 = UserFactory(username='owner1')
        cls.team_owner2 = UserFactory(username='owner2')
        cls.team1 = TeamMemberFactory.create(user=cls.team_owner1).team
        cls.team2 = TeamMemberFactory.create(user=cls.team_owner2).team
        cls.logger.info('setup: Create users')
        cls.users = {
                      #username, langauges-spoken
                      'en_only': ['en'],
                      'en_fr': ['en', 'fr'],
                      'pt_br_fr_de': ['pt-br', 'fr', 'de'],
                      'fil': ['fil'],
                      'de_en': ['de', 'en'],
                      'fr_fil': ['fil', 'fr'],
                    }
        cls.team1_managers = ['de_en'] 
        cls.team1_admins = ['en_only', 'en_fr']
        cls.team1_contributors = ['pt_br_fr_de', 'fil']
        cls.team2_admins = ['en_only', 'de_en']
        cls.team2_contributors = ['en_fr', 'pt_br_fr_de', 'fr_fil']



        for username, langs in cls.users.iteritems():
            setattr(cls, username, UserFactory(username=username))
            for lc in langs:
                UserLangFactory(user=getattr(cls, username), language=lc)

        #set the team 1 admins
        for u in cls.team1_admins:
            user = getattr(cls, u)
            TeamMemberFactory.create(
                                     role='ROLE_ADMIN',
                                     team=cls.team1,
                                     user=user)

        #set the team 1 manager 
        for u in cls.team1_managers:
            user = getattr(cls, u)
            TeamMemberFactory.create(
                                     role='ROLE_MANAGER',
                                     team=cls.team1,
                                     user=user)
        #set the team 1 contributors 
        for u in cls.team1_contributors:
            user = getattr(cls, u)
            TeamMemberFactory.create(
                                     role='ROLE_CONTRIBUTOR',
                                     team=cls.team1,
                                     user=user)
        #set the team 2 admins   
        for u in cls.team2_admins:
            user = getattr(cls, u)
            TeamMemberFactory.create(
                                     role='ROLE_ADMIN',
                                     team=cls.team2,
                                     user=user)


        #set the team 2 contributors 
        for u in cls.team2_contributors:
            user = getattr(cls, u)
            TeamMemberFactory.create(
                                     role='ROLE_CONTRIBUTOR',
                                     team=cls.team2,
                                     user=user)

        cls.new_message_pg.open_page("/")
         
    def test_admins_team_list(self):
        "Team list limited to team admins only"
        self.new_message_pg.log_in(self.en_only.username, 'password')
        self.new_message_pg.open_new_message_form()
        en_only_teams = [self.team1.name, self.team2.name]
        self.assertEqual(en_only_teams, self.new_message_pg.available_teams())
        en_fr_teams = [self.team1.name]
        self.new_message_pg.log_in(self.en_fr.username, 'password')
        self.new_message_pg.open_new_message_form()
        self.assertEqual(en_fr_teams, self.new_message_pg.available_teams())
        

    def test_managers_team_list(self):
        "Managers can not message whole team"
        self.new_message_pg.log_in(self.de_en.username, 'password')
        self.new_message_pg.open_new_message_form()
        de_en_teams = [self.team2.name]
        self.assertEqual(de_en_teams, self.new_message_pg.available_teams())

    def test_contributors_no_team_option(self):
        """Contributors only don't see team message pulldown"""

        self.new_message_pg.log_in(self.pt_br_fr_de.username, 'password')
        self.new_message_pg.open_new_message_form()
        self.assertFalse(self.new_message_pg.available_teams())

    def test_team_language_message(self):
        """Message users speaking a specific language"""
        self.new_message_pg.log_in(self.en_only.username, 'password')
        self.new_message_pg.open_new_message_form()
        mail.outbox = []
        self.new_message_pg.add_subject("To all German speaking test team 1")
        self.new_message_pg.add_message("you rock!")
        self.new_message_pg.choose_team(self.team1.name)
        self.new_message_pg.choose_language('German')
        self.new_message_pg.send()
        self.assertTrue(self.new_message_pg.sent())
        messages = mail.outbox
        self.assertTrue(2, len(mail.outbox))
        message_recipients = []
        for m in mail.outbox:
            message_recipients.append(m.recipients()[0].split('@')[0])
        expected_recipients = ['de_en', 'pt_br_fr_de']
        self.assertEqual(sorted(expected_recipients), sorted(message_recipients))
     

    def test_whole_team_message(self):
        """Message all team members"""
        self.new_message_pg.log_in(self.de_en.username, 'password')
        self.new_message_pg.open_new_message_form()
        mail.outbox = []
        self.new_message_pg.add_subject("To all test team 2")
        self.new_message_pg.add_message("you rock!")
        self.new_message_pg.choose_team(self.team2.name)
        self.new_message_pg.send()
        self.assertTrue(self.new_message_pg.sent())
        messages = mail.outbox
        self.assertEqual(5, len(mail.outbox))
        message_recipients = []
        for m in mail.outbox:
            message_recipients.append(m.recipients()[0].split('@')[0])
        expected_recipients = ['owner2', 'en_only', 'en_fr', 'pt_br_fr_de', 'fr_fil']
        self.assertEqual(sorted(expected_recipients), sorted(message_recipients))



   

    def test_large_team_message(self):
        """Message all team members"""
        for x in range(0,20):
            TeamMemberFactory.create(role='ROLE_CONTRIBUTOR',
                                     team=self.team2,
                                     user=UserFactory.create())
        self.new_message_pg.log_in(self.de_en.username, 'password')
        self.new_message_pg.open_new_message_form()
        mail.outbox = []
        self.new_message_pg.add_subject("To all test team 2")
        self.new_message_pg.add_message("you rock!")
        self.new_message_pg.choose_team(self.team2.name)
        start = time.clock()
        self.new_message_pg.send()
        self.assertTrue(self.new_message_pg.sent())
        elapsed = (time.clock() - start)
        self.assertLess(elapsed, 10)
        self.user_message_pg.open_sent_messages()
        self.assertTrue(self.user_message_pg.message_subject(), 'To all test team 2')


    def test_user_selected_disables_team(self):
        """Choosing to message a user, disables team selections."""
        self.new_message_pg.log_in(self.en_only.username, 'password')
        self.new_message_pg.open_new_message_form()
        mail.outbox = []
        self.new_message_pg.add_subject("To de_en")
        self.new_message_pg.add_message("you rock!")
        self.new_message_pg.choose_user('de_en')
        self.assertTrue(self.new_message_pg.team_choice_disabled())
        self.assertTrue(self.new_message_pg.lang_choice_disabled())
        self.new_message_pg.send()
        self.assertTrue(self.new_message_pg.sent())
        messages = mail.outbox
        message_recipients = []
        for m in mail.outbox:
            message_recipients.append(m.recipients()[0].split('@')[0])
        expected_recipients = ['de_en']
        self.assertEqual(expected_recipients, message_recipients)

class TestCaseTeamMessages(WebdriverTestCase):
    """TestSuite for searching team videos """
    NEW_BROWSER_PER_TEST_CASE = False
    _TEST_MESSAGES = {
        'INVITATION': ('I hear you are an awesome translator, please join '
                       'my team.'),
        'APPLICATION': ('Thank you for applying to the team, we will review ' 
                        'your qualifications and get back to you.'),
        'NEW_MANAGER': ('Congrats, you have been promoted to Manager.'),
        'NEW_ADMIN': ('Congrats, you have been promoted to Admin status.'),
        'NEW_MEMBER': ('We have approved your application.  Welcome!')
        }

    @classmethod
    def setUpClass(cls):
        super(TestCaseTeamMessages, cls).setUpClass()
        cls.data_utils = data_helpers.DataHelpers()
        cls.a_team_pg = ATeamPage(cls)
        cls.members_tab = members_tab.MembersTab(cls)
        cls.messages_tab = messages_tab.MessagesTab(cls)
        cls.user_message_pg = user_messages_page.UserMessagesPage(cls)
        cls.non_member = UserFactory.create(username='NonMember')
        cls.team_owner = UserFactory.create(is_partner = True)

        #CREATE AN APPLICATION-ONLY TEAM 
        cls.team = TeamMemberFactory.create(
            team__membership_policy = 1,
            user = cls.team_owner,
            ).team

        cls.team_member = TeamMemberFactory.create(role="ROLE_CONTRIBUTOR",
                                           user=UserFactory(),
                                           team=cls.team).user

        #ADD THE TEST MESSAGES TO THE TEST TEAM
        cls.members_tab.open_members_page(cls.team.slug)
        cls.members_tab.log_in(cls.team_owner.username, 'password')
        cls.messages_tab.open_messages_tab(cls.team.slug)
        cls.messages_tab.edit_messages(cls._TEST_MESSAGES)


    def test_videos_added_hourly(self):
        """check emails sent with hourly setting for videos added"""
        TeamMemberFactory(role="ROLE_CONTRIBUTOR",
                                           user=UserFactory(),
                                           team=self.team)

        for x in range(0,5):
            video = TeamVideoFactory.create(
                    team=self.team, 
                    video=self.data_utils.create_video())
        mail.outbox = []
        tasks.add_videos_notification_hourly.apply()
        msg = str(mail.outbox[-1].message())
        self.assertIn('team has added new videos, and they need your help:', 
                      msg)
        for x in mail.outbox:
            self.logger.info(x.message())
        self.assertEqual(3,len(mail.outbox))

    def test_videos_added_daily(self):
        """check email sent with daily setting for videos added"""
        team2 = TeamMemberFactory(team__notify_interval='NOTIFY_DAILY').team
        mail.outbox = []
        video = TeamVideoFactory.create(
                team=team2, 
                video=self.data_utils.create_video())
        
        tasks.add_videos_notification_daily.apply()
        msg = str(mail.outbox[-1].message())
        self.logger.info(msg)
        self.assertIn('team has added new videos, and they need your help:', 
                      msg)


    def test_message_new_user(self):
        """message sent when user joins the team."""
        member = UserFactory()
        langs = ['en', 'cs', 'ru', 'ar']
        for lc in langs:
            UserLangFactory(user = member,
                            language = lc)
        self.members_ 
        
    def test_messages_edit(self):
        """Change the default messages via the UI and verify they are stored.

        """
        self.members_tab.log_in(self.team_owner.username, 'password')
        self.messages_tab.open_messages_tab(self.team.slug)

        self.assertEqual(self._TEST_MESSAGES, 
            self.messages_tab.stored_messages())

    def test_messages_invitation(self):
        """Invited user see the custom message.  """
        self.members_tab.log_in(self.team_owner.username, 'password')
        self.messages_tab.open_messages_tab(self.team.slug)

        self.members_tab.open_members_page(self.team.slug)
        self.members_tab.invite_user_via_form(
            username = self.non_member.username,
            message = 'Join my team',
            role = 'Contributor')

        #Verify the user gets the message displayed.
        self.user_message_pg.log_in(self.non_member.username, 'password')
        self.user_message_pg.open_messages()
        self.assertTrue(self._TEST_MESSAGES['INVITATION'] in 
            self.user_message_pg.message_text())

    def test_messages_application(self):
        """Custom message for user application.

        """
        self.user_message_pg.log_in(self.non_member.username, 'password')
        self.a_team_pg.open_team_page(self.team.slug)
        self.a_team_pg.apply()
        self.assertTrue(self._TEST_MESSAGES['APPLICATION'] in 
            self.a_team_pg.application_custom_message())

    def test_messages_promoted_admin(self):
        """Message for user promoted to admin.

        """
        self.skipTest('needs bugs fixed: i1541 and i438')
        self.members_tab.member_search(self.team.slug,
            self.team_member.username)
        self.members_tab.edit_user(role="Admin")

        #Verify the user gets the message displayed.
        self.user_message_pg.log_in(self.non_member.username, 'password')
        self.user_message_pg.open_messages()
        self.assertTrue(self._TEST_MESSAGES['NEW_ADMIN'] in 
            self.user_message_pg.message_text())

    def test_messages_promoted_manager(self):
        """Message for user promoted to manager.

        """
        self.skipTest('needs bugs fixed: i1541 and i438')
        self.members_tab.member_search(self.team.slug,
            self.team_member.username)
        self.members_tab.edit_user(role="Manager")

        #Verify the user gets the message displayed.
        self.user_message_pg.log_in(self.non_member.username, 'password')
        self.user_message_pg.open_messages()
        self.assertTrue(self._TEST_MESSAGES['NEW_MANAGER'] in 
            self.user_message_pg.message_text())
 
