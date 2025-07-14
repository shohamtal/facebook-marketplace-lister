from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from Helpers import read_json, write_json, format_xpath
from locales import Locale


class Element:
    def __init__(self, driver, name, values = None, locale:Locale=Locale.Hebrew):
        self.driver = driver
        self.name = name
        self.values = values
        self.pathes = read_json(f'elements-{locale.value}')
    @property
    def xpath(self):
        xpath_format = self.pathes[self.name]['xpath']
        defaults = self.defaults
        return format_xpath(xpath_format, self.values) if self.values else format_xpath(xpath_format, defaults)
    @property
    def defaults(self):
        return self.pathes[self.name]['defaults']
    @property
    def element(self):
        xpath = self.xpath
        element_type = self.pathes[self.name]['type']
        if element_type == 'button' :
            element = WebDriverWait(self.driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
            )
        else:
            element = self.driver.find_element(By.XPATH, xpath)
        return element

