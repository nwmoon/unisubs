#!/usr/bin/env python
import time
import os
from urlparse import urlparse
import csv
from collections import defaultdict
from webdriver_testing.pages.site_pages import UnisubsPage
import requests

class BillingPage(UnisubsPage):
    """Billing page, available only to is_superuser users.

    """

    _URL = "admin/billing/"
    _TEAM = "ul li label"
    _START = "input#id_start_date"
    _END = "input#id_end_date"
    _TYPE = "select#id_type"
    _SUBMIT = "button.green_button"
    _LATEST_REPORT = "tbody tr:nth-child(1) td:nth-child(6) a"

    def open_billing_page(self):
        self.open_page(self._URL)


    def submit_billing_parameters(self, team, start, end, bill_type):
        teams = team.split(',')
        boxes = self.get_elements_list(self._TEAM)
        for b in boxes:
            if b.text in teams:
                b.find_element_by_css_selector('input').click()
        self.type_by_css(self._START, start)
        self.type_by_css(self._END, end)
        self.select_option_by_text(self._TYPE, bill_type)
        self.submit_by_css(self._SUBMIT)

    def check_latest_report_url(self):
        url = self.get_element_attribute(self._LATEST_REPORT, 'href')
        filename = urlparse(url).path.split('/')[-1]
        report = os.path.join(os.getcwd(), 'user-data', 'teams', 'billing', filename)
        entries = []
        with open(report, 'rb') as fp:
            reader = csv.DictReader(fp, dialect='excel')
            for rowdict in reader:
                entries.append(rowdict)
        return entries



        return report
