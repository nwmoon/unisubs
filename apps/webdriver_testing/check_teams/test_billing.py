# -*- coding: utf-8 -*-
import datetime
import csv
from collections import defaultdict
import time

from utils.factories import *
from webdriver_testing.webdriver_base import WebdriverTestCase
from webdriver_testing.data_factories import BillingFactory
from webdriver_testing.data_factories import TeamLangPrefFactory

from webdriver_testing import data_helpers
from webdriver_testing.pages.site_pages import billing_page


class TestCaseBilling(WebdriverTestCase):
    NEW_BROWSER_PER_TEST_CASE = False

    @classmethod
    def setUpClass(cls):
        super(TestCaseBilling, cls).setUpClass()
        cls.data_utils = data_helpers.DataHelpers()
        cls.billing_pg = billing_page.BillingPage(cls)
        cls.admin = UserFactory()
        cls.manager = UserFactory()
        cls.member = UserFactory()
        cls.team = TeamFactory(admin=cls.admin,
                               manager=cls.manager,
                               member=cls.member)

        cls.terri = UserFactory(is_staff=True, is_superuser=True)
        TeamMemberFactory(team=cls.team, user=cls.terri)
        cls.team = TeamMemberFactory.create(user = cls.user).team
        cls.video, cls.tv = cls._create_tv_with_original_subs(cls.user, cls.team)
        cls._upload_sv_translation(cls.video, cls.user, complete=True)

        cls.bill_dict = cls.create_team_bill()
        cls.billing_pg.open_billing_page()
        cls.billing_pg.log_in(cls.terri.username, 'password')


    @classmethod
    def create_team_bill(cls):
        report = BillingFactory( start_date=(datetime.date.today() - 
                                            datetime.timedelta(1)),
                                end_date=datetime.datetime.now(),
                                )
        report.teams=[cls.team]
        report.save()
        report.process()
        cls.bill = 'user-data/%s' % report.csv_file
        bill_dict = cls._bill_dict(cls.bill)
        return bill_dict


    @classmethod
    def _create_tv_with_original_subs(cls, user, team, complete=True):

        vid_data = {'primary_audio_language_code': 'en' }
        video = cls.data_utils.create_video(**vid_data)
        tv = TeamVideoFactory.create(
            team=team, 
            video=video, 
            added_by=user)

        data = {
                    'primary_audio_language_code': 'en',
                    'language_code': 'en',
                    'complete': int(complete), 
                    'is_complete': complete,
                    'video': video.pk,
                    'draft': open('apps/webdriver_testing/subtitle_data/Timed_text.en.srt')
                }
        cls.data_utils.upload_subs(user, **data)

        return video, tv

    @classmethod
    def _upload_sv_translation(cls, video, user, complete=False):

        data = {
                'language_code': 'sv',
                'from_language_code': 'en',
                'video': video.pk,
                'subtitles': open('apps/webdriver_testing/subtitle_data/'
                              'Timed_text.sv.dfxp'),
                'complete': complete}
        cls.data_utils.upload_subs(user, **data)

    @classmethod
    def _bill_dict(cls, bill_file):
        team_bill = defaultdict(dict)
        with open(bill_file, 'rb') as fp:
            reader = csv.DictReader(fp, dialect='excel')
            for rowdict in reader:
                video_id = rowdict.pop("Video ID")
                lang = rowdict.pop("Language")
                team_bill[video_id][lang] = rowdict 
        return dict(team_bill)

    def test_complete(self):
        """Complete team videos are billed.

        """

        self.assertEqual('3.0', 
                         self.bill_dict[self.video.video_id]['en']['Minutes'])


    def test_incomplete(self):
        """Incomplete languages have no billing record. """
        video, tv = self._create_tv_with_original_subs(self.member, self.team)
        inc_video, inc_tv = self._create_tv_with_original_subs(self.member, 
                                                               self.team, 
                                                               complete=False)

        report = BillingFactory(start_date=(datetime.date.today() - 
                                            datetime.timedelta(1)),
                                end_date=datetime.datetime.now(),
                                )
        report.teams=[self.team]
        report.save()

        report.process()
        bill = 'user-data/%s' % report.csv_file
        bill_dict = self._bill_dict(bill)
        self.assertNotIn(inc_video.video_id, bill_dict.keys())

    def test_primary_audio_language(self):
        """Primary audio lang true / false included in Original field.

        """
        self.assertEqual('True',
                         self.bill_dict[self.video.video_id]['en']['Original'])
        self.assertEqual('False',
                         self.bill_dict[self.video.video_id]['sv']['Original'])


    def test_translation__complete(self):
        """Billing record added for complete translations

        """
        self.assertIn('sv', self.bill_dict[self.video.video_id].keys())


    def test_minutes(self):
        """Minutes from last synced sub rounded up to whole minute.

        """
        self.assertEqual('3.0', 
                         self.bill_dict[self.video.video_id]['en']['Minutes'])


    def test_source(self):
        """Source of subs is listed in data (youtube, upload, api...)

        """
        self.assertEqual('upload', 
                         self.bill_dict[self.video.video_id]['en']['Source'])

    def test_user(self):
        """User credit with subtitles is listed in the record.

        """
        testuser = TeamMemberFactory.create().user
        video, tv = self._create_tv_with_original_subs(self.member, self.team)
        self._upload_sv_translation(video, testuser, complete=True)
        report = BillingFactory(start_date=(datetime.date.today() - 
                                            datetime.timedelta(1)),
                                end_date=datetime.datetime.now(),
                                )
        report.teams=[self.team]
        report.save()
        report.process()
        bill = 'user-data/%s' % report.csv_file
        bill_dict = self._bill_dict(bill)
        self.assertEqual(self.member.username, bill_dict[video.video_id]['en']['User'])
        self.assertEqual(testuser.username, bill_dict[video.video_id]['sv']['User'])


    def test_team(self):
        """Team is listed in the record.

        """
        self.assertEqual(self.team.slug, 
                         self.bill_dict[self.video.video_id]['en']['Team'])
    
    def test_created(self):
        """Data subtitles completed is listed in the record.

        """
        self.video.clear_language_cache()
        en = self.video.subtitle_language('en').get_tip(full=True)
        self.assertEqual(en.created.strftime("%Y-%m-%d %H:%M:%S"), 
                         self.bill_dict[self.video.video_id]['en']['Created'])

    def test_video(self):
        """Video id is listed in the record.

        """
        self.assertIn(self.video.video_id, self.bill_dict.keys())


    def test_delete_video(self):

        video1, tv1 = self._create_tv_with_original_subs(self.member, self.team)
        video, tv = self._create_tv_with_original_subs(self.member, self.team)
        video.delete()
        report = BillingFactory(start_date=(datetime.date.today() - 
                                            datetime.timedelta(1)),
                                end_date=datetime.datetime.now(),
                                )
        report.teams=[self.team]
        report.save()
        report.process()
        bill = 'user-data/%s' % report.csv_file
        bill_dict = self._bill_dict(bill)
        self.assertIn('deleted', bill_dict.keys())

    def test_crowd_billing_fields(self):
        video, tv = self._create_tv_with_original_subs(self.member, self.team)
        report = BillingFactory(start_date=(datetime.date.today() - 
                                            datetime.timedelta(1)),
                                end_date=datetime.datetime.now(),
                                )
        report.teams=[self.team]
        report.save()
        report.process()
        bill = csv.DictReader(open('user-data/%s' %report.csv_file))
        expected_fields = ['Video Title', 'Video ID', 'Language', 'Minutes', 
                           'Original', 'Language number', 'Team', 'Created', 'Source', 'User']
        self.assertEqual(expected_fields, bill.fieldnames)

    def test_download_crowd(self):
        """Data range of records downloaded to a csv file for a team.

        """
        for x in range(3):
            video, tv = self._create_tv_with_original_subs(self.member, self.team)
        self.billing_pg.open_billing_page()
        self.billing_pg.log_in(self.terri.username, 'password')
        self.billing_pg.open_billing_page()
        start = (datetime.date.today() - datetime.timedelta(7))
        end =  (datetime.date.today() + datetime.timedelta(2))

        self.billing_pg.submit_billing_parameters(self.team.name,
                                                  start.strftime("%Y-%m-%d"),
                                                  end.strftime("%Y-%m-%d"),
                                                  'Crowd sourced')
        report_dl = self.billing_pg.check_latest_report_url()
        new_headers = ['Language', 'Language number', 'Created', 'Video ID', 
                       'Video Title', 'Source', 'User', 'Team', 'Minutes', 
                       'Original']
        self.assertEqual(5, len(report_dl))
        self.assertEqual(new_headers, report_dl[0].keys())
     


    def test_download__multi_team_new(self):
        """Create a report for several teams.

        """

        team2_user = UserFactory.create()
        team2 = TeamMemberFactory.create(user = team2_user).team
        video2, tv2 = self._create_tv_with_original_subs(team2_user, team2)
        self._upload_sv_translation(video2, team2_user, complete=True)


        for x in range(3):
            self._create_tv_with_original_subs(team2_user, team2)

        self.billing_pg.open_billing_page()
        self.billing_pg.log_in(self.terri.username, 'password')
        self.billing_pg.open_billing_page()
        start = (datetime.date.today() - datetime.timedelta(7))
        end =  (datetime.date.today() + datetime.timedelta(2))
        team_names = ','.join([self.team.name, team2.name])
        self.billing_pg.submit_billing_parameters(team_names,
                                                  start.strftime("%Y-%m-%d"),
                                                  end.strftime("%Y-%m-%d"),
                                                  'Crowd sourced')
        report_dl = self.billing_pg.check_latest_report_url()
        new_headers = ['Language', 'Language number', 'Created', 'Video ID', 
                       'Video Title', 'Source', 'User', 'Team', 'Minutes', 
                       'Original']
        self.assertEqual(7, len(report_dl))
        self.assertEqual(new_headers, report_dl[0].keys())


class TestCaseDemandReports(WebdriverTestCase):
    NEW_BROWSER_PER_TEST_CASE = False

    @classmethod
    def setUpClass(cls):
        super(TestCaseDemandReports, cls).setUpClass()
        cls.data_utils = data_helpers.DataHelpers()
        cls.billing_pg = billing_page.BillingPage(cls)
        cls.terri = UserFactory.create(username='Terri', 
                                       is_staff=True, is_superuser=True)

        cls.owner = UserFactory.create()
        cls.team = cls.create_workflow_team()
        langs = ['ru', 'pt-br', 'de']
        for lc in langs:
            vid, tv = cls.create_tv_with_original_subs('en', cls.owner, cls.team)
            cls.data_utils.complete_review_task(tv, 20, cls.manager)
            cls.data_utils.complete_approve_task(tv, 20, cls.admin)
            cls.add_translation(lc, vid, cls.contributor, complete=True)
            cls.data_utils.complete_review_task(tv, 20, cls.contributor2)
            cls.data_utils.complete_approve_task(tv, 20, cls.admin)

    @classmethod
    def create_workflow_team(cls):
        team = TeamMemberFactory.create(team__workflow_enabled=True,
                                            team__translate_policy=20, #any team
                                            team__subtitle_policy=20, #any team
                                            team__task_assign_policy=10, #any team
                                            user = cls.owner,
                                            ).team
        cls.workflow = WorkflowFactory(team = team,
                                       autocreate_subtitle=True,
                                       autocreate_translate=True,
                                       approve_allowed = 10, # manager 
                                       review_allowed = 10, # peer
                                       )
        lang_list = ['en', 'ru', 'pt-br', 'de', 'sv']
        for language in lang_list:
            TeamLangPrefFactory.create(team=team, language_code=language,
                                       preferred=True)
        cls.contributor = TeamMemberFactory(role="ROLE_CONTRIBUTOR",team=team,
                                     user__first_name='Jerry', 
                                     user__last_name='Garcia',
                                     user__pay_rate_code='L2').user

        cls.contributor2 = TeamMemberFactory(role="ROLE_CONTRIBUTOR",
                team=team,
                user__first_name='Gabriel José de la Concordia'.decode("utf8"), 
                user__last_name='García Márquez'.decode("utf8")).user
        cls.admin = TeamMemberFactory(role="ROLE_ADMIN",team=team).user
        cls.manager = TeamMemberFactory(role="ROLE_MANAGER",team=team).user

        return team



    @classmethod
    def create_tv_with_original_subs(cls, lc, user, team, complete=True):
        sub_file = 'apps/webdriver_testing/subtitle_data/Timed_text.en.srt'
        video = VideoUrlFactory().video
        tv = TeamVideoFactory.create(
            team=team, 
            video=video, 
            added_by=user)
        data = {'language_code': lc,
                'video': video.pk,
                'primary_audio_language_code': lc,
                'draft': open(sub_file),
                'is_complete': complete,
                'complete': int(complete),
                }
        cls.data_utils.upload_subs(user, **data)
        return video, tv

    @classmethod
    def add_translation(cls, lc, video, user, complete=False):
        member_creds = dict(username=user.username, password='password')

        data = {'language_code': lc,
                'video': video.pk,
                'draft': open('apps/webdriver_testing/subtitle_data/'
                              'Timed_text.sv.dfxp'),
                'is_complete': complete,
                'complete': int(complete),}
        cls.data_utils.upload_subs(user, **data)

    @classmethod
    def _bill_dict(cls, bill_file):
        team_bill = defaultdict(dict)
        entries = []
        with open(bill_file, 'rb') as fp:
            reader = csv.DictReader(fp, dialect='excel')
            for rowdict in reader:
                entries.append(rowdict)
        return entries

    def test_translators_report(self):
        """Translator reports have rev and trnsltr entries for approved vids"""
        report = BillingFactory(type=4, 
                                start_date=(datetime.date.today() - 
                                            datetime.timedelta(1)),
                                end_date=datetime.datetime.now(),
                                )
        report.teams=[self.team]
        report.save()
        report.process()
        bill = 'user-data/%s' % report.csv_file
        entries = self._bill_dict(bill)
        self.assertEqual(18, len(entries))

    def test_professional_svcs_report(self):
        """Professional svcs report only contains approved videos."""
        report = BillingFactory(type=3, 
                                start_date=(datetime.date.today() - 
                                            datetime.timedelta(1)),
                                end_date=datetime.datetime.now(),
                                )
        report.teams=[self.team]
        report.save()
        report.process()
        bill = 'user-data/%s' % report.csv_file
        entries = self._bill_dict(bill)
        self.assertEqual(6, len(entries))


    def test_translator_report_values(self):
        """Check the content of translation team payment reports.
        
        Report should: 
        - display the video time as a decimal
        - contain separate entries for translator and reviewer
        - show the pay rate for translator and reviewer
        - contain True / False for original language
        - contain any reviewers notes.
        - list the approver, team, title and id.
        """

        team = self.create_workflow_team()
        vid, tv = self.create_tv_with_original_subs('en', self.owner, team)
        self.data_utils.complete_review_task(tv, 20, self.contributor)
        self.data_utils.complete_approve_task(tv, 20, self.admin)
        self.add_translation('de', vid, self.contributor2, complete=True)
        self.data_utils.complete_review_task(tv, 20, self.contributor, 
                                             note = 'Task shared with GabrielJosé') 

        self.data_utils.complete_approve_task(tv, 20, self.admin)
        report = BillingFactory(type=4, 
                                start_date=(datetime.date.today() - 
                                            datetime.timedelta(1)),
                                end_date=datetime.datetime.now(),
                                )
        report.teams=[team]
        report.save()
        report.process()
        bill = 'user-data/%s' % report.csv_file
        entries = self._bill_dict(bill)
        user_tasks = []
        unwanted_fields = ['Video ID', 'Team', 'Video Title', 'Approver', 'Date']
        for e in entries:
            [e.pop(x) for x in unwanted_fields]
            user_tasks.append(e)
        expected_translate_data = {  
                            'Task Type': 'Translate', 
                            'Language': 'de', 
                            'Minutes': '2.45015', 
                            'Pay Rate': '',
                            'Note': '', 
                            'User': ("Gabriel Jos\xc3\xa9 de la Concordia "
                                     "Garc\xc3\xada M\xc3\xa1rquez"),
                            'Original': 'False'
                          }

        expected_reviewer_data = {
                                   'Task Type': 'Review', 
                                   'Language': 'de', 
                                   'Minutes': '2.45015', 
                                   'Note': 'Task shared with Gabriel', 
                                   'User': " ".join([self.contributor.first_name, 
                                                     self.contributor.last_name]),
                                   'Pay Rate': 'L2',
                                   'Original': 'False',
                                   'Note': 'Task shared with GabrielJos\xc3\xa9'
                                 }
        self.assertIn(expected_translate_data, user_tasks)
        self.assertIn(expected_reviewer_data, user_tasks)

    def test_prof_services_report_values(self):
        """Check the content of professions services team billing reports.
        
        Report should: 
        - round the minutes up to the nearest whole number
        - contain the True / False for is translation
        - contain True / False for original language
        - contain the language code
        - list the approver
        """

        team = self.create_workflow_team()
        vid, tv = self.create_tv_with_original_subs('en', self.owner, team)
        self.data_utils.complete_review_task(tv, 20, self.contributor)
        self.data_utils.complete_approve_task(tv, 20, self.admin)
        self.add_translation('de', vid, self.contributor2, complete=True)
        self.data_utils.complete_review_task(tv, 20, self.contributor) 
        self.data_utils.complete_approve_task(tv, 20, self.admin)
        report = BillingFactory(type=3, 
                                start_date=(datetime.date.today() - 
                                            datetime.timedelta(1)),
                                end_date=datetime.datetime.now(),
                                )
        report.teams=[team, self.team]
        report.save()
        report.process()
        bill = 'user-data/%s' % report.csv_file
        entries = self._bill_dict(bill)
        team_data = []
        unwanted_fields = ['Video ID', 'Team', 'Video Title', 'Approver', 'Date']
        for e in entries:
            [e.pop(x) for x in unwanted_fields]
            team_data.append(e)
        expected_translation_data = {  
                                       'Translation?': 'True', 
                                       'Language': 'de', 
                                       'Minutes': '2.45015', 
                                       'Original': 'False'
                                    }

        expected_orig_lang_data = {
                                     'Translation?': 'False', 
                                     'Language': 'en', 
                                     'Minutes': '2.45015', 
                                     'Original': 'True'
                                  } 

        self.assertIn(expected_translation_data, team_data)
        self.assertIn(expected_orig_lang_data, team_data)

    def test_prof_services_no_review(self):
        """Profession services report generates when no review tasks.
        
        """
        team = self.create_workflow_team()
        wf  = team.get_workflow()
        wf.review_allowed = 0
        wf.save()
        
        vid, tv = self.create_tv_with_original_subs('en', self.owner, team)
        self.data_utils.complete_approve_task(tv, 20, self.admin)
        self.add_translation('de', vid, self.contributor2, complete=True)
        self.data_utils.complete_approve_task(tv, 20, self.admin)
        report = BillingFactory(type=3, 
                                start_date=(datetime.date.today() - 
                                            datetime.timedelta(1)),
                                end_date=datetime.datetime.now(),
                                )
        report.teams=[team, self.team]
        report.save()
        report.process()
        bill = 'user-data/%s' % report.csv_file
        entries = self._bill_dict(bill)
        # expect 6 entries from the main team + 2 entries from the no review team
        self.assertEqual(8, len(entries))

    def test_translators_no_review(self):
        """Translators report generates when no review tasks.
        
        """
        team = self.create_workflow_team()
        wf  = team.get_workflow()
        wf.review_allowed = 0
        wf.save()
        
        vid, tv = self.create_tv_with_original_subs('en', self.owner, team)
        self.data_utils.complete_approve_task(tv, 20, self.admin)

        self.add_translation('de', vid, self.contributor2, complete=True)
        self.data_utils.complete_approve_task(tv, 20, self.admin)
        report = BillingFactory(type=4, 
                                start_date=(datetime.date.today() - 
                                            datetime.timedelta(1)),
                                end_date=datetime.datetime.now(),
                                )
        report.teams=[team]
        report.save()
        report.process()
        bill = 'user-data/%s' % report.csv_file
        entries = self._bill_dict(bill)
        self.assertEqual(4, len(entries))

    def test_download_professional(self):
        """Check generation and download of professional services report.

        """
        self.billing_pg.open_billing_page()
        self.billing_pg.log_in(self.terri.username, 'password')
        self.billing_pg.open_billing_page()
        start = (datetime.date.today() - datetime.timedelta(7))
        end =  (datetime.date.today() + datetime.timedelta(2))
        self.billing_pg.submit_billing_parameters(
                                                  self.team.name,
                                                  start.strftime("%Y-%m-%d"),
                                                  end.strftime("%Y-%m-%d"),
                                                  'Professional services')
        report_dl = self.billing_pg.check_latest_report_url()
        self.assertEqual(6, len(report_dl))

    def test_download_translators(self):
        """Check generation download of on-demand translators report.

        """
        self.billing_pg.open_billing_page()
        self.billing_pg.log_in(self.terri.username, 'password')
        self.billing_pg.open_billing_page()
        start = (datetime.date.today() - datetime.timedelta(7))
        end =  (datetime.date.today() + datetime.timedelta(2))
        self.billing_pg.submit_billing_parameters(
                                                  self.team.name,
                                                  start.strftime("%Y-%m-%d"),
                                                  end.strftime("%Y-%m-%d"),
                                                  'On-demand translators')
        report_dl = self.billing_pg.check_latest_report_url()
        self.assertEqual(18, len(report_dl))
