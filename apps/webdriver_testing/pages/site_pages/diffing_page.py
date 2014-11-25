#!/usr/bin/env python
# -*- coding: utf-8 -*-

from webdriver_testing.pages.site_pages import UnisubsPage

class DiffingPage(UnisubsPage):
    """
     Revision diffing page

    """

    _URL = "videos/diffing/{0}/{1}/"  # format(rev1.id, rev2.id)
    _ROLLBACK = "div.left_column div.revision_buttons a.roll_back" 

    def open_diffing_page(self, rev1, rev2):
        self.open_page(self._URL.format(rev1, rev2))

    def rollback_exists(self):
        return self.is_element_present(self._ROLLBACK)

    def rollback(self):
        self.browser.execute_script("document.getElementsByClassName('roll_back')[0].click()")
        #self.click_by_css(self._ROLLBACK)
        self.handle_js_alert('accept')
        return self.success_message_present('Rollback successful')

