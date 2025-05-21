import re

from time import sleep

from date_time import DateTime
from ticket_types import TicketTypes

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver import Keys, ActionChains

from playwright.sync_api import Page, sync_playwright

origin_station = "Norwich"
destination_station = "Colchester"
departure_time = DateTime(hour=16, minute=30, day=20, month=5, year=2025)
return_time = DateTime(hour=20, minute=0, day=20, month=5, year=2025)
ticket_type = TicketTypes.SINGLE
child_tickets = 1
adult_tickets = 1

def get_trainpal_cheapest_ticket(origin_station, destination_station, departure_time, return_time, ticket_type, child_tickets, adult_tickets):
    options = Options()
    options.add_argument("--log-level=3")
    # options.add_argument("--headless")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36")
    
    browser = Chrome(options=options)
    actions = ActionChains(browser)

    url = f"https://uk.trip.com/trains/list?hidchildnum={child_tickets}&biztype=UK&locale=en-GB&curr=GBP"
    url += f"&departurecity={origin_station}"
    url += f"&arrivalcity={destination_station}"
    url += f"&departdate={departure_time.get_year()}-{departure_time.get_month()}-{departure_time.get_day()}"
    url += f"&departhouript={departure_time.get_hour()}&departminuteipt={departure_time.get_min()}"
    url += f"&hidadultnum={adult_tickets}"
    url += f"&hidadultnum={adult_tickets}"

    if ticket_type == TicketTypes.RETURN:
        url += f"&scheduleType=return"
        url += f"&returndate={return_time.get_year()}-{return_time.get_month()}-{return_time.get_day()}"
        url += f"&returnhouript={return_time.get_hour()}&returnminuteipt={return_time.get_min()}"
    else:
        url += f"&scheduleType=single"

    browser.get(url)
    
    # with sync_playwright() as p:
    #     browser = p.chromium.launch(headless=False)
        
    #     page = browser.new_page()
    #     page.goto(url)
        
    #     sleep(15)
        
    
    sleep(5)
    
    ticket_list = browser.find_elements(By.ID, "train-search-list")
    if len(ticket_list) > 0:
        for i in range(0, 10):
            ticket_element = ticket_list[0].find_elements(By.ID, f"train-id-{i}")
            if len(ticket_element) > 0:
                ticket = ticket_element[0]
                
                ticket_spans = ticket.find_elements(By.TAG_NAME, "span")
                for ticket_span in ticket_spans:
                    if ":" in ticket_span.text:
                        print(ticket_span.text)
    

    input()
    

if __name__ == "__main__":

    get_trainpal_cheapest_ticket(origin_station, destination_station, departure_time, return_time, ticket_type, child_tickets, adult_tickets)