import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from api_client.betting_api import BettingAPIClient
from config import HEADLESS, IMPLICIT_WAIT_SECONDS


@pytest.fixture
def driver():
    options = Options()
    if HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,900")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    chrome_driver = webdriver.Chrome(options=options)
    chrome_driver.implicitly_wait(IMPLICIT_WAIT_SECONDS)
    yield chrome_driver
    chrome_driver.quit()


@pytest.fixture
def api_client() -> BettingAPIClient:
    return BettingAPIClient()


@pytest.fixture
def reset_balance(api_client: BettingAPIClient):
    """Ensures each test starts from a known balance, and cleans up after itself.
    Runs reset both before and after so a failed test doesn't poison the next one."""
    api_client.reset_balance()
    yield
    api_client.reset_balance()
