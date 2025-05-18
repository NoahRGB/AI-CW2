
from date_time import DateTime
from ticket_types import TicketTypes
from national_rail_scaper import NationalRailScraper

if __name__ == "__main__":


    ticket = TicketTypes.RETURN
    leaving_date = DateTime(hour=13, minute=30, day=12, month=5, year=2025)
    # return_date = DateTime(hour=13, minute=45, day=21, month=3, year=2025)
    origin = "NRW"
    destination = "IPS"
    adults = 1
    children = 1

    scraper = NationalRailScraper(origin, destination, leaving_date, adults, children)
    scraper.set_single_ticket(leaving_date)
    # scraper.set_return_ticket(leaving_date, return_date)
    scraper.launch_scraper()
    scraper.clear_cookies_popup()

    cheapest = scraper.get_cheapest_listed()
    print(f"\n\nCheapest ticket:\nDeparture time: {cheapest['departure_time']}\nArrival time: {cheapest['arrival_time']}\nDuration: {cheapest['length']}\nPrice: {cheapest['price']}\n\n")

    input()
