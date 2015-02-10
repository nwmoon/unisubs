# -*- coding: utf-8 -*-
from django.core import mail
import time
from django.core import management
from teams import tasks
from teams.models import TeamMember
from teams.models import Team

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
        cls.admin = UserFactory()
        cls.manager = UserFactory()
        cls.member = UserFactory(notify_by_email=True, is_active=True)
        cls.team1 = TeamFactory(admin=cls.admin,
                               manager=cls.manager,
                               member=cls.member)

        cls.team2 = TeamFactory(admin=cls.admin,
                               manager=cls.manager,
                               member=cls.member)
        cls.users = {
                      #username, langauges-spoken
                      'en_only': ['en'],
                      'en_fr': ['en', 'fr'],
                      'pt_br_fr_de': ['pt-br', 'fr', 'de'],
                      'fil': ['fil'],
                      'de_en': ['de', 'en'],
                      'fr_fil': ['fil', 'fr'],
                    }
        for username, langs in cls.users.iteritems():
            setattr(cls, username, UserFactory(username=username))
            for lc in langs:
                UserLangFactory(user=getattr(cls, username), language=lc)

        #set the team 1 contributors 
        TeamMemberFactory(user=cls.de_en, team=cls.team1,
                          role=TeamMember.ROLE_MANAGER)
        TeamMemberFactory(user=cls.en_only, team=cls.team1,
                          role=TeamMember.ROLE_ADMIN)
        TeamMemberFactory(user=cls.en_fr, team=cls.team1,
                          role=TeamMember.ROLE_ADMIN)
        TeamMemberFactory(user=cls.pt_br_fr_de, team=cls.team1,
                          role=TeamMember.ROLE_CONTRIBUTOR)
        TeamMemberFactory(user=cls.fil, team=cls.team1,
                          role=TeamMember.ROLE_CONTRIBUTOR)

        #set the team 2 contributors 
        TeamMemberFactory(user=cls.en_only, team=cls.team2,
                          role=TeamMember.ROLE_ADMIN)
        TeamMemberFactory(user=cls.de_en, team=cls.team2,
                          role=TeamMember.ROLE_ADMIN)
        TeamMemberFactory(user=cls.en_fr, team=cls.team2,
                          role=TeamMember.ROLE_CONTRIBUTOR)
        TeamMemberFactory(user=cls.pt_br_fr_de, team=cls.team2,
                          role=TeamMember.ROLE_CONTRIBUTOR)
        TeamMemberFactory(user=cls.fr_fil, team=cls.team2,
                          role=TeamMember.ROLE_CONTRIBUTOR)

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
        self.assertEqual(7, len(mail.outbox))
   

    def test_large_team_message(self):
        """Message all team members"""
        for x in range(0,20):
            TeamMemberFactory.create(role=TeamMember.ROLE_CONTRIBUTOR,
                                     team=self.team2)
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
        'NEW_MEMBER': ('You are now on our team, Welcome!')
        }

    @classmethod
    def setUpClass(cls):
        super(TestCaseTeamMessages, cls).setUpClass()
        cls.data_utils = data_helpers.DataHelpers()
        cls.a_team_pg = ATeamPage(cls)
        cls.members_tab = members_tab.MembersTab(cls)
        cls.messages_tab = messages_tab.MessagesTab(cls)
        cls.user_message_pg = user_messages_page.UserMessagesPage(cls)
        cls.non_member = UserFactory()
        cls.admin = UserFactory()
        cls.manager = UserFactory()
        cls.member = UserFactory()

        cls.team = TeamFactory(admin=cls.admin,
                               manager=cls.manager,
                               member=cls.member,
                               )
        cls.team.membership_policy = 1
        cls.team.save()

        #ADD THE TEST MESSAGES TO THE TEST TEAM
        cls.members_tab.open_members_page(cls.team.slug)
        cls.members_tab.log_in(cls.admin.username, 'password')
        cls.messages_tab.open_messages_tab(cls.team.slug)
        cls.messages_tab.edit_messages(cls._TEST_MESSAGES)


    def test_videos_added_hourly(self):
        """check emails sent with hourly setting for videos added"""
        team = TeamFactory(admin=self.admin,
                           manager=self.manager,
                           member=self.member,
                           notify_interval = Team.NOTIFY_HOURLY)
        for x in range(0,5):
            video = VideoFactory()
            TeamVideoFactory(video=video, team=team) 
        management.call_command('update_index', interactive=False)
        mail.outbox = []
        tasks.add_videos_notification_hourly.apply()
        time.sleep(2)
        msg = str(mail.outbox[-1].message())
        self.assertIn('team has added new videos, and they need your help:', 
                      msg)
        for x in mail.outbox:
            self.logger.info(x.to)
        self.assertEqual(8,len(mail.outbox))

    def test_videos_added_daily(self):
        """check email sent with daily setting for videos added"""
        team2 = TeamFactory(admin=self.admin,
                            manager=self.manager,
                            member=self.member,
                            notify_interval = Team.NOTIFY_DAILY)
        video = VideoFactory()
        TeamVideoFactory(video=video, team=team2) 
        management.call_command('update_index', interactive=False)
        mail.outbox = []
        tasks.add_videos_notification_daily.apply()
        time.sleep(5)
        self.logger.info(len(mail.outbox))
        msg = str(mail.outbox[-1].message())
        self.logger.info(msg)
        self.assertIn('team has added new videos, and they need your help:', 
                      msg)


    def test_message_new_user(self):
        """message sent when user joins the team."""
        joiner = UserFactory()
        langs = ['en', 'cs', 'ru', 'ar']
        for lc in langs:
            UserLangFactory(user=joiner, language=lc)
        self.a_team_pg.log_in(joiner.username, 'password')
        mail.outbox = []
        self.a_team_pg.open_team_page(self.team.slug)
        self.a_team_pg.join()
        msg = str(mail.outbox[-1].message())
        self.logger.info(msg)
        self.assertIn(self._TEST_MESSAGES["NEW_MEMBER"], 
                      msg)

        
    def test_messages_edit(self):
        """Change the default messages via the UI and verify they are stored.

        """
        self.members_tab.log_in(self.admin.username, 'password')
        self.messages_tab.open_messages_tab(self.team.slug)

        self.assertEqual(self._TEST_MESSAGES, 
            self.messages_tab.stored_messages())

    def test_messages_invitation(self):
        """Invited user see the custom message.  """
        self.members_tab.log_in(self.admin.username, 'password')
        self.messages_tab.open_messages_tab(self.team.slug)

        self.members_tab.open_members_page(self.team.slug)
        self.members_tab.invite_user_via_form(
            user = self.non_member,
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
            self.member.username)
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
            self.member.username)
        self.members_tab.edit_user(role="Manager")

        #Verify the user gets the message displayed.
        self.user_message_pg.log_in(self.non_member.username, 'password')
        self.user_message_pg.open_messages()
        self.assertTrue(self._TEST_MESSAGES['NEW_MANAGER'] in 
            self.user_message_pg.message_text())
 
