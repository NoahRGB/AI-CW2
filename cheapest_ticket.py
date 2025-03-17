
from enum import Enum
from time import sleep
import pickle

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver import Keys, ActionChains

class TicketTypes(Enum):
    SINGLE=1,
    RETURN=2

class DateTime:
    # can be used just to store a time, just to store a date, or both. day/month/year will always
    # be integers and str() will format the date in the form "ddmmyy"
    months = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]

    def __init__(self, hour, minute, day=1, month=1, year=2025):
        self.hour = hour
        self.minute = minute
        self.day = day
        self.month = month
        self.year = year

        if type(self.month) is str:
            does_month_exist = DateTime.months.count(self.month.lower()) > 0
            if does_month_exist:
                # turn string month into integer month
                self.month = DateTime.months.index(self.month.lower()) + 1
        
        # check all attributes are integers and year is correct length, otherwise reset
        if not isinstance(self.day, int) or not isinstance(self.month, int) or not isinstance(self.year, int) or len(str(self.year)) != 4:
            self.reset()

    def reset(self):
        self.day = 1
        self.month = 1
        self.year = 2025

    def __str__(self):
        return f"{'0' if self.day < 10 else ''}{str(self.day)}{'0' if self.month < 10 else ''}{str(self.month)}{str(self.year)[2:4]}"
    
    def get_hour(self):
        return f"{'0' if self.hour < 10 else ''}{self.hour}"
    
    def get_min(self):
        return f"{'0' if self.minute < 10 else ''}{self.minute}"

class NationalRailScraper:
    # queries the national rail website (https://www.nationalrail.co.uk/) for the
    # specified train journey and finds the cheapest ticket with the given options

    def __init__(self, origin, destination, date, adults, children):
        options = Options()
        self.browser = Chrome(options=options)
        self.actions = ActionChains(self.browser)
        self.ticket_type = None
        self.url = (f"https://www.nationalrail.co.uk/journey-planner/?origin={origin}"
                    + f"&destination={destination}&leavingDate={date}&adults={adults}"
                    + f"&children={children}&leavingType=departing&extraTime=0")

    def __del__(self):
        self.browser.close()

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
        
    def launch_scraper(self):
        self.browser.get(self.url)



with open("station_list.pickle", "rb") as file:
    station_dict = pickle.load(file)
print(station_dict)

# ========================================================
# gather this information from the chatbot (somehow)
ticket = TicketTypes.RETURN
leaving_date = DateTime(12, 45, 19, 3, 2025)
return_date = DateTime(13, 45, 21, 3, 2025)
origin = "NRW"
destination = "IPS"
adults = 2
children = 2
# ========================================================




# ================================================================================
# use the gathered information with a web scraper to retrieve journey times
scraper = NationalRailScraper(origin, destination, leaving_date, adults, children)
scraper.set_return_ticket(leaving_date, return_date)
scraper.launch_scraper()
scraper.clear_cookies_popup();
# ================================================================================


input()