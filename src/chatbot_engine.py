from random import choice

from ticket_types import TicketTypes
from national_rail_scaper import national_rail_cheapest_ticket
from realtimetickets_scraper import realtimetickets_cheapest_ticket
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
            
    def reset_facts(self):
        self.retract(self.chatbot.ticket_fact)
        self.chatbot.ticket_fact = self.declare(Ticket(pending=True))
        self.retract(self.chatbot.origin_station_fact)
        self.chatbot.origin_station_fact = self.declare(OriginStation(pending=True))
        self.retract(self.chatbot.destination_station_fact)
        self.chatbot.destination_station_fact = self.declare(DestinationStation(pending=True))
        self.retract(self.chatbot.departure_time_fact)
        self.chatbot.departure_time_fact = self.declare(DepartureTime(pending=True))
        self.retract(self.chatbot.departure_date_fact)
        self.chatbot.departure_date_fact = self.declare(DepartureDate(pending=True))
        self.retract(self.chatbot.return_time_fact)
        self.chatbot.return_time_fact = self.declare(ReturnTime(pending=True))
        self.retract(self.chatbot.return_date_fact)
        self.chatbot.return_date_fact = self.declare(ReturnDate(pending=True))
        self.retract(self.chatbot.adult_tickets_fact)
        self.chatbot.adult_tickets_fact = self.declare(AdultTickets(count=1, pending=True))
        self.retract(self.chatbot.child_tickets_fact)
        self.chatbot.child_tickets_fact = self.declare(ChildTickets(count=0, pending=True))
                    
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
    
    @Rule(Intention(type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH) & ~Ticket(pending=False) & ~Ticket(type=W(), pending=True))
    def select_ticket(self):
        self.chatbot.send_bot_message("What type of ticket do you need? (single, return)")
    
    # ====== INPUTTING AN ORIGIN STATION ======
        
    @Rule(Intention(type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH) & Ticket(type=MATCH.ticket_type, pending=True) 
          & ~OriginStation(name=W(), code=W(), pending=True), salience=0)
    def select_origin_station(self, ticket_type):
        self.chatbot.send_bot_message(f"You have selected a {ticket_type} ticket. Where are you travelling from?")
        
    # ====== INPUTTING A DESTINATION STATION ======
        
    @Rule(Intention(type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH) & Ticket(type=MATCH.ticket_type, pending=True) 
          & ~DestinationStation(name=W(), code=W(), pending=True), salience=1)
    def select_destination_station(self, ticket_type):
        self.chatbot.send_bot_message(f"You have selected a {ticket_type} ticket. Where are you travelling to?")
        
    # ====== INPUTTING A DEPARTURE TIME ======
        
    @Rule(Intention(type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH) & Ticket(type=MATCH.ticket_type, pending=True)
          & OriginStation(name=MATCH.origin_name, code=MATCH.origin_code, pending=True)
          & DestinationStation(name=MATCH.destination_name, code=MATCH.destination_code, pending=True)
          & ~DepartureTime(time=W(), pending=True))
    def select_departure_time(self, ticket_type, origin_name, origin_code, destination_name, destination_code):
        self.chatbot.send_bot_message(f"What time (24hr) do you want to leave {origin_name} ({origin_code}) to get to {destination_name} ({destination_code})?")
        
    # ====== INPUTTING A DEPARTURE DATE ======

    @Rule(Intention(type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH) & Ticket(type=MATCH.ticket_type, pending=True)
          & OriginStation(name=MATCH.origin_name, code=MATCH.origin_code, pending=True)
          & DestinationStation(name=MATCH.destination_name, code=MATCH.destination_code, pending=True)
          & ~DepartureDate(date=W(), pending=True))
    def select_departure_date(self, ticket_type, origin_name, origin_code, destination_name, destination_code):
        self.chatbot.send_bot_message(f"What date do you want to leave {origin_name} ({origin_code}) to get to {destination_name} ({destination_code})?")
        
    # ====== INPUTTING RETURN TIME ======

    @Rule(Intention(type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH)
          & Ticket(type=TicketTypes.RETURN, pending=True)
          & OriginStation(name=MATCH.origin_name, code=MATCH.origin_code, pending=True)
          & DestinationStation(name=MATCH.destination_name, code=MATCH.destination_code, pending=True)
          & ~ReturnTime(time=W(), pending=True)
          & DepartureDate(date=W(), pending=True) & DepartureTime(time=W(), pending=True))
    def select_return_time(self, origin_name, origin_code, destination_name, destination_code):
        self.chatbot.send_bot_message(f"What time (24hr) do you want to return to {origin_name} ({origin_code}) from {destination_name} ({destination_code})?")

    # ====== INPUTTING RETURN DATE ======

    @Rule(Intention(type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH)
          & Ticket(type=TicketTypes.RETURN, pending=True)
          & OriginStation(name=MATCH.origin_name, code=MATCH.origin_code, pending=True)
          & DestinationStation(name=MATCH.destination_name, code=MATCH.destination_code, pending=True)
          & ~ReturnDate(date=W(), pending=True)
          & DepartureDate(date=W(), pending=True) & DepartureTime(time=W(), pending=True))
    def select_return_date(self, origin_name, origin_code, destination_name, destination_code):
        self.chatbot.send_bot_message(f"What date do you want to return to {origin_name} ({origin_code}) from {destination_name} ({destination_code})?")
        
    # ====== FINDING CHEAPEST TICKET ======
    
    @Rule(Intention(type=Chatbot.IntentionTypes.CONFIRM)
              & OriginStation(name=MATCH.origin_name, code=MATCH.origin_code, pending=True)
              & DestinationStation(name=MATCH.destination_name, code=MATCH.destination_code, pending=True)
              & DepartureTime(time=MATCH.departure_time, pending=True)
              & DepartureDate(date=MATCH.departure_date, pending=True)
              & (Ticket(type=TicketTypes.SINGLE, pending=True) | (Ticket(type=TicketTypes.RETURN, pending=True) &  ReturnDate(date=MATCH.return_date, pending=True) &  ReturnTime(time=MATCH.return_time, pending=True)))
              & AdultTickets(count=MATCH.adult_tickets)
              & ChildTickets(count=MATCH.child_tickets))
    def confirm_cheapest_ticket_confirmation(self, return_time=None, return_date=None):
        self.chatbot.child_tickets_fact = self.modify(self.chatbot.child_tickets_fact, pending=False)
        self.chatbot.adult_tickets_fact = self.modify(self.chatbot.adult_tickets_fact, pending=False)
        self.chatbot.departure_date_fact = self.modify(self.chatbot.departure_date_fact, pending=False)
        self.chatbot.departure_time_fact = self.modify(self.chatbot.departure_time_fact, pending=False)
        self.chatbot.destination_station_fact = self.modify(self.chatbot.destination_station_fact, pending=False)
        self.chatbot.origin_station_fact = self.modify(self.chatbot.origin_station_fact, pending=False)
        self.chatbot.ticket_fact = self.modify(self.chatbot.ticket_fact, pending=False)
        if return_date != None and return_time != None:
            self.chatbot.return_date_fact = self.modify(self.chatbot.return_date_fact, pending=False)
            self.chatbot.return_time_fact = self.modify(self.chatbot.return_time_fact, pending=False)
        
    @Rule(Intention(type=Chatbot.IntentionTypes.DENY)
              & OriginStation(name=MATCH.origin_name, code=MATCH.origin_code, pending=True)
              & DestinationStation(name=MATCH.destination_name, code=MATCH.destination_code, pending=True)
              & DepartureTime(time=MATCH.departure_time, pending=True)
              & DepartureDate(date=MATCH.departure_date, pending=True)
              & (Ticket(type=TicketTypes.SINGLE, pending=True) | (Ticket(type=TicketTypes.RETURN, pending=True) &  ReturnDate(date=MATCH.return_date, pending=True) &  ReturnTime(time=MATCH.return_time, pending=True)))
              & AdultTickets(count=MATCH.adult_tickets)
              & ChildTickets(count=MATCH.child_tickets))
    def deny_cheapest_ticket_confirmation(self):
        self.reset_facts()
        self.chatbot.send_bot_message("Ticket denied. Please try again")
    
    @Rule(NOT(Intention(type=Chatbot.IntentionTypes.CONFIRM)) 
              & OriginStation(name=MATCH.origin_name, code=MATCH.origin_code, pending=True)
              & DestinationStation(name=MATCH.destination_name, code=MATCH.destination_code, pending=True)
              & DepartureTime(time=MATCH.departure_time, pending=True)
              & DepartureDate(date=MATCH.departure_date, pending=True)
              & (Ticket(type=TicketTypes.SINGLE, pending=True) | (Ticket(type=TicketTypes.RETURN, pending=True) &  ReturnDate(date=MATCH.return_date, pending=True) &  ReturnTime(time=MATCH.return_time, pending=True)))
              & AdultTickets(count=MATCH.adult_tickets)
              & ChildTickets(count=MATCH.child_tickets))
    def prompt_cheapest_ticket_confirmation(self, origin_name, origin_code, destination_name, destination_code, departure_time, departure_date, adult_tickets, child_tickets, return_time=None, return_date=None):
        ticket_type = self.chatbot.ticket_fact["type"]
        confirm_message = (f"Do you want to confirm the following ticket?<br>Ticket type: {ticket_type}<br>Origin station: {origin_name} ({origin_code})"
                           + f"<br>Destination station: {destination_name} ({destination_code})<br>Departure: {departure_date.get_date()} at {departure_time.get_time()}"
                           + f"<br>Adult tickets: {adult_tickets}<br>Child tickets: {child_tickets}")
        
        if ticket_type == TicketTypes.RETURN:
            confirm_message += f"<br>Return: {return_date.get_date()} at {return_time.get_time()}"
            
        self.chatbot.send_bot_message(confirm_message)
    
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
        
        total_departure_date = DateTime(minute=departure_time.get_min(),
                                        hour=departure_time.get_hour(),
                                        day=departure_date.day,
                                        month=departure_date.month)
        
        total_return_date = None
        if ticket_type == TicketTypes.RETURN:
            total_return_date = DateTime(minute=return_time.get_min(),
                                         hour=return_time.get_hour(),
                                         day=return_date.day,
                                         month=return_date.month)


        cheapest_ticket_info = None
        
        nr_cheapest_ticket_info = national_rail_cheapest_ticket(origin_code, destination_code, ticket_type, total_departure_date, total_return_date, adult_count, child_count)
        rtt_cheapest_ticket_info = realtimetickets_cheapest_ticket(origin_name, destination_name, ticket_type, total_departure_date, total_return_date, adult_count, child_count)
        
        if nr_cheapest_ticket_info == None and rtt_cheapest_ticket_info != None:
            cheapest_ticket_info = rtt_cheapest_ticket_info
        elif rtt_cheapest_ticket_info == None and nr_cheapest_ticket_info != None:
            cheapest_ticket_info = nr_cheapest_ticket_info
        elif nr_cheapest_ticket_info != None and rtt_cheapest_ticket_info != None:
            nr_cheapest_ticket, nr_url = nr_cheapest_ticket_info
            rtt_cheapest_ticket, rtt_url = rtt_cheapest_ticket_info
            
            print(f"\nNational Rail cheapest ticket: {nr_cheapest_ticket['price']}")
            print(f"\nRealtimetickets cheapest ticket: {nr_cheapest_ticket['price']}")
            
            if float(nr_cheapest_ticket["price"][1:]) < float(nr_cheapest_ticket["price"][1:]):
                cheapest_ticket_info = (nr_cheapest_ticket, nr_url)
            else:
                cheapest_ticket_info = (rtt_cheapest_ticket, rtt_url)
        
        if cheapest_ticket_info != None:
            cheapest, url = cheapest_ticket_info
            if ticket_type == TicketTypes.SINGLE:
                self.chatbot.send_bot_message(f"Cheapest single ticket from {origin_name} to {destination_name} leaving after {total_departure_date.get_date()}"
                                              + f" at {total_departure_date.get_time()} ({adult_count} adults and {child_count} children):<br>"
                                              + f"🟢 Departure time: {cheapest['departure_time']}<br>🔴 Arrival time: {cheapest['arrival_time']}<br>"
                                              + f"⏰ Duration: {cheapest['length']}<br>💷 Price: {cheapest['price']}<br>"
                                              + f"🌐 Link: <a class='dark' target='_blank' href='{url}'>click here</a>")
            else:
                self.chatbot.send_bot_message(f"Cheapest return ticket from {origin_name} to {destination_name} leaving after {total_departure_date.get_date()}"
                                              + f" at {total_departure_date.get_time()} <br> and returning after {total_return_date.get_date()} at {total_return_date.get_time()}"
                                              + f" ({adult_count} adults and {child_count} children):<br>🟢 Outbound departure time: {cheapest['departure_time']}<br>"
                                              + f"🔴 Outbound arrival time: {cheapest['arrival_time']}<br>🟢 Return departure time: {cheapest['return_departure_time']}<br>"
                                              + f"🔴 Return arrival time: {cheapest['return_arrival_time']}<br>⏰ Outbound duration: {cheapest['length']}<br>"
                                              + f"⏰ Return duration: {cheapest['return_length']}<br>💷 Price: {cheapest['price']}<br>"
                                              + f"🌐 Link: <a class='dark' target='_blank' href='{url}'>click here</a>")
        else:
            self.chatbot.send_bot_message(f"There was an issue with your specified journey")
            
        self.reset_facts()
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
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