from random import choice

from ticket_types import TicketTypes
from cheapest_ticket import NationalRailScraper, TicketTypes
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
        print(f"\n cleared intentions\n{self.facts}\n")
        
    def find_next_station_type(self):
        if self.chatbot.detect_declaring_station(self.chatbot.last_message) == Chatbot.IntentionTypes.DECLARING_ORIGIN_STATION:
            return Chatbot.IntentionTypes.DECLARING_ORIGIN_STATION
        elif self.chatbot.detect_declaring_station(self.chatbot.last_message) == Chatbot.IntentionTypes.DECLARING_DESTINATION_STATION:
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
        
    @Rule(Intention(type=Chatbot.IntentionTypes.TASK1))
    def begin_task_one(self):
        self.chatbot.last_intention_fact = self.modify(self.chatbot.last_intention_fact, type=Chatbot.IntentionTypes.SELECT_TICKET)
    
    @Rule(Intention(type=Chatbot.IntentionTypes.CONFIRM), Ticket(type=W(), pending=True))
    def confirm_pending_ticket(self):
        self.chatbot.ticket_fact = self.modify(self.chatbot.ticket_fact, pending=False)
    
    @Rule(Intention(type=Chatbot.IntentionTypes.SELECT_TICKET))
    def select_ticket(self):
        detected_ticket = self.chatbot.detect_ticket_type(self.chatbot.last_message, 0.9)
        if detected_ticket:
            self.chatbot.ticket_fact = self.modify(self.chatbot.ticket_fact, type=detected_ticket, pending=True)
            self.chatbot.send_bot_message(f"Are you sure you want a {detected_ticket} ticket?")
        else:
            self.chatbot.send_bot_message("What type of ticket do you need? (single, return)")
            
    @Rule(Intention(type=Chatbot.IntentionTypes.CONFIRM), OriginStation(name=W(), code=W(), pending=True))
    def confirm_pending_origin_station(self):
        self.chatbot.origin_station_fact = self.modify(self.chatbot.origin_station_fact, pending=False, needs_confirmation=False)
        
    @Rule(Intention(type=Chatbot.IntentionTypes.CONFIRM), DestinationStation(name=W(), code=W(), pending=True))
    def confirm_pending_destination_station(self):
        self.chatbot.destination_station_fact = self.modify(self.chatbot.destination_station_fact, pending=False, needs_confirmation=False)
            
    @Rule(EXISTS(Intention()), Ticket(type=MATCH.ticket_type, pending=False), OriginStation(pending=True, needs_confirmation=False) | DestinationStation(pending=True, needs_confirmation=False))
    def select_stations(self, ticket_type):
        print("SELECTING STATIONS")
        detected_station = self.chatbot.detect_station_name(self.chatbot.last_message)
        station_type = self.find_next_station_type()
        if detected_station:
            station, code = detected_station
            if station_type == Chatbot.IntentionTypes.DECLARING_ORIGIN_STATION:
                self.chatbot.origin_station_fact = self.modify(self.chatbot.origin_station_fact, name=station, code=code, pending=True, needs_confirmation=True)
            elif station_type == Chatbot.IntentionTypes.DECLARING_DESTINATION_STATION:
                self.chatbot.destination_station_fact = self.modify(self.chatbot.destination_station_fact, name=station, code=code, pending=True, needs_confirmation=True)
            self.chatbot.send_bot_message(f"You chose {station} ({code}). Is that right?")
        else:
            if station_type == Chatbot.IntentionTypes.DECLARING_ORIGIN_STATION:
                self.chatbot.send_bot_message(f"You've selected a {ticket_type} ticket. Where are you travelling from?")
            elif station_type == Chatbot.IntentionTypes.DECLARING_DESTINATION_STATION:
                self.chatbot.send_bot_message(f"You've selected a {ticket_type} ticket. Where are you travelling to?")
                
    @Rule(EXISTS(Intention()),
          Ticket(type=MATCH.ticket_type, pending=False),
          OriginStation(name=MATCH.origin_name, code=MATCH.origin_code, pending=False, needs_confirmation=False),
          DestinationStation(name=MATCH.destination_name, code=MATCH.destination_code, pending=False, needs_confirmation=False),
          ~DepartureTime())
    def select_departure_time(self, ticket_type, origin_name, origin_code, destination_name, destination_code):
        print("selecting departure time")
        detected_departure_time = self.chatbot.detect_date_time(self.chatbot.last_message)
        if detected_departure_time:
            self.declare(DepartureTime(time=detected_departure_time))
            scraper = NationalRailScraper(origin_code, destination_code, detected_departure_time, 1, 0)

            scraper.set_single_ticket(detected_departure_time)

            scraper.launch_scraper()
            scraper.clear_cookies_popup()
            cheapest = scraper.get_cheapest_listed()
            self.chatbot.send_bot_message(f"Cheapest ticket from {origin_name} to {destination_name} leaving after {detected_departure_time}:<br>Departure time: {cheapest['departure_time']}<br>Arrival time: {cheapest['arrival_time']}<br>Duration: {cheapest['length']}<br>Price: {cheapest['price']}<br>Link: <a class='dark' target='_blank' href='{scraper.get_current_url()}'>click here</a>")
        else:
            self.chatbot.send_bot_message(f"When do you want to leave {origin_name} ({origin_code}) to get to {destination_name} ({destination_code})?")
        
    @Rule(Intention(type=Chatbot.IntentionTypes.GREETING))
    def greeting(self):
        self.chatbot.send_bot_message(choice(self.chatbot.intentions["intentions"]["greeting"]["responses"]))
        
    @Rule(Intention(type=Chatbot.IntentionTypes.THANKS))
    def thanks(self):
        self.chatbot.send_bot_message(choice(self.chatbot.intentions["intentions"]["thanks"]["responses"]))
        
    @Rule(OR(Intention(type=Chatbot.IntentionTypes.NONE), Intention(type=Chatbot.IntentionTypes.UNSURE)))
    def confirm(self):
        self.chatbot.send_bot_message("I'm unsure what you mean, but you can ask me about train tickets!")