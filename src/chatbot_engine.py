from random import choice

from ticket_types import TicketTypes
from cheapest_ticket import NationalRailScraper, TicketTypes

from experta import *
from difflib import get_close_matches, SequenceMatcher

import warnings
warnings.filterwarnings('ignore')

from chatbot import Chatbot

class Intention(Fact):
    # information about current user intention
    # e.g. greeting, exit, task1, task2
    pass

class Ticket(Fact):
    # information about a ticket
    # e.g. single, return
    pass

class OriginStation(Fact):
    # information about the origin station
    # e.g. norwich (nrw), ipswich (ips), etc.
    pass

class DestinationStation(Fact):
    # information about the destination station
    # e.g. norwich (nrw), ipswich (ips), etc.
    pass

class DepartureTime(Fact):
    # information about the departure time
    # stores a DateTime object
    pass

class ReturnTime(Fact):
    # information about the return time
    # stores a DateTime object
    pass

class ChatbotEngine(KnowledgeEngine):
    def __init__(self, chatbot):
        KnowledgeEngine.__init__(self)
        self.chatbot = chatbot

    def clear_chatbot_intention(self):
        self.chatbot.last_intention = Chatbot.IntentionTypes.NONE
        self.chatbot.last_intention_fact = self.modify(self.chatbot.last_intention_fact, type=self.chatbot.last_intention)
    
    def has_fact(self, fact):
        # returns True if a fact exists of the given type in the engine
        # otherwise False
        return any(isinstance(f, fact) for f in self.facts.values())
        
    def prompt_confirmation(self, confirm_message):
        # asks for confirmation using the given message and returns True
        # if the user confirms the message and False otherwise
        self.chatbot.send_bot_message(f"I've detected that {confirm_message}. Is that right?")
        confirmation_input = input()
        confirmation_input_intention = self.chatbot.find_user_intention(confirmation_input, 0.8)
        if confirmation_input_intention == Chatbot.IntentionTypes.CONFIRMATION:
            return True
        else:
            return False

    def verify_station_choice(self, station_choice):
        # detects train stations in the given text and returns the most similar  
        # one if the user confirms that it is correct, otherwise returns None
        detected_station = self.chatbot.detect_station_name(station_choice)
        if detected_station:
            station, code = detected_station
            station = station.title()
            code = code.upper()
            if self.prompt_confirmation(f"you chose {station} ({code})"):
                return station, code
            return None

    @DefFacts()
    def setup(self):
        # setup the initial facts 
        yield Intention(type=Chatbot.IntentionTypes.UNSURE)

    @Rule(Intention(type=Chatbot.IntentionTypes.TASK1), NOT(Ticket(type=W)))
    def task1_setup(self):
        # user seems to want to start task 1, so modify the intention to selecting a ticket
        # print(self.detect_all_info(self.chatbot.last_message))
        self.chatbot.last_intention_fact = self.modify(self.chatbot.last_intention_fact, type=Chatbot.IntentionTypes.SELECT_TICKET)

    @Rule(Intention(type=Chatbot.IntentionTypes.SELECT_TICKET), AS.ticket_fact << Ticket(type=MATCH.ticket_type))
    def change_ticket_type(self, ticket_type):
        # trying to select a ticket type when there is already one selected
        self.chatbot.send_bot_message(f"You already have a {ticket_type} ticket selected. Do you want to select a new one?")
        confirmation_input = input()
        if self.chatbot.find_user_intention(confirmation_input) == Chatbot.IntentionTypes.CONFIRMATION:
            # need to retract the old Ticket fact so that a new one can be selected
            for fact_id, fact in self.facts.items():
                if isinstance(fact, Ticket):
                    self.retract(fact_id)
                    break
            self.select_ticket()
        else:
            self.chatbot.send_bot_message(f"Ok, you still have a {ticket_type} ticket selected")

    @Rule(OR(OR(AND(~Ticket(), EXISTS(DestinationStation())), AND(~Ticket(), EXISTS(OriginStation())),
             Intention(type=Chatbot.IntentionTypes.SELECT_TICKET))))
    def select_ticket(self):
        # need to select a return/single ticket
        found_type = None

        # check if the last message sent was a ticket type
        initial_check = self.chatbot.detect_ticket_type(self.chatbot.last_message, 0.9)
        if initial_check:
            found_type = initial_check
            self.chatbot.send_bot_message(f"You have selected a {found_type} ticket. Where are you travelling from?")
        else:
            # if it wasn't, prompt the user for a ticket type
            self.chatbot.send_bot_message("What kind of ticket do you want? (single, return)")
            ticket_input = input()
            ticket_type = self.chatbot.detect_ticket_type(ticket_input, 0.9)
            if ticket_type:
                found_type = ticket_type
            else:
                self.chatbot.send_bot_message("I don't know that ticket type. Try again...")

        if found_type: self.declare(Ticket(type=found_type))
        self.clear_chatbot_intention()
        
    @Rule(OR(Intention(type=Chatbot.IntentionTypes.SELECT_STATION), 
             AND(Ticket(type=MATCH.ticket_type), OR(~OriginStation(), ~DestinationStation()))))
    def select_station(self, ticket_type=None):
        
        if self.chatbot.last_intention == Chatbot.IntentionTypes.SELECT_STATION:
            # check if the last message sent was a valid train station
            
            detected_station = self.verify_station_choice(self.chatbot.last_message)
            last = self.chatbot.last_message.split(" ")
            if detected_station:
                station, code = detected_station
                
                # find whether the detected station is meant to be an origin station or
                # a destination station and declare it
                intention = self.chatbot.find_user_ticket_intention(self.chatbot.last_message)
                if intention == Chatbot.IntentionTypes.DECLARING_DESTINATION_STATION:
                    self.declare(DestinationStation(name=station, code=code))
                elif intention == Chatbot.IntentionTypes.DECLARING_ORIGIN_STATION:
                    self.declare(OriginStation(name=station, code=code))
                else:
                    if not self.has_fact(OriginStation):
                        self.declare(OriginStation(name=station, code=code))  
                    elif not self.has_fact(DestinationStation): 
                        self.declare(DestinationStation(name=station, code=code))
        else:
            # if the last message sent wasn't a valid train station, then prompt the user for
            # a station 
            
            # decide whether the user needs to input an origin or destination station
            looking_for_origin_station = False
            if not self.has_fact(OriginStation):
                looking_for_origin_station = True
                self.chatbot.send_bot_message(f"You have selected a {ticket_type} ticket. Where do you want to travel from?")
            elif not self.has_fact(DestinationStation): 
                looking_for_origin_station = False
                self.chatbot.send_bot_message(f"You have selected a {ticket_type} ticket. Where do you want to travel to?")

            station_input = input()
            detected_station = self.verify_station_choice(station_input)
            if detected_station:
                station, code = detected_station
                if looking_for_origin_station:
                    self.declare(OriginStation(name=station, code=code))
                    if ~DestinationStation():
                        self.chatbot.send_bot_message(f"You have selected {station} station. Where do you want to travel to?")
                else:
                    self.declare(DestinationStation(name=station, code=code))
                    if ~OriginStation():
                        self.chatbot.send_bot_message(f"You have selected {station} station. Where do you want to travel to?")
            else:
                self.chatbot.send_bot_message("There seems to have been an issue. Try spelling your station differently, or ask me for something else")
                self.clear_chatbot_intention()
    
    @Rule(Ticket(type=MATCH.ticket_type), 
          OriginStation(name=MATCH.origin_name, code=MATCH.origin_code), 
          DestinationStation(name=MATCH.destination_name, code=MATCH.destination_code))
    def select_departure_time(self, ticket_type, origin_name, origin_code, destination_name, destination_code):
        # already selected ticket type & origin/destination station, need to select a departure time

        self.chatbot.send_bot_message(f"When do you want to leave {origin_name} ({origin_code}) to get to {destination_name} ({destination_code})?")
        departure_time_input = input()
        detected_departure_time = self.chatbot.detect_date_time(departure_time_input)
        if detected_departure_time is None:
            self.chatbot.send_bot_message("Sorry, I don't understand that date or time")
        else:
            self.declare(DepartureTime(time=detected_departure_time))
            scraper = NationalRailScraper(origin_code, destination_code, detected_departure_time, 1, 0)
            if ticket_type is TicketTypes.SINGLE:
                scraper.set_single_ticket(detected_departure_time)
            else:
                self.chatbot.send_bot_message(f"When do you want to return from {destination_name} ({destination_code}) to get back to {origin_name} ({origin_code})?")
                return_time_input = input()
                detected_return_time = self.chatbot.detect_date_time(return_time_input)
                if detected_return_time is None:
                    self.chatbot.send_bot_message("Sorry, I don't understand that date or time")
                else:
                    self.declare(ReturnTime(time=detected_return_time))
                    scraper.set_return_ticket(detected_departure_time, detected_return_time)
            scraper.launch_scraper()
            scraper.clear_cookies_popup()
            self.chatbot.send_bot_message("Finding cheapest ticket...")
            cheapest = scraper.get_cheapest_listed()
            self.chatbot.send_bot_message(f"Cheapest ticket:\nDeparture time: {cheapest['departure_time']}\nArrival time: {cheapest['arrival_time']}\nDuration: {cheapest['length']}\nPrice: {cheapest['price']}\nLink: {scraper.get_current_url()}")

    @Rule(Intention(type=Chatbot.IntentionTypes.GREETING))
    def greeting_message(self):
        self.chatbot.send_bot_message(choice(self.chatbot.intentions["intentions"]["greeting"]["responses"]))

    @Rule(Intention(type=Chatbot.IntentionTypes.EXIT))
    def exit_message(self):
        self.chatbot.send_bot_message(choice(self.chatbot.intentions["exit"]["responses"]))

    @Rule(Intention(type=Chatbot.IntentionTypes.UNSURE))
    def unsure_message(self):
        self.chatbot.send_bot_message("I'm unsure what you mean, but you can ask me about train tickets!")
