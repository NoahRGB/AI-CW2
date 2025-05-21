from time import sleep

import pickle

import requests

from date_time import DateTime
from ticket_types import TicketTypes

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver import Keys, ActionChains

def build_realtimetickets_dictionary():
    
    station_dict = {}
            
    response = requests.get("https://www.realtimetickets.co.uk/api/locations_dropdown")
    station_codes = response.json()
    for code in station_codes["locations"]:
        station_dict[code["value"]] = code["data"]["nlc"]
    
    with open("../chatbot_data/realtimetickets_station_codes.pickle", "wb") as file:
        pickle.dump(station_dict, file)
        
def get_cheapest_ticket_in_list(browser, direction):
    cheapest_ticket = { "price": "£999" }
    outbound_ticket_list_element = browser.find_elements(By.ID, f"ticket_info_{direction}")
    if len(outbound_ticket_list_element) > 0:
        outbound_ticket_list = outbound_ticket_list_element[0]
        tickets = outbound_ticket_list.find_elements(By.TAG_NAME, "label")
        for ticket in tickets:
            divs = ticket.find_elements(By.TAG_NAME, "div")
            for div in divs:
                if "From" in div.text:
                    split = div.text.split("\n")
                    if len(split) >= 3:
                        if "From" in split[2]:
                            price = split[2].split(" ")[1]
                            if float(price[1:]) < float(cheapest_ticket["price"][1:]):
                                cheapest_ticket["price"] = price
                                times = split[0].split(" ")
                                cheapest_ticket["departure_time"] = times[0]
                                cheapest_ticket["arrival_time"] = times[1]
                                cheapest_ticket["length"] = split[1].strip().split(",")[0]
                    break
    return cheapest_ticket if "departure_time" in cheapest_ticket else None


def realtimetickets_cheapest_ticket(origin_station, destination_station, ticket_type, departure_date, return_date, adult_tickets, child_tickets):
        options = Options()
        options.add_argument("--log-level=3")

        options.add_argument("--headless=new")
        browser = Chrome(options=options)
        actions = ActionChains(browser)
        
        # load realtimetickets station code dictionary from build_realtimetickets_dictionary()
        with open("../chatbot_data/realtimetickets_station_codes.pickle", "rb") as file:
            station_codes = pickle.load(file)

        # build journey URL
        if ticket_type == TicketTypes.SINGLE:
            url = (f"https://www.realtimetickets.co.uk/a2b/search/single/{station_codes[origin_station]}/{station_codes[destination_station]}"
                + f"/out/after/{departure_date.get_year()}-{departure_date.get_month()}-{departure_date.get_day()}/"
                + f"{departure_date.get_hour()}:{departure_date.get_min()}:00/?adults={adult_tickets}&children={child_tickets}")
        else:
            url = (f"https://www.realtimetickets.co.uk/a2b/search/return/{station_codes[origin_station]}/{station_codes[destination_station]}"
                + f"/out/after/{departure_date.get_year()}-{departure_date.get_month()}-{departure_date.get_day()}/"
                + f"{departure_date.get_hour()}:{departure_date.get_min()}:00/back/after/{return_date.get_year()}-{return_date.get_month()}-{return_date.get_day()}"
                + f"/{return_date.get_hour()}:{return_date.get_min()}:00?adults={adult_tickets}&children={child_tickets}")

        browser.get(url)
        
        sleep(1)
        
        cheapest_ticket = get_cheapest_ticket_in_list(browser, "outbound")
        if ticket_type == TicketTypes.RETURN and cheapest_ticket != None:
            return_cheapest_ticket = get_cheapest_ticket_in_list(browser, "return")
            if return_cheapest_ticket != None:
                cheapest_ticket["return_departure_time"] = return_cheapest_ticket["departure_time"]
                cheapest_ticket["return_arrival_time"] = return_cheapest_ticket["arrival_time"]
                cheapest_ticket["return_length"] = return_cheapest_ticket["length"]

        print(cheapest_ticket)
        browser.close()
        return (cheapest_ticket, url) if cheapest_ticket != None else None
        

# if you run this file
if __name__ == "__main__":
    
    # test journey
    origin_station = "Norwich"
    destination_station = "Colchester"
    departure_date = DateTime(hour=12, minute=15, day=21, month=5, year=2025)
    return_date = DateTime(hour=20, minute=0, day=21, month=5, year=2025)
    ticket_type = TicketTypes.SINGLE
    child_tickets = 1
    adult_tickets = 1
    
    # build_realtimetickets_dictionary()
    ticket = realtimetickets_cheapest_ticket(origin_station, destination_station, ticket_type, departure_date, return_date, adult_tickets, child_tickets)
    print(f"\n\nTicket: {ticket}\n\n")