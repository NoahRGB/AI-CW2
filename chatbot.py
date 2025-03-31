from random import choice
import json
import re
from enum import Enum

from DateTime import DateTime
from cheapest_ticket import NationalRailScraper, TicketTypes

from experta import *
from difflib import get_close_matches, SequenceMatcher

import spacy
import spacy.cli

import pickle

import warnings
warnings.filterwarnings('ignore')
# spacy.cli.download("en_core_web_sm")

class Chatbot:  
    class IntentionTypes(Enum):
        GREETING=1
        EXIT=2,
        TASK1=3,
        UNSURE=4,
        SELECT_TICKET=5,
        CONFIRMATION=6,

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
            return Chatbot.IntentionTypes.UNSURE


    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.sentences_path = "./chatbot_data/sentences.txt"
        self.intentions_path = "./chatbot_data/intentions.json"
        self.responses_path = "./chatbot_data/responses.json"
        # self.month_list = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]

        self.last_intention = None # stores the most recent intention
        self.last_intention_fact = None # stores the most recent Experta intention fact

        with open("./chatbot_data/station_list.pickle", "rb") as f:
            self.station_dict = pickle.load(f)

        with open(self.intentions_path) as f:
            self.intentions = json.load(f)

        with open(self.responses_path) as f:
            self.responses = json.load(f)

        # get sentences from self.sentences_path and turn them into
        # intention_labels and formatted sentences
        self.intention_labels, self.sentences = [], []
        with open(self.sentences_path) as file:
            for line in file:
                parts = line.split(" | ")
                if parts[0] == "task1":
                    self.intention_labels.append("task1")
                elif parts[0] == "exit":
                    self.intention_labels.append("exit")
                else:
                    self.intention_labels.append("greeting")
                sentence_tokens = self.nlp(parts[1])
                self.sentences.append(sentence_tokens.text.lower().strip())
        
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
                
        self.last_intention = Chatbot.IntentionTypes.UNSURE
        return self.last_intention

    def detect_ticket_type(self, text, min_similarity=0.5):
        # detect whether the text refers to a single ticket or
        # a return ricket
        text_tokens = self.nlp(self.clean_text(text))

        for single_text in self.intentions["single_ticket"]["patterns"]:
            single_text_tokens = self.nlp(self.clean_text(single_text))
            if single_text_tokens.similarity(text_tokens) > min_similarity:
                return "single"
            
        for return_text in self.intentions["return_ticket"]["patterns"]:
            return_text_tokens = self.nlp(self.clean_text(return_text))
            if return_text_tokens.similarity(text_tokens) > min_similarity:
                return "return"
            
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
            return {best_match:self.station_dict[best_match]}
        else:
            return None
        
    def detect_date_time(self, text):
        # returns one DateTime object for the detected date & time in the provided text
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
        return DateTime(detected_hour, detected_min, detected_day, detected_month)
        

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

