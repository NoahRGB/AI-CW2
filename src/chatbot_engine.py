from random import choice

from ticket_types import TicketTypes
from cheapest_ticket import NationalRailScraper, TicketTypes
from delay_prediction import find_remaining_delays
from date_time import DateTime
from fact_types import *

from experta import *
from difflib import get_close_matches, SequenceMatcher

import warnings
warnings.filterwarnings('ignore')

from chatbot import Chatbot

class ChatbotEngine(KnowledgeEngine):
    def __init__(self, chatbot):
        KnowledgeEngine.__init__(self)
        self.chatbot = chatbot

    def clear_chatbot_intention(self):
        self.chatbot.last_intention = Chatbot.IntentionTypes.NONE
        self.chatbot.last_intention_fact = self.modify(self.chatbot.last_intention_fact, type=self.chatbot.last_intention)
        
    def find_next_station_type(self):
        declaring_stations = self.chatbot.detect_declaring_station(self.chatbot.last_message)
        if declaring_stations and declaring_stations[0] == Chatbot.IntentionTypes.DECLARING_ORIGIN_STATION:
            return Chatbot.IntentionTypes.DECLARING_ORIGIN_STATION
        elif declaring_stations and declaring_stations[0] == Chatbot.IntentionTypes.DECLARING_DESTINATION_STATION:
            return Chatbot.IntentionTypes.DECLARING_DESTINATION_STATION
        else:
            if self.chatbot.origin_station_fact["pending"] == True:
                return Chatbot.IntentionTypes.DECLARING_ORIGIN_STATION
            elif self.chatbot.destination_station_fact["pending"] == True:
                return Chatbot.IntentionTypes.DECLARING_DESTINATION_STATION
                    
    @DefFacts()
    def setup(self):
        # setup the initial facts
        yield Intention(type=Chatbot.IntentionTypes.UNSURE)
        
    # ====== GENERAL CHAT RESPONSES ======
        
    @Rule(Intention(type=Chatbot.IntentionTypes.GREETING))
    def greeting(self):
        self.chatbot.send_bot_message(choice(self.chatbot.intentions["intentions"]["greeting"]["responses"]))
        
    @Rule(Intention(type=Chatbot.IntentionTypes.THANKS))
    def thanks(self):
        self.chatbot.send_bot_message(choice(self.chatbot.intentions["intentions"]["thanks"]["responses"]))
        
    @Rule(Intention(type=Chatbot.IntentionTypes.EXIT))
    def exit(self):
        self.chatbot.send_bot_message(choice(self.chatbot.intentions["intentions"]["exit"]["responses"]))
        
    @Rule(AND(OR(Intention(type=Chatbot.IntentionTypes.NONE), Intention(type=Chatbot.IntentionTypes.UNSURE)),
              AND(~Ticket(type=MATCH.ticket_type, pending=True) & ~OriginStation(name=MATCH.origin_name, code=MATCH.origin_code, pending=True)
                  & ~DestinationStation(name=W(), code=W(), pending=True)
                  & ~DepartureTime(time=W(), pending=True)
                  & ~DepartureDate(date=W(), pending=True)
                  & ~ReturnTime(time=W(), pending=True)
                  & ~ReturnDate(date=W(), pending=True)
                  & ~AdultTickets(count=W(), pending=True)
                  & ~ChildTickets(count=W(), pending=True)
                  & ~CurrentStation(name=W(), code=W(), pending=True)
                  & ~CurrentTime(time=W(), pending=True)
                  & ~CurrentDelay(amount=W(), pending=True)
                  & ~Direction(to_nrw=W(), pending=True))))
    def unsure(self):
        self.chatbot.send_bot_message("I'm unsure what you mean, but you can ask me about train tickets!")

    # ====== INPUTTING A TICKET TYPE ======

    @Rule(NOT(Intention(type=Chatbot.IntentionTypes.CONFIRM)) & Ticket(type=MATCH.ticket_type, pending=True))
    def prompt_ticket_confirmation(self, ticket_type):
        self.chatbot.send_bot_message(f"Are you sure you want a {ticket_type} ticket?")
        
    @Rule(Intention(type=Chatbot.IntentionTypes.CONFIRM) & Ticket(type=MATCH.ticket_type, pending=True))
    def confirm_pending_ticket(self, ticket_type):
        self.chatbot.ticket_fact = self.modify(self.chatbot.ticket_fact, pending=False)
        self.chatbot.last_intention_fact = self.modify(self.chatbot.last_intention_fact, type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH)
        
    @Rule(Intention(type=Chatbot.IntentionTypes.DENY) & Ticket(type=MATCH.ticket_type, pending=True))
    def deny_pending_ticket(self, ticket_type):
        self.retract(self.chatbot.ticket_fact)
        self.chatbot.ticket_fact = self.declare(Ticket(pending=True))
        self.chatbot.last_intention_fact = self.modify(self.chatbot.last_intention_fact, type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH)
        print(f"\nFacts after denying ticket:\n{self.facts}\n")
    
    @Rule(Intention(type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH) & ~Ticket(pending=False) & ~Ticket(type=W(), pending=True))
    def select_ticket(self):
        self.chatbot.send_bot_message("What type of ticket do you need? (single, return)")
    
    # ====== INPUTTING AN ORIGIN STATION ======

    @Rule(NOT(Intention(type=Chatbot.IntentionTypes.CONFIRM)) 
          & OriginStation(name=MATCH.origin_name, code=MATCH.origin_code, pending=True))
    def prompt_origin_station_confirmation(self, origin_name, origin_code):
        self.chatbot.send_bot_message(f"Confirm origin station {origin_name} ({origin_code})?")
        
    @Rule(Intention(type=Chatbot.IntentionTypes.CONFIRM) & OriginStation(name=W(), code=W(), pending=True) 
          & ~Ticket(type=MATCH.ticket_type, pending=True))
    def confirm_pending_origin_station(self):
        self.chatbot.origin_station_fact = self.modify(self.chatbot.origin_station_fact, pending=False)
        self.chatbot.last_intention_fact = self.modify(self.chatbot.last_intention_fact, type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH)
        
    @Rule(Intention(type=Chatbot.IntentionTypes.DENY) & OriginStation(name=W(), code=W(), pending=True)
          & ~Ticket(type=MATCH.ticket_type, pending=True))
    def deny_pending_origin_station(self):
        self.retract(self.chatbot.origin_station_fact)
        self.chatbot.origin_station_fact = self.declare(OriginStation(pending=True))
        self.chatbot.last_intention_fact = self.modify(self.chatbot.last_intention_fact, type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH)
        
    @Rule(Intention(type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH) & Ticket(type=MATCH.ticket_type, pending=False) 
          & ~OriginStation(pending=False), salience=0)
    def select_origin_station(self, ticket_type):
        self.chatbot.send_bot_message(f"You have selected a {ticket_type} ticket. Where are you travelling from?")
        
    # ====== INPUTTING A DESTINATION STATION ======
        
    @Rule(NOT(Intention(type=Chatbot.IntentionTypes.CONFIRM)) 
          & DestinationStation(name=MATCH.destination_name, code=MATCH.destination_code, pending=True))
    def prompt_destination_station_confirmation(self, destination_name, destination_code):
        self.chatbot.send_bot_message(f"Confirm destination station {destination_name} ({destination_code})?")
        
    @Rule(Intention(type=Chatbot.IntentionTypes.CONFIRM) & DestinationStation(name=W(), code=W(), pending=True) 
          & ~Ticket(type=MATCH.ticket_type, pending=True) & ~OriginStation(name=W(), code=W(), pending=True))
    def confirm_pending_destination_station(self):
        self.chatbot.destination_station_fact = self.modify(self.chatbot.destination_station_fact, pending=False)
        self.chatbot.last_intention_fact = self.modify(self.chatbot.last_intention_fact, type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH)
        
    @Rule(Intention(type=Chatbot.IntentionTypes.DENY) & DestinationStation(name=W(), code=W(), pending=True)
          & ~Ticket(type=MATCH.ticket_type, pending=True) & ~OriginStation(name=W(), code=W(), pending=True))
    def deny_pending_destination_station(self):
        self.retract(self.chatbot.destination_station_fact)
        self.chatbot.destination_station_fact = self.declare(DestinationStation(pending=True))
        self.chatbot.last_intention_fact = self.modify(self.chatbot.last_intention_fact, type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH)
        
    @Rule(Intention(type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH) & Ticket(type=MATCH.ticket_type, pending=False) 
          & ~DestinationStation(pending=False), salience=1)
    def select_destination_station(self, ticket_type):
        self.chatbot.send_bot_message(f"You have selected a {ticket_type} ticket. Where are you travelling to?")
        
    # ====== INPUTTING A DEPARTURE TIME ======
        
    @Rule(NOT(Intention(type=Chatbot.IntentionTypes.CONFIRM)) 
          & DepartureTime(time=MATCH.departure_time, pending=True))
    def prompt_departure_time_confirmation(self, departure_time):
        self.chatbot.send_bot_message(f"Confirm departure time: {departure_time.get_time()}?")
        
    @Rule(Intention(type=Chatbot.IntentionTypes.CONFIRM) & DepartureTime(time=W(), pending=True) 
          & ~Ticket(type=MATCH.ticket_type, pending=True) & ~OriginStation(name=W(), code=W(), pending=True)
          & ~DestinationStation(name=W(), code=W(), pending=True))
    def confirm_pending_departure_time(self):
        self.chatbot.departure_time_fact = self.modify(self.chatbot.departure_time_fact, pending=False)
        self.chatbot.last_intention_fact = self.modify(self.chatbot.last_intention_fact, type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH)
        
    @Rule(Intention(type=Chatbot.IntentionTypes.DENY) & DepartureTime(time=W(), pending=True)
          & ~Ticket(type=MATCH.ticket_type, pending=True) & ~OriginStation(name=W(), code=W(), pending=True)
          & ~DestinationStation(name=W(), code=W(), pending=True))
    def deny_pending_departure_time(self):
        self.retract(self.chatbot.departure_time_fact)
        self.chatbot.departure_time_fact = self.declare(DepartureTime(pending=True))
        self.chatbot.last_intention_fact = self.modify(self.chatbot.last_intention_fact, type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH)
        
    @Rule(Intention(type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH) & Ticket(type=MATCH.ticket_type, pending=False)
          & OriginStation(name=MATCH.origin_name, code=MATCH.origin_code, pending=False)
          & DestinationStation(name=MATCH.destination_name, code=MATCH.destination_code, pending=False)
          & ~DepartureTime(pending=False))
    def select_departure_time(self, ticket_type, origin_name, origin_code, destination_name, destination_code):
        self.chatbot.send_bot_message(f"What time (24hr) do you want to leave {origin_name} ({origin_code}) to get to {destination_name} ({destination_code})?")
        
    # ====== INPUTTING A DEPARTURE DATE ======
    
    @Rule(NOT(Intention(type=Chatbot.IntentionTypes.CONFIRM)) 
          & DepartureDate(date=MATCH.departure_date, pending=True))
    def prompt_departure_date_confirmation(self, departure_date):
        self.chatbot.send_bot_message(f"Confirm departure date: {departure_date.get_date()}?")
        
    @Rule(Intention(type=Chatbot.IntentionTypes.CONFIRM) & DepartureDate(date=W(), pending=True) 
          & ~Ticket(type=MATCH.ticket_type, pending=True) & ~OriginStation(name=W(), code=W(), pending=True)
          & ~DestinationStation(name=W(), code=W(), pending=True) & ~DepartureTime(time=W(), pending=True))
    def confirm_pending_departure_date(self):
        self.chatbot.departure_date_fact = self.modify(self.chatbot.departure_date_fact, pending=False)
        self.chatbot.last_intention_fact = self.modify(self.chatbot.last_intention_fact, type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH)
        
    @Rule(Intention(type=Chatbot.IntentionTypes.DENY) & DepartureDate(date=W(), pending=True)
          & ~Ticket(type=MATCH.ticket_type, pending=True) & ~OriginStation(name=W(), code=W(), pending=True)
          & ~DestinationStation(name=W(), code=W(), pending=True) & ~DepartureTime(time=W(), pending=True))
    def deny_pending_departure_date(self):
        self.retract(self.chatbot.departure_date_fact)
        self.chatbot.departure_date_fact = self.declare(DepartureDate(pending=True))
        self.chatbot.last_intention_fact = self.modify(self.chatbot.last_intention_fact, type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH)

    @Rule(Intention(type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH) & Ticket(type=MATCH.ticket_type, pending=False)
          & OriginStation(name=MATCH.origin_name, code=MATCH.origin_code, pending=False)
          & DestinationStation(name=MATCH.destination_name, code=MATCH.destination_code, pending=False)
          & ~DepartureDate(pending=False))
    def select_departure_date(self, ticket_type, origin_name, origin_code, destination_name, destination_code):
        self.chatbot.send_bot_message(f"What date do you want to leave {origin_name} ({origin_code}) to get to {destination_name} ({destination_code})?")
        
    # ====== INPUTTING RETURN TIME ======

    @Rule(NOT(Intention(type=Chatbot.IntentionTypes.CONFIRM)) 
          & ReturnTime(time=MATCH.return_time, pending=True))
    def prompt_return_time_confirmation(self, return_time):
        self.chatbot.send_bot_message(f"Confirm return time: {return_time.get_time()}?")
        
    @Rule(Intention(type=Chatbot.IntentionTypes.CONFIRM) & ReturnTime(time=W(), pending=True) 
          & ~Ticket(type=MATCH.ticket_type, pending=True) & ~OriginStation(name=W(), code=W(), pending=True)
          & ~DestinationStation(name=W(), code=W(), pending=True) & ~DepartureTime(time=W(), pending=True)
          & ~DepartureDate(date=W(), pending=True))
    def confirm_pending_return_time(self):
        self.chatbot.return_time_fact = self.modify(self.chatbot.return_time_fact, pending=False)
        self.chatbot.last_intention_fact = self.modify(self.chatbot.last_intention_fact, type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH)
        
    @Rule(Intention(type=Chatbot.IntentionTypes.DENY) & ReturnTime(time=W(), pending=True)
          & ~Ticket(type=MATCH.ticket_type, pending=True) & ~OriginStation(name=W(), code=W(), pending=True)
          & ~DestinationStation(name=W(), code=W(), pending=True) & ~DepartureTime(time=W(), pending=True)
          & ~DepartureDate(date=W(), pending=True))
    def deny_pending_return_time(self):
        self.retract(self.chatbot.return_time_fact)
        self.chatbot.return_time_fact = self.declare(ReturnTime(pending=True))
        self.chatbot.last_intention_fact = self.modify(self.chatbot.last_intention_fact, type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH)

    @Rule(Intention(type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH)
          & Ticket(type=TicketTypes.RETURN, pending=False)
          & OriginStation(name=MATCH.origin_name, code=MATCH.origin_code, pending=False)
          & DestinationStation(name=MATCH.destination_name, code=MATCH.destination_code, pending=False)
          & ~ReturnTime(pending=False)
          & DepartureDate(pending=False) & DepartureTime(pending=False))
    def select_return_time(self, origin_name, origin_code, destination_name, destination_code):
        self.chatbot.send_bot_message(f"What time (24hr) do you want to return to {origin_name} ({origin_code}) from {destination_name} ({destination_code})?")

    # ====== INPUTTING RETURN DATE ======

    @Rule(NOT(Intention(type=Chatbot.IntentionTypes.CONFIRM)) 
          & ReturnDate(date=MATCH.return_date, pending=True))
    def prompt_return_date_confirmation(self, return_date):
        self.chatbot.send_bot_message(f"Confirm return date: {return_date.get_date()}?")
        
    @Rule(Intention(type=Chatbot.IntentionTypes.CONFIRM) & ReturnDate(date=W(), pending=True) 
          & ~Ticket(type=MATCH.ticket_type, pending=True) & ~OriginStation(name=W(), code=W(), pending=True)
          & ~DestinationStation(name=W(), code=W(), pending=True) & ~DepartureTime(time=W(), pending=True)
          & ~DepartureDate(date=W(), pending=True) & ~ReturnTime(time=W(), pending=True))
    def confirm_pending_return_date(self):
        self.chatbot.return_date_fact = self.modify(self.chatbot.return_date_fact, pending=False)
        self.chatbot.last_intention_fact = self.modify(self.chatbot.last_intention_fact, type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH)
                 
    @Rule(Intention(type=Chatbot.IntentionTypes.DENY) & ReturnDate(date=W(), pending=True)
          & ~Ticket(type=MATCH.ticket_type, pending=True) & ~OriginStation(name=W(), code=W(), pending=True)
          & ~DestinationStation(name=W(), code=W(), pending=True) & ~DepartureTime(time=W(), pending=True)
          & ~DepartureDate(date=W(), pending=True) & ~ReturnTime(time=W(), pending=True))
    def deny_pending_return_date(self):
        self.retract(self.chatbot.return_date_fact)
        self.chatbot.return_date_fact = self.declare(ReturnDate(pending=True))
        self.chatbot.last_intention_fact = self.modify(self.chatbot.last_intention_fact, type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH)

    @Rule(Intention(type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH)
          & Ticket(type=TicketTypes.RETURN, pending=False)
          & OriginStation(name=MATCH.origin_name, code=MATCH.origin_code, pending=False)
          & DestinationStation(name=MATCH.destination_name, code=MATCH.destination_code, pending=False)
          & ~ReturnDate(pending=False)
          & DepartureDate(pending=False) & DepartureTime(pending=False))
    def select_return_date(self, origin_name, origin_code, destination_name, destination_code):
        self.chatbot.send_bot_message(f"What date do you want to return to {origin_name} ({origin_code}) from {destination_name} ({destination_code})?")

    # ====== INPUTTING ADULT TICKETS ======
        
    @Rule(NOT(Intention(type=Chatbot.IntentionTypes.CONFIRM)) 
          & AdultTickets(count=MATCH.adult_tickets_count, pending=True))
    def prompt_adult_tickets_confirmation(self, adult_tickets_count):
        self.chatbot.send_bot_message(f"Do you want {adult_tickets_count} adult tickets?")
        
    @Rule(Intention(type=Chatbot.IntentionTypes.CONFIRM) & AdultTickets(count=W(), pending=True) 
          & ~Ticket(type=MATCH.ticket_type, pending=True) & ~OriginStation(name=W(), code=W(), pending=True)
          & ~DestinationStation(name=W(), code=W(), pending=True) & ~DepartureTime(time=W(), pending=True)
          & ~DepartureDate(date=W(), pending=True))
    def confirm_pending_adult_tickets(self):
        self.chatbot.adult_tickets_fact = self.modify(self.chatbot.adult_tickets_fact, pending=False)
        self.chatbot.last_intention_fact = self.modify(self.chatbot.last_intention_fact, type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH)
        
    @Rule(Intention(type=Chatbot.IntentionTypes.DENY) & AdultTickets(count=W(), pending=True)
          & ~Ticket(type=MATCH.ticket_type, pending=True) & ~OriginStation(name=W(), code=W(), pending=True)
          & ~DestinationStation(name=W(), code=W(), pending=True) & ~DepartureTime(time=W(), pending=True)
          & ~DepartureDate(date=W(), pending=True))
    def deny_pending_adult_tickets(self):
        self.retract(self.chatbot.adult_tickets_fact)
        self.chatbot.adult_tickets_fact = self.declare(AdultTickets(count=1, pending=True))
        self.chatbot.last_intention_fact = self.modify(self.chatbot.last_intention_fact, type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH)
    
    # ====== INPUTTING CHILD TICKETS ======
        
    @Rule(NOT(Intention(type=Chatbot.IntentionTypes.CONFIRM)) 
          & ChildTickets(count=MATCH.child_tickets_count, pending=True))
    def prompt_child_tickets_confirmation(self, child_tickets_count):
        self.chatbot.send_bot_message(f"Do you want {child_tickets_count} child tickets?")
        
    @Rule(Intention(type=Chatbot.IntentionTypes.CONFIRM) & ChildTickets(count=W(), pending=True) 
          & ~Ticket(type=MATCH.ticket_type, pending=True) & ~OriginStation(name=W(), code=W(), pending=True)
          & ~DestinationStation(name=W(), code=W(), pending=True) & ~DepartureTime(time=W(), pending=True)
          & ~DepartureDate(date=W(), pending=True) & ~AdultTickets(count=W(), pending=True))
    def confirm_pending_child_tickets(self):
        self.chatbot.child_tickets_fact = self.modify(self.chatbot.child_tickets_fact, pending=False)
        self.chatbot.last_intention_fact = self.modify(self.chatbot.last_intention_fact, type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH)
          
    @Rule(Intention(type=Chatbot.IntentionTypes.DENY) & ChildTickets(count=W(), pending=True)
          & ~Ticket(type=MATCH.ticket_type, pending=True) & ~OriginStation(name=W(), code=W(), pending=True)
          & ~DestinationStation(name=W(), code=W(), pending=True) & ~DepartureTime(time=W(), pending=True)
          & ~DepartureDate(date=W(), pending=True) & ~AdultTickets(count=W(), pending=True))
    def deny_pending_child_tickets(self):
        self.retract(self.chatbot.child_tickets_fact)
        self.chatbot.child_tickets_fact = self.declare(ChildTickets(count=0, pending=True))
        self.chatbot.last_intention_fact = self.modify(self.chatbot.last_intention_fact, type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH)
        
    # ====== FINDING CHEAPEST TICKET ======
    
    @Rule(OR(Ticket(type=TicketTypes.SINGLE, pending=False), (Ticket(type=TicketTypes.RETURN, pending=False) & ReturnDate(date=MATCH.return_date, pending=False) & ReturnTime(time=MATCH.return_time, pending=False)))
          & OriginStation(name=MATCH.origin_name, code=MATCH.origin_code, pending=False)
          & DestinationStation(name=MATCH.destination_name, code=MATCH.destination_code, pending=False)
          & DepartureTime(time=MATCH.departure_time, pending=False)
          & DepartureDate(date=MATCH.departure_date, pending=False)
          & AdultTickets(count=MATCH.adult_count, pending=False)
          & ChildTickets(count=MATCH.child_count, pending=False))
    def get_cheapest_ticket(self, origin_name, origin_code, destination_name, destination_code, departure_time, departure_date, adult_count, child_count, return_time=None, return_date=None,):
        print("Getting cheapest ticket")
        
        ticket_type = self.chatbot.ticket_fact["type"]
        
        total_departure_time = DateTime(minute=departure_time.get_min(),
                                        hour=departure_time.get_hour(),
                                        day=departure_date.day,
                                        month=departure_date.month)
        
        scraper = NationalRailScraper(origin_code, destination_code, total_departure_time, int(adult_count), int(child_count))
        
        if ticket_type == TicketTypes.SINGLE:
            scraper.set_single_ticket(total_departure_time)
        elif ticket_type == TicketTypes.RETURN:
            total_return_time = DateTime(minute=return_time.get_min(),
                                         hour=return_time.get_hour(),
                                         day=return_date.day,
                                         month=return_date.month)
            scraper.set_return_ticket(total_departure_time, total_return_time)

        scraper.launch_scraper()
        scraper.clear_cookies_popup()
        cheapest = scraper.get_cheapest_listed()
        self.chatbot.send_bot_message(f"Cheapest ticket from {origin_name} to {destination_name} leaving after {total_departure_time.get_date()} at {total_departure_time.get_time()} ({adult_count} adults and {child_count} children):<br>🟢 Departure time: {cheapest['departure_time']}<br>🔴 Arrival time: {cheapest['arrival_time']}<br>⏰ Duration: {cheapest['length']}<br>💷 Price: {cheapest['price']}<br>🌐 Link: <a class='dark' target='_blank' href='{scraper.get_current_url()}'>click here</a>")

    # ====== INPUTTING CURRENT STATION ======

    @Rule(Intention(type=Chatbot.IntentionTypes.CONFIRM) & CurrentStation(name=MATCH.current_station_name, code=MATCH.current_station_code, pending=True))
    def confirm_pending_current_station(self, current_station_name, current_station_code):
        self.chatbot.current_station_fact = self.modify(self.chatbot.current_station_fact, pending=False)
        self.chatbot.last_intention_fact = self.modify(self.chatbot.last_intention_fact, type=Chatbot.IntentionTypes.DELAY_WALKTHROUGH)
        
    @Rule(NOT(Intention(type=Chatbot.IntentionTypes.CONFIRM))
              & CurrentStation(name=MATCH.current_station_name, code=MATCH.current_station_code, pending=True))
    def prompt_current_station_confirmation(self, current_station_name, current_station_code):
        self.chatbot.send_bot_message(f"Confirm current station {current_station_name} ({current_station_code})?")

    @Rule(Intention(type=Chatbot.IntentionTypes.DELAY_WALKTHROUGH) & ~CurrentStation(pending=False))
    def select_current_station(self):
        self.chatbot.send_bot_message(f"I can help to predict delays along the Norwich -> London Liverpool Street line<br>What station are you currently at?")

    # ====== INPUTTING CURRENT TIME ======

    @Rule(Intention(type=Chatbot.IntentionTypes.CONFIRM) 
          & CurrentTime(time=MATCH.current_time, pending=True)
          & ~CurrentStation(name=W(), code=W(), pending=True))
    def confirm_pending_current_time(self, current_time):
        self.chatbot.current_time_fact = self.modify(self.chatbot.current_time_fact, pending=False)
        self.chatbot.last_intention_fact = self.modify(self.chatbot.last_intention_fact, type=Chatbot.IntentionTypes.DELAY_WALKTHROUGH)
        
    @Rule(NOT(Intention(type=Chatbot.IntentionTypes.CONFIRM))
              & CurrentTime(time=MATCH.current_time, pending=True))
    def prompt_current_time_confirmation(self, current_time):
        self.chatbot.send_bot_message(f"Confirm current time {current_time.get_time()}?")

    @Rule(Intention(type=Chatbot.IntentionTypes.DELAY_WALKTHROUGH) 
          & CurrentStation(name=W(), code=W(), pending=False) & ~CurrentTime(pending=False))
    def select_current_time(self):
        self.chatbot.send_bot_message(f"What is the current time?")

    # ====== INPUTTING CURRENT DELAY ======

    @Rule(Intention(type=Chatbot.IntentionTypes.CONFIRM) 
          & CurrentDelay(amount=MATCH.current_delay, pending=True)
          & ~CurrentStation(name=W(), code=W(), pending=True)
          & ~CurrentTime(time=W(), pending=True))
    def confirm_pending_current_delay(self, current_delay):
        self.chatbot.current_delay_fact = self.modify(self.chatbot.current_delay_fact, pending=False)
        self.chatbot.last_intention_fact = self.modify(self.chatbot.last_intention_fact, type=Chatbot.IntentionTypes.DELAY_WALKTHROUGH)
        
    @Rule(NOT(Intention(type=Chatbot.IntentionTypes.CONFIRM))
              & CurrentDelay(amount=MATCH.current_delay, pending=True))
    def prompt_current_delay_confirmation(self, current_delay):
        self.chatbot.send_bot_message(f"Confirm current delay of {current_delay} minutes?")

    @Rule(Intention(type=Chatbot.IntentionTypes.DELAY_WALKTHROUGH) 
          & CurrentStation(name=W(), code=W(), pending=False)
          & CurrentTime(time=W(), pending=False) 
          & ~CurrentDelay(pending=False))
    def select_current_delay(self):
        self.chatbot.send_bot_message(f"What is your current delay (minutes)?")
        self.chatbot.last_intention_fact = self.modify(self.chatbot.last_intention_fact, type=Chatbot.IntentionTypes.DECLARING_DELAY)
        
    # ====== PREDICT DELAY ======
    
    @Rule(CurrentStation(name=MATCH.current_station_name, code=MATCH.current_station_code, pending=False)
          & CurrentTime(time=MATCH.current_time, pending=False)
          & CurrentDelay(amount=MATCH.current_delay, pending=False))
    def predict_delay(self, current_station_name, current_station_code, current_time, current_delay):
        print("Predicting delay")

        data = {
            "current_stop": current_station_code,
            "time": current_time,
            "to_nrw": True,
            "current_delay": current_delay
        }

        delays = find_remaining_delays(data)
        delay_message = f"Further delays from {data['current_stop']} {'towards Norwich' if data['to_nrw'] else 'towards London Liverpool Street'} at {data['time'].get_time()} with {data['current_delay']} minute(s) of delay:<br>"
        for delay in delays:
            mintutes_message = (str(delays[delay]) + " minutes late") if delays[delay] > 0 else (str(delays[delay])[1:] + " minutes early")
            delay_message += f"Delay at {delay}: {mintutes_message}<br>"
        self.chatbot.send_bot_message(delay_message)