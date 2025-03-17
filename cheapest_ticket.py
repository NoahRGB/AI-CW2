
from time import sleep

import requests
from bs4 import BeautifulSoup

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver import Keys, ActionChains

class NationalRailScraper:
    def __init__(self):
        options = Options()
        self.browser = Chrome(options=options)
        self.browser.get("https://www.nationalrail.co.uk/")
        self.actions = ActionChains(self.browser)
    
    def __del__(self):
        self.browser.close()

    def clear_cookies_popup(self):
        # looks for cookies accept button until it exists
        cookies_button = self.browser.find_elements(By.ID, "onetrust-accept-btn-handler")
        while len(cookies_button) == 0:
            cookies_button = self.browser.find_elements(By.ID, "onetrust-accept-btn-handler")

        cookies_button[0].click()
        sleep(1)
    
    def launch_journey_box(self):
        # clicks the button to launch the journey planner on the homepage
        initial_button = self.browser.find_element(By.CSS_SELECTOR, "button[data-testid='jp-preview-btn']")
        initial_button.click()  
        sleep(1)
    
    def set_stations(self, origin, destination):
        # adds the origin and destination stations to the relevant boxes in the journey planner box
        origin_input = self.browser.find_element(By.ID, "jp-origin")
        destination_input = self.browser.find_element(By.ID, "jp-destination")

        origin_input.send_keys(origin)
        self.press_enter();
        destination_input.send_keys(destination)

        sleep(1)

    def press_enter(self):
        self.actions.key_down(Keys.ENTER).perform()
 

scraper = NationalRailScraper()

scraper.clear_cookies_popup()
scraper.launch_journey_box()
scraper.set_stations("NRW", "IPS")


input()