class ChatbotEngine(KnowledgeEngine):
    def __init__(self, chatbot):
        KnowledgeEngine.__init__(self)
        self.chatbot = chatbot

    @DefFacts()
    def setup(self):
        yield Intention(type=Chatbot.IntentionTypes.UNSURE)
        
    @Rule(Intention(type=Chatbot.IntentionTypes.GREETING))
    def greeting_message(self):
        self.chatbot.send_bot_message(choice(self.chatbot.responses["greeting"]))

    @Rule(Intention(type=Chatbot.IntentionTypes.EXIT))
    def exit_message(self):
        self.chatbot.send_bot_message(choice(self.chatbot.responses["exit"]))

    @Rule(AND(Intention(type=Chatbot.IntentionTypes.TASK1), NOT(Ticket(type=W))))
    def task1_setup(self):
        self.chatbot.send_bot_message(choice(self.chatbot.responses["task1_setup"]))
        chatbot.last_intention_fact = self.modify(chatbot.last_intention_fact, type=Chatbot.IntentionTypes.SELECT_TICKET)

    @Rule(Intention(type=Chatbot.IntentionTypes.SELECT_TICKET))
    def select_ticket(self):
        # need to select a return/single ticket
        ticket_input = input()
        chatbot.find_user_intention(ticket_input)
        ticket_type = self.chatbot.detect_ticket_type(ticket_input, 0.9)
        if ticket_type:
            ticket_type_resolved = True
            if ticket_type == "single":
                self.declare(Ticket(type="single"))

            elif ticket_type == "return":
                self.declare(Ticket(type="return"))
        elif ticket_type == False:
            self.chatbot.send_bot_message("I don't know that ticket type. Try again...")

    @Rule(Ticket(type=MATCH.ticket_type))
    def select_origin_station(self, ticket_type):
        # already selected a ticket type, need to select origin train station
        self.chatbot.send_bot_message(f"You want a {ticket_type} ticket. Where do you want to start your journey?")
        origin_input = input()
        detected_origin_stations = self.chatbot.detect_station_name(origin_input)

        if detected_origin_stations:
            for station in detected_origin_stations:
                self.chatbot.send_bot_message(f"You want to leave from {station} ({detected_origin_stations[station].upper()}). Is that right?")
                confirmation_input = input()
                confirmation_input_intention = self.chatbot.find_user_intention(confirmation_input, 0.8)
                if confirmation_input_intention == Chatbot.IntentionTypes.CONFIRMATION:
                    self.declare(OriginStation(name=station, code=self.chatbot.station_dict[station]))
                else:
                    self.chatbot.send_bot_message("Sorry, my mistake")
        else:
            self.chatbot.send_bot_message("I don't know that station. Try spelling it differently, or ask me for something else")
        
    @Rule(Ticket(type=MATCH.ticket_type), OriginStation(name=MATCH.origin_name, code=MATCH.origin_code))
    def select_destination_station(self, ticket_type, origin_name, origin_code):
        # already selected ticket type & origin satation, need to select destination
        self.chatbot.send_bot_message(f"You want a {ticket_type} ticket from {origin_name} ({origin_code}). Where do you want to go?")
        destination_input = input()
        detected_destination_stations = self.chatbot.detect_station_name(destination_input)

        if detected_destination_stations:
            for station in detected_destination_stations:
                self.chatbot.send_bot_message(f"You want to go to {station} ({detected_destination_stations[station].upper()}). Is that right?")
                confirmation_input = input()
                confirmation_input_intention = self.chatbot.find_user_intention(confirmation_input, 0.8)
                if confirmation_input_intention == Chatbot.IntentionTypes.CONFIRMATION:
                    self.declare(DestinationStation(name=station, code=self.chatbot.station_dict[station]))
                else:
                    self.chatbot.send_bot_message("Sorry, my mistake")
        else:
            self.chatbot.send_bot_message("I don't know that station. Try spelling it differently, or ask me for something else")
    
    @Rule(Ticket(type=MATCH.ticket_type), OriginStation(name=MATCH.origin_name, code=MATCH.origin_code), DestinationStation(name=MATCH.destination_name, code=MATCH.destination_code))
    def select_departure_time(self, origin_name, origin_code, destination_name, destination_code):
        # already selected ticket type & origin/desintaiton, need to select departure time
        self.chatbot.send_bot_message(f"When do you want to leave {origin_name} ({origin_code}) to get to {destination_name} ({destination_code})?")
        departure_time_input = input()
        detected_date_time = chatbot.detect_date_time(departure_time_input)
        if detected_date_time is None:
            self.chatbot.send_bot_message("Sorry, I don't understand that date or time")
        else:
            self.declare(DepartureTime(time=detected_date_time))
            scraper = NationalRailScraper(origin_code, destination_code, detected_date_time, 1, 0)
            scraper.set_single_ticket(detected_date_time)
            scraper.launch_scraper()
            scraper.clear_cookies_popup()
            cheapest = scraper.get_cheapest_listed()
            self.chatbot.send_bot_message("Finding cheapest ticket...")
            self.chatbot.send_bot_message(f"Cheapest ticket:\nDeparture time: {cheapest['departure_time']}\nArrival time: {cheapest['arrival_time']}\nDuration: {cheapest['length']}\nPrice: {cheapest['price']}")

    @Rule(Intention(type=Chatbot.IntentionTypes.UNSURE))
    def unsure_message(self):
        self.chatbot.send_bot_message("I'm unsure what you mean, but you can ask me about train tickets!")


    
################################################################

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

    # print(f"\n{chatbot_engine.facts}\n")
    chatbot_engine.run()

# https://www.nationalrail.co.uk/journey-planner/?origin=nrw&destination=ips&leavingDate=310325&adults=1&children=0&leavingType=departing&extraTime=0&type=single&leavingHour=00&leavingMin=15
# https://www.nationalrail.co.uk/journey-planner/?type=single&origin=NRW&destination=IPS&leavingType=departing&leavingDate=310325&leavingHour=15&leavingMin=00&adults=1&extraTime=0#O