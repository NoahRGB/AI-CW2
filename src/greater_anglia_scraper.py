import re

from time import sleep

from date_time import DateTime
from ticket_types import TicketTypes

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver import Keys, ActionChains

class GreaterAngliaScraper:
    # queries the greater anglia website (https://www.greateranglia.co.uk/) for the
    # specified train journey and finds the cheapest ticket with the given options

    def __init__(self):
        options = Options()
        options.add_argument("--log-level=3")
        # headless means that a browser window won't actually open and it will do it in the background instead
        options.add_argument("--headless=new")
    #       options.addArguments("--headless");

        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36")

    # options.addArguments("user-agent=Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36");
        self.browser = Chrome(options=options)
        self.actions = ActionChains(self.browser)
        self.ticket_type = None
        self.url = (f"https://www.greateranglia.co.uk/")
        self.url_additions = ""

    def __del__(self):
        self.browser.close()
        
    def clear_cookies_popup(self):
        # keeps looking for the cookies popup and then accepts it once it exists
        cookies_button = self.browser.find_elements(By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll")
        while len(cookies_button) == 0:
            cookies_button = self.browser.find_elements(By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll")
        cookies_button[0].click()
        sleep(1)
        
    def set_origin_station(self, station):
        origin_station_box = self.browser.find_element(By.ID, "from-buy-header")
        origin_station_box.click()
        origin_station_box.send_keys(station)
        
    def set_destination_station(self, station):
        destination_station_box = self.browser.find_element(By.ID, "to-header")
        destination_station_box.click()
        destination_station_box.send_keys(station)
        
    def set_ticket_type(self, ticket_type):
        sleep(1)
        ticket_select_button = None
        self.ticket_type = ticket_type
        if ticket_type == TicketTypes.SINGLE:
            ticket_select_button = self.browser.find_element(By.ID, "chip-single--header")
        elif ticket_type == TicketTypes.RETURN:
            ticket_select_button = self.browser.find_element(By.ID, "chip-return--header")
        ticket_select_button.click()
        
    def set_ticket_counts(self, adult_count, child_count):
        adult_url_param = "&passengers%5B%5D=1995-05-12"
        child_url_param = "&passengers%5B%5D=2015-05-12"
        for i in range(0, adult_count):
            self.url_additions += adult_url_param
        for i in range(0, child_count):
            self.url_additions += child_url_param
    
    def set_departure_time(self, departure_time):
        self.url_additions += f"&outwardDateType=departAfter&outwardDate={departure_time.get_year()}-{departure_time.get_month()}-{departure_time.get_day()}T{departure_time.get_hour()}%3A{departure_time.get_min()}%3A00"
       
    def set_return_time(self, return_time):
        if self.ticket_type == TicketTypes.RETURN:

            self.url_additions += f"&inwardDateType=departAfter&inwardDate={return_time.get_year()}-{return_time.get_month()}-{return_time.get_day()}T{return_time.get_hour()}%3A{return_time.get_min()}%3A00"
       
    def search_for_journey(self):
        submit_button = self.browser.find_elements(By.CSS_SELECTOR, "button[aria-label='Find times and tickets']")
        if len(submit_button) > 0:
            submit_button[0].click()
            self.clear_cookies_popup()
            
            current_url = self.browser.current_url
            current_url = re.sub(r"&passengers\%5B\%5D=[^&]*", "", current_url)
            current_url = re.sub("&outwardDateType=departAfter&outwardDate=\d\d\d\d-\d\d-\d\dT\d\d%3A\d\d%3A00", "", current_url)
            current_url = re.sub("&inwardDateType=departAfter&inwardDate=\d\d\d\d-\d\d-\d\dT\d\d%3A\d\d%3A00", "", current_url)
            current_url += self.url_additions
            
            self.browser.get(current_url)
            
    def get_ticket_data_in_list(self, ticket_list):
        found_tickets = []
        tickets = ticket_list.find_elements(By.CSS_SELECTOR, "li > div")
        for ticket in tickets:
            data = {}
            
            prices_found = set()
            spans = ticket.find_elements(By.CSS_SELECTOR, "span")
            for span in spans:
                if "£" in span.text:
                    prices_found.add(float(span.text[1:]))
            if len(prices_found) != 0:
                data["price"] = min(prices_found)
            
            departure_time = ticket.find_elements(By.CSS_SELECTOR, "div[data-test='train-results-departure-time'] > p > time > span")
            if len(departure_time) > 0:
                data["departure_time"] = departure_time[0].text

            arrival_time = ticket.find_elements(By.CSS_SELECTOR, "div[data-test='train-results-arrival-time'] > p > time > span")
            arrival_time.extend(ticket.find_elements(By.CSS_SELECTOR, "div[data-test='train-results-arrival-time'] > div > p > time > span"))
            if len(arrival_time) > 0:
                data["arrival_time"] = arrival_time[0].text
                
            spans = ticket.find_elements(By.CSS_SELECTOR, "span")
            for span in spans:
                if "minute" in span.text:
                    data["length"] = span.text
        
            found_tickets.append(data)
        return found_tickets
    
    def get_cheapest_ticket(self):
        ticket_lists = self.browser.find_elements(By.CLASS_NAME, "ColumnContent-module__alternativesListWrapper__YSLNb")

        outbound_tickets, return_tickets = [], []
    
        if len(ticket_lists) > 0: outbound_tickets = self.get_ticket_data_in_list(ticket_lists[0])
        if len(ticket_lists) >= 1: return_tickets = self.get_ticket_data_in_list(ticket_lists[1])
        
        if return_tickets == []:
            # must be a single journey
            cheapest_ticket = min(outbound_tickets, key=lambda ticket: ticket["price"])
            return cheapest_ticket
        else:
            # must be a return journey
            cheapest_outbound_ticket = min(outbound_tickets, key=lambda ticket: ticket["price"])
            cheapest_return_ticket = return_tickets[outbound_tickets.index(cheapest_outbound_ticket)]
            return cheapest_outbound_ticket, cheapest_return_ticket
        
    def launch_scraper(self):
        self.browser.get(self.url)
        
if __name__ == "__main__": 
    scraper = GreaterAngliaScraper()
    scraper.launch_scraper()
    print("Launched greater anglia web scraper")
    sleep(5)
    print("Starting cookie clearer")
    scraper.clear_cookies_popup()

    print("Cleared cookies popup")
    scraper.set_origin_station("Norwich")
    scraper.set_destination_station("Colchester")
    print("Set stations")
    scraper.set_ticket_type(TicketTypes.RETURN)
    print("Set ticket types")
    scraper.set_departure_time(DateTime(hour=15, minute=30, day=13, month=5))
    scraper.set_return_time(DateTime(hour=20, minute=0, day=13, month=5))     
    print("Set times")                  
    scraper.set_ticket_counts(2, 1)
    print("Set ticket counts")
    scraper.search_for_journey()
    print("Searching for journey")
    cheapest_ticket = scraper.get_cheapest_ticket()
    print(cheapest_ticket)

    input()
