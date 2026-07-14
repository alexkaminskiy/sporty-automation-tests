"""Base page object: shared explicit-wait helpers.

Design note: implicit + explicit waits are never mixed (config.IMPLICIT_WAIT_SECONDS = 0)
because Selenium applies implicit waits to every findElement call including ones inside an
explicit WebDriverWait poll loop, which silently multiplies timeouts and makes failures slow
and hard to diagnose.
"""
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from config import EXPLICIT_WAIT_SECONDS


class BasePage:
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.wait = WebDriverWait(driver, EXPLICIT_WAIT_SECONDS)

    def find(self, locator: tuple[str, str]) -> WebElement:
        return self.wait.until(EC.presence_of_element_located(locator))

    def find_clickable(self, locator: tuple[str, str]) -> WebElement:
        return self.wait.until(EC.element_to_be_clickable(locator))

    def find_all(self, locator: tuple[str, str]) -> list[WebElement]:
        return self.wait.until(EC.presence_of_all_elements_located(locator))

    def wait_until_visible(self, locator: tuple[str, str]) -> WebElement:
        return self.wait.until(EC.visibility_of_element_located(locator))

    def wait_until_gone(self, locator: tuple[str, str]) -> bool:
        return self.wait.until(EC.invisibility_of_element_located(locator))

    def wait_until_text_changes(self, locator: tuple[str, str], old_text: str) -> bool:
        return self.wait.until(lambda d: d.find_element(*locator).text != old_text)

    def text_of(self, locator: tuple[str, str]) -> str:
        return self.find(locator).text.strip()
