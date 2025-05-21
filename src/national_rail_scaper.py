from time import sleep

from date_time import DateTime
from ticket_types import TicketTypes

from selenium.webdriver.chrome.service import Service
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver import Keys, ActionChains

# national_rail_cheapest_ticket() builds a URL for the national rail website (https://www.nationalrail.co.uk/)
# and uses get_ticket_price() + get_info_on_ticket() to extract the cheapest ticket from the list. will return
# None if an error was found along the way (e.g. the journey is invalid)

def get_info_on_ticket(browser, ticket_number, direction):
    # returns an object with departure/arrival time, length and price for a ticket given
    # by the number that it appears in the ticket list
    # MUST BE on the ticket list page
    ticket_info = { "departure_time": None, "arrival_time": None, "length": None, "price": None, "ticket_number": None }
    ticket_container = browser.find_elements(By.ID, f"{direction}-{ticket_number}")
    if len(ticket_container) > 0:
        times = ticket_container[0].find_elements(By.TAG_NAME, "time")
        ticket_info["departure_time"] = times[0].text
        ticket_info["arrival_time"] = times[1].text
        ticket_info["length"] = times[2].text[:-1] # remove redundant comma
        ticket_info["price"] = get_ticket_price(browser, ticket_number)
        ticket_info["ticket_number"] = ticket_number
    return ticket_info

def get_info_on_return_ticket(browser, actions, ticket_number):
    # selects the given ticket using ticket_number and then finds the first return ticket that appears
    # in the list after
    # MUST BE on the outbound ticket page
    return_button = browser.find_elements(By.CSS_SELECTOR, f"label[for='ticket-button-outward-{ticket_number}']")

    if len(return_button) > 0:
        actions.move_to_element(return_button[0]).click().perform()
        return_ticket  = get_info_on_ticket(browser, 0, "inward")
        return return_ticket if return_ticket["departure_time"] != None else None

def get_ticket_price(browser, ticket_number):
    # finds the price for a ticket given by the number that it appears in the ticket list
    # MUST BE on the ticket list page
    price_holder = browser.find_element(By.ID, f"result-card-price-outward-{ticket_number}")
    price = price_holder.find_element(By.TAG_NAME, "div").find_elements(By.TAG_NAME, "span")[1].text
    return price   

def national_rail_cheapest_ticket(origin_station, destination_station, ticket_type, departure_date, return_date, adult_tickets, child_tickets):
        service = Service("C:/WebDriver/chromedriver.exe") # replace this with your chromedriver location
        options = Options()
        options.add_argument("--log-level=3")

        options.add_argument("--headless=new")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36")
        browser = Chrome(service=service, options=options)
        actions = ActionChains(browser)

        # build journey URL
        url = (f"https://www.nationalrail.co.uk/journey-planner/?origin={origin_station}"
                    + f"&destination={destination_station}&leavingDate={departure_date}&adults={adult_tickets}"
                    + f"&children={child_tickets}&leavingType=departing&extraTime=0"
                    + f"&leavingHour={departure_date.get_hour()}&leavingMin={departure_date.get_min()}")
        
        if ticket_type == TicketTypes.RETURN:
            url += (f"&type=return&returnType=departing&returnDate={return_date}"
                        + f"&returnHour={return_date.get_hour()}&returnMin={return_date.get_min()}")
        else:
            url += (f"&type=single")
            
        browser.get("https://www.nationalrail.co.uk/")
        sleep(0.5)
        browser.get(url)

       # clear cookies popup
        cookies_button = browser.find_elements(By.ID, "onetrust-accept-btn-handler")
        while len(cookies_button) == 0:
            cookies_button = browser.find_elements(By.ID, "onetrust-accept-btn-handler")
        cookies_button[0].click()
        sleep(1) 
        
        # find cheapest ticket
        cheapest_ticket = { "price": "999" }
        result_num = 0
        should_continue = len(browser.find_elements(By.ID, f"outward-{result_num}")) > 0
        while should_continue:
            price = get_ticket_price(browser, result_num)
            if float(price[1:]) < float(cheapest_ticket["price"][1:]):
                cheapest_ticket = get_info_on_ticket(browser, result_num, "outward")

            result_num += 1
            should_continue = len(browser.find_elements(By.ID, f"outward-{result_num}")) > 0
        
        if ticket_type == TicketTypes.RETURN and "ticket_number" in cheapest_ticket:
            return_ticket = get_info_on_return_ticket(browser, actions, cheapest_ticket["ticket_number"])
            if return_ticket != None:
                cheapest_ticket["return_departure_time"] = return_ticket["departure_time"]
                cheapest_ticket["return_arrival_time"] = return_ticket["arrival_time"]
                cheapest_ticket["return_length"] = return_ticket["length"]
        
        browser.close()
        return (cheapest_ticket, url) if "departure_time" in cheapest_ticket else None
        

# if you run this file
if __name__ == "__main__":
    
    # test journey
    origin_station = "COL"
    destination_station = "NRW"
    departure_date = DateTime(hour=15, minute=30, day=25, month=5, year=2025)
    return_date = DateTime(hour=20, minute=0, day=25, month=5, year=2025)
    ticket_type = TicketTypes.RETURN
    adult_tickets = 1
    child_tickets = 0

    ticket = national_rail_cheapest_ticket(origin_station, destination_station, ticket_type, departure_date, return_date, adult_tickets, child_tickets)
    print(f"\n\nTicket: {ticket}\n\n")
