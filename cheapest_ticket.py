
from enum import Enum
from time import sleep
import pickle

from DateTime import DateTime

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver import Keys, ActionChains

class TicketTypes(Enum):
    SINGLE=1,
    RETURN=2

    @staticmethod
    def from_string(s): # turn string into a TicketTypes enum
        if s.lower() == "return":
            return TicketTypes.RETURN
        elif s.lower() == "single":
            return TicketTypes.SINGLE

class NationalRailScraper:
    # queries the national rail website (https://www.nationalrail.co.uk/) for the
    # specified train journey and finds the cheapest ticket with the given options

    def __init__(self, origin, destination, date, adults, children):
        options = Options()
        options.add_argument("--log-level=3")
        options.add_argument("--headless=new")
        self.browser = Chrome(options=options)
        self.actions = ActionChains(self.browser)
        self.ticket_type = None
        self.url = (f"https://www.nationalrail.co.uk/journey-planner/?origin={origin}"
                    + f"&destination={destination}&leavingDate={date}&adults={adults}"
                    + f"&children={children}&leavingType=departing&extraTime=0")

    def __del__(self):
        pass
        # self.browser.close()

    def clear_cookies_popup(self):
        # looks for the cookies accept button until it exists and then clicks it
        cookies_button = self.browser.find_elements(By.ID, "onetrust-accept-btn-handler")
        while len(cookies_button) == 0:
            cookies_button = self.browser.find_elements(By.ID, "onetrust-accept-btn-handler")
        cookies_button[0].click()
        sleep(1)

    def set_single_ticket(self, leaving_time):
        # sets ticket type and URL parameters for a single ticket if no ticket has been set yet
        if self.ticket_type is None:
            self.ticket_type = TicketTypes.SINGLE
            self.url += f"&type=single&leavingHour={leaving_time.get_hour()}&leavingMin={leaving_time.get_min()}"
        else:
            return False
    
    def set_return_ticket(self, leaving_time, return_date):
        # sets ticket type and URL parameters for a return ticket if no ticket has been set yet
        if self.ticket_type is None:
            self.ticket_type = TicketTypes.RETURN
            self.url += (f"&type=return&returnType=departing&leavingHour={leaving_time.get_hour()}"
                         + f"&leavingMin={leaving_time.get_min()}&returnDate={str(return_date)}"
                         + f"&returnHour={return_date.get_hour()}&returnMin={return_date.get_min()}")
        else:
            return False
        
    def get_info_on_ticket(self, ticket_number):
        # returns an object with departure/arrival time, length and price for a ticket given
        # by the number that it appears in the ticket list
        # MUST BE on the ticket list page
        ticket_info = { "departure_time": None, "arrival_time": None, "length": None, "price": None}
        ticket_container = self.browser.find_element(By.CSS_SELECTOR, f"div[data-testid='card-result-card-outward-{ticket_number}'")
        times = ticket_container.find_elements(By.TAG_NAME, "time")
        ticket_info["departure_time"] = times[0].text
        ticket_info["arrival_time"] = times[1].text
        ticket_info["length"] = times[2].text[:-1] # remove redundant comma
        ticket_info["price"] = self.get_ticket_price(ticket_number)
        return ticket_info
    
    def get_ticket_price(self, ticket_number):
        # finds the price for a ticket given by the number that it appears in the ticket list
        # MUST BE on the ticket list page
        price_holder = self.browser.find_element(By.ID, f"result-card-price-outward-{ticket_number}")
        price = price_holder.find_element(By.TAG_NAME, "div").find_elements(By.TAG_NAME, "span")[1].text
        return price    
        
    def get_cheapest_listed(self):
        # returns the ticket info using get_info_on_ticket() for the cheapest ticket in the list
        # MUST BE on the ticket list page
        cheapest_ticket = { "price": "999" }
        result_num = 0
        should_continue = len(self.browser.find_elements(By.ID, f"result-card-price-outward-{result_num}")) > 0
        while should_continue:
            price = self.get_ticket_price(result_num)
            if float(price[1:]) < float(cheapest_ticket["price"][1:]):
                cheapest_ticket = self.get_info_on_ticket(result_num)

            result_num += 1
            should_continue = len(self.browser.find_elements(By.ID, f"result-card-price-outward-{result_num}")) > 0
        return cheapest_ticket

    def launch_scraper(self):
        self.browser.get(self.url)




with open("./chatbot_data/station_list.pickle", "rb") as file:
    station_dict = pickle.load(file)

# ========================================================
# gather this information from the chatbot (somehow)
ticket = TicketTypes.RETURN
leaving_date = DateTime(12, 30, 31, 3, 2025)
# return_date = DateTime(13, 45, 21, 3, 2025)
origin = "NRW"
destination = "IPS"
adults = 1
children = 1
# ========================================================


# ================================================================================
# use the gathered information with a web scraper to retrieve journey times

# scraper = NationalRailScraper(origin, destination, leaving_date, adults, children)
# scraper.set_single_ticket(leaving_date)
# # scraper.set_return_ticket(leaving_date, return_date)
# scraper.launch_scraper()
# scraper.clear_cookies_popup()

# cheapest = scraper.get_cheapest_listed()
# print(f"\n\nCheapest ticket:\nDeparture time: {cheapest['departure_time']}\nArrival time: {cheapest['arrival_time']}\nDuration: {cheapest['length']}\nPrice: {cheapest['price']}\n\n")

# ================================================================================