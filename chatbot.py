from random import choice
import json
import re
from enum import Enum

from date_time import DateTime
from ticket_types import TicketTypes
from cheapest_ticket import NationalRailScraper, TicketTypes

from experta import *
from difflib import get_close_matches, SequenceMatcher

import spacy
import spacy.cli

import pickle

import warnings
warnings.filterwarnings('ignore')

# may need to download the spacy english vocabulary
# spacy.cli.download("en_core_web_sm")

class Chatbot:  
    class IntentionTypes(Enum):
        # represents the different intentions that the user can have when they 
        # send a message
        GREETING=1
        EXIT=2,
        TASK1=3,
        UNSURE=4,
        SELECT_TICKET=5,
        CONFIRMATION=6,
        SELECT_STATION=7,

        @staticmethod
        def from_string(s): # turn string into an IntentionTypes enum
            if s == "greeting":
                return Chatbot.IntentionTypes.GREETING
            elif s == "exit":
                return Chatbot.IntentionTypes.EXIT
            elif s == "task1":
                return Chatbot.IntentionTypes.TASK1
            elif s == "single_ticket" or s == "return_ticket":
                return Chatbot.IntentionTypes.SELECT_TICKET
            elif s == "confirm":
                return Chatbot.IntentionTypes.CONFIRMATION
            elif s == "select_station":
                return Chatbot.IntentionTypes.SELECT_STATION
            return Chatbot.IntentionTypes.UNSURE


    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")

        self.last_input = None # stores the most recent user input
        self.last_intention = None # stores the most recent intention
        self.last_intention_fact = None # stores the most recent Experta intention fact

        # load list of UK train stations from generate_stations.py
        with open("./chatbot_data/station_list.pickle", "rb") as f:
            self.station_dict = pickle.load(f)

        # load list of chatbot intentions / patterns / responses
        with open("./chatbot_data/intentions.json") as f:
            self.intentions = json.load(f)
        
    def clean_text(self, text):
        # turn text into tokens (stopwords + punctuation removed)
        tokens = self.nlp(text.lower())
        cleaned_text = ""
        for token in tokens:
            if not token.is_stop and not token.is_punct:
                cleaned_text = cleaned_text + token.text + " "
        return cleaned_text.strip()

    def find_user_intention(self, user_input, min_similarity=0.7):
        # find what kind of message the user sent using Chatbot.IntentionTypes
        cleaned_user_input = self.clean_text(user_input)
        user_input_tokens = self.nlp(cleaned_user_input)

        for intention in self.intentions:
            for pattern in self.intentions[intention]["patterns"]:
                sm = SequenceMatcher(None, cleaned_user_input, pattern).ratio()
                if sm > min_similarity:
                    self.last_intention = Chatbot.IntentionTypes.from_string(intention)
                    return self.last_intention
                
        station_detect = self.detect_station_name(user_input)
        if station_detect:
            self.last_intention = Chatbot.IntentionTypes.SELECT_STATION
            return self.last_intention
        
        self.last_intention = Chatbot.IntentionTypes.UNSURE
        return self.last_intention

    def detect_ticket_type(self, text, min_similarity=0.5):
        # detect whether the text refers to a single ticket or a return ricket
        text_tokens = self.nlp(self.clean_text(text))

        for single_text in self.intentions["single_ticket"]["patterns"]:
            single_text_tokens = self.nlp(self.clean_text(single_text))
            if single_text_tokens.similarity(text_tokens) > min_similarity:
                return TicketTypes.SINGLE
            
        for return_text in self.intentions["return_ticket"]["patterns"]:
            return_text_tokens = self.nlp(self.clean_text(return_text))
            if return_text_tokens.similarity(text_tokens) > min_similarity:
                return TicketTypes.RETURN
            
        return False

    def detect_station_name(self, text):
        # find the most similar match in text from the list of
        # UK train stations. will only return a match if the
        # similarity to at least one station is over 60%
        text_tokens = self.nlp(self.clean_text(text))
        min_similarity = 0.6

        matches = get_close_matches(text, self.station_dict.keys())
        if len(matches) > 0:
            best_match = matches[0]
        else:
            return None
        
        sm = SequenceMatcher(None, text, best_match)
        score = sm.ratio()

        if score >= min_similarity:
            return best_match, self.station_dict[best_match]
        else:
            return None
        
    def detect_date_time(self, text):
        # returns one DateTime object for the detected date & time in the provided text
        # returns None if there is no date or time
        text_tokens = self.nlp(text)
        detected_hour, detected_min, detected_day, detected_month = -1, -1, -1, -1

        detected_date = DateTime.find_valid_date(text)
        detected_day = int(detected_date.day)
        detected_month = int(detected_date.month)

        detected_time = DateTime.find_valid_time(text)
        detected_min = int(detected_time.get_min())
        detected_hour = int(detected_time.get_hour())

        if detected_min == -1 or detected_hour == -1 or detected_day == -1 or detected_month == -1:
            return None
        return DateTime(hour=detected_hour, minute=detected_min, day=detected_day, month=detected_month)
        

    def send_bot_message(self, message):
        print(f"\n{message}\n")


class Intention(Fact):
    # information about current user intention
    # e.g. gretting, exit, task1, task2
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

    def verify_station_choice(self, station_choice):
        # detects train stations in the given text and returns the most similar  
        # one if the user confirms that it is correct, otherwise returns None
        detected_origin_station = self.chatbot.detect_station_name(station_choice)
        if detected_origin_station:
            station, code = detected_origin_station
            station = station.title()
            code = code.upper()
            self.chatbot.send_bot_message(f"You chose {station} ({code}). Is that right?")
            confirmation_input = input()
            confirmation_input_intention = self.chatbot.find_user_intention(confirmation_input, 0.8)
            if confirmation_input_intention == Chatbot.IntentionTypes.CONFIRMATION:
                return station, code
            else:
                return None

    @DefFacts()
    def setup(self):
        # setup the initial facts 
        yield Intention(type=Chatbot.IntentionTypes.UNSURE)

    @Rule(Intention(type=Chatbot.IntentionTypes.TASK1), NOT(Ticket(type=W)))
    def task1_setup(self):
        # user seems to want to start task 1, so modify the intention to selecting a ticket
        chatbot.last_intention_fact = self.modify(chatbot.last_intention_fact, type=Chatbot.IntentionTypes.SELECT_TICKET)

    @Rule(Intention(type=Chatbot.IntentionTypes.SELECT_TICKET))
    def select_ticket(self):
        # need to select a return/single ticket
        found_type = None

        # check if the last message sent was a ticket type
        initial_check = self.chatbot.detect_ticket_type(self.chatbot.last_message, 0.7)
        if initial_check:
            found_type = initial_check
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

    @Rule(OR(AND(Intention(type=Chatbot.IntentionTypes.SELECT_STATION), Ticket(type=MATCH.ticket_type)), Ticket(type=MATCH.ticket_type)))
    def select_origin_station(self, ticket_type):
        # already selected a ticket type, need to select origin train station

        if self.chatbot.last_intention == Chatbot.IntentionTypes.SELECT_STATION:
            # check if the last message sent was a valid train station
            initial_check = self.verify_station_choice(self.chatbot.last_message)
            if initial_check:
                station, code = initial_check
                self.declare(OriginStation(name=station, code=code))
        else:
            # if it wasn't prompt the user to input a train station
            self.chatbot.send_bot_message(f"You want a {ticket_type} ticket. Where do you want to start your journey?")
            origin_input = input()
            detected_station = self.verify_station_choice(origin_input)
            if detected_station:
                station, code = detected_station
                self.declare(OriginStation(name=station, code=code))
            else:
                self.chatbot.send_bot_message("There seems to have been an issue. Try spelling your station differently, or ask me for something else")
        
    @Rule(OR(AND(Intention(type=Chatbot.IntentionTypes.SELECT_STATION), Ticket(type=MATCH.ticket_type), OriginStation(name=MATCH.origin_name, code=MATCH.origin_code)), AND(Ticket(type=MATCH.ticket_type), OriginStation(name=MATCH.origin_name, code=MATCH.origin_code))))
    def select_destination_station(self, ticket_type, origin_name, origin_code):
        # already selected ticket type & origin satation, need to select destination station
        
        if self.chatbot.last_intention == Chatbot.IntentionTypes.SELECT_STATION:
            # check if the last message sent was a valid train station
            initial_check = self.verify_station_choice(self.chatbot.last_message)
            if initial_check:
                station, code = initial_check
                self.declare(DestinationStation(name=station, code=code))
        else:
            # if it wasn't prompt the user to input a train station
            self.chatbot.send_bot_message(f"You want a {ticket_type} ticket from {origin_name} ({origin_code}). Where do you want to go?")
            destination_input = input()
            detected_station = self.verify_station_choice(destination_input)
            if detected_station:
                station, code = detected_station
                self.declare(DestinationStation(name=station, code=code))
            else:
                self.chatbot.send_bot_message("There seems to have been an issue. Try spelling your station differently, or ask me for something else")
    
    @Rule(Ticket(type=MATCH.ticket_type), OriginStation(name=MATCH.origin_name, code=MATCH.origin_code), DestinationStation(name=MATCH.destination_name, code=MATCH.destination_code))
    def select_departure_time(self, ticket_type, origin_name, origin_code, destination_name, destination_code):
        # already selected ticket type & origin/desintaiton station, need to select a departure time

        self.chatbot.send_bot_message(f"When do you want to leave {origin_name} ({origin_code}) to get to {destination_name} ({destination_code})?")
        departure_time_input = input()
        detected_departure_time = chatbot.detect_date_time(departure_time_input)
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
                detected_return_time = chatbot.detect_date_time(return_time_input)
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
        self.chatbot.send_bot_message(choice(self.chatbot.intentions["greeting"]["responses"]))

    @Rule(Intention(type=Chatbot.IntentionTypes.EXIT))
    def exit_message(self):
        self.chatbot.send_bot_message(choice(self.chatbot.intentions["exit"]["responses"]))

    @Rule(Intention(type=Chatbot.IntentionTypes.UNSURE))
    def unsure_message(self):
        self.chatbot.send_bot_message("I'm unsure what you mean, but you can ask me about train tickets!")


    
########################## RUN ######################################

chatbot = Chatbot()

chatbot_engine = ChatbotEngine(chatbot)
chatbot_engine.reset()

chatbot.find_user_intention("Hey")
chatbot.last_intention_fact = chatbot_engine.modify(chatbot_engine.facts[1], type=chatbot.last_intention)
chatbot_engine.run()

while True:
    test_input = input()
    chatbot.find_user_intention(test_input)
    chatbot.last_intention_fact = chatbot_engine.modify(chatbot.last_intention_fact, type=chatbot.last_intention)
    chatbot.last_message = test_input

    print(f"\n{chatbot_engine.facts}\n")
    chatbot_engine.run()
