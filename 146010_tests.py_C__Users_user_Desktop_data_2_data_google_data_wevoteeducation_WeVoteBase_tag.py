# tag/tests.py
# Brought to you by We Vote. Be good.
# -*- coding: UTF-8 -*-

from django.test import LiveServerTestCase
from selenium.webdriver.firefox.webdriver import WebDriver

from tag.models import Tag


class TagIntegrationTests(LiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        cls.selenium = WebDriver()
        super(TagIntegrationTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(TagIntegrationTests, cls).tearDownClass()

    # TODO Build out these tests
    # http://www.effectivedjango.com/tutorial/views.html
    # def test_contact_listed(self):
    #
    #     # create a test contact
    #     Tag.objects.create(first_name='foo', last_name='bar')
    #
    #     # make sure it's listed as <first> <last> on the list
    #     self.selenium.get('%s%s' % (self.live_server_url, '/'))
    #     self.assertEqual(
    #         self.selenium.find_elements_by_css_selector('.contact')[0].text,
    #         'foo bar'
    #     )
    #
    # def test_add_contact_linked(self):
    #
    #     self.selenium.get('%s%s' % (self.live_server_url, '/'))
    #     self.assert_(
    #         self.selenium.find_element_by_link_text('add contact')
    #     )
    #
    # def test_add_contact(self):
    #
    #     self.selenium.get('%s%s' % (self.live_server_url, '/'))
    #     self.selenium.find_element_by_link_text('add contact').click()
    #
    #     self.selenium.find_element_by_id('id_first_name').send_keys('test')
    #     self.selenium.find_element_by_id('id_last_name').send_keys('contact')
    #     self.selenium.find_element_by_id('id_email').send_keys('test@example.com')
    #
    #     self.selenium.find_element_by_id("save_contact").click()
    #     self.assertEqual(
    #         self.selenium.find_elements_by_css_selector('.contact')[-1].text,
    #         'test contact'
    #     )