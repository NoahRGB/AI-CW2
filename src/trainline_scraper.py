import re

from time import sleep

from date_time import DateTime
from ticket_types import TicketTypes

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver import Keys, ActionChains

class TrainlineScraper:
    # queries the trainline website (https://www.thetrainline.com/) for the
    # specified train journey and finds the cheapest ticket with the given options

    def __init__(self):
        options = Options()
        options.add_argument("--log-level=3")
        # headless means that a browser window won't actually open and it will do it in the background instead
        # options.add_argument("--headless=new")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36")
        self.browser = Chrome(options=options)
        self.actions = ActionChains(self.browser)
        self.ticket_type = None
        self.url = (f"https://www.thetrainline.com/")
        self.url_additions = ""
        
        
    def clear_cookies_popup(self):
        # keeps looking for the cookies popup and then accepts it once it exists
        cookies_button = self.browser.find_elements(By.ID, "onetrust-accept-btn-handler")
        while len(cookies_button) == 0:
            cookies_button = self.browser.find_elements(By.ID, "onetrust-accept-btn-handler")
        cookies_button[0].click()
        sleep(1)
        
    def set_origin_input(self, origin_station):
        sleep(1)
        origin_box = self.browser.find_elements(By.ID, "jsf-origin-input")
        if len(origin_box) > 0:
            origin_box[0].send_keys(origin_station)
            sleep(1)
            origin_box[0].send_keys(Keys.RETURN)
            
    def set_destination_input(self, destination_station):
        sleep(1)
        destination_box = self.browser.find_elements(By.ID, "jsf-destination-input")
        if len(destination_box) > 0:
            destination_box[0].send_keys(destination_station)
            sleep(1)
            destination_box[0].send_keys(Keys.RETURN)
    
    def set_ticket_type(self, ticket_type):
        ticket_type_box = None
        if ticket_type == TicketTypes.RETURN:
            ticket_type_box = self.browser.find_elements(By.ID, "return")
        else:
            ticket_type_box = self.browser.find_elements(By.ID, "single")
        
        sleep(1)
        if len(ticket_type_box) > 0:
            ticket_type_box[0].click()
            
    def set_ticket_counts(self, adult_count, child_count):
        sleep(1)
        toggle = self.browser.find_element(By.ID, "jsf-passengers-input-toggle")
        toggle.click()
        
        plus_buttons = self.browser.find_elements(By.CSS_SELECTOR, "button[data-testid='incrementButton']")
        for plus in plus_buttons:
            if "adult" in plus.accessible_name:
                for i in range(0, adult_count - 1):
                    sleep(1)
                    plus.click()
            elif "child" in plus.accessible_name:
                for i in range(0, child_count):
                    sleep(1)
                    plus.click()
                    age_dropdown = self.browser.find_element(By.ID, f"child-age-dropdown-{i}")
                    sleep(1)
                    age_dropdown.click()
                    age = age_dropdown.find_element(By.CSS_SELECTOR, "option[value='15']")
                    sleep(1)
                    age.click()
        
                    
            
    def search_for_journey(self):
        sleep(1)
        promo_box = self.browser.find_element(By.ID, "bookingPromo")
        promo_box.click()
        submit_box = self.browser.find_element(By.CSS_SELECTOR, "button[data-testid='jsf-submit']")
        sleep(1)
        submit_box.click()
        sleep(2)
        
   
    def __del__(self):
        self.browser.close()

    def launch_scraper(self):
        self.browser.get(self.url)
        
if __name__ == "__main__": 
    scraper = TrainlineScraper()
    scraper.launch_scraper()
    scraper.clear_cookies_popup()
    scraper.set_origin_input("Colchester")
    scraper.set_destination_input("Norwich")
    scraper.set_ticket_type(TicketTypes.RETURN)
    scraper.set_ticket_counts(2, 3)
    scraper.search_for_journey()


    input()
