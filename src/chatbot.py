from random import choice
import json
from enum import Enum

from date_time import DateTime
from ticket_types import TicketTypes

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
        UNSURE=1,
        GREETING=2,
        TICKET_WALKTHROUGH=3,
        SELECT_TICKET=4,
        NONE=5,
        CONFIRM=6,
        SELECT_STATION=7,
        DECLARING_ORIGIN_STATION=8,
        DECLARING_DESTINATION_STATION=9,
        THANKS=10,
        EXIT=11,

        @staticmethod
        def from_string(s): # turn string into an IntentionTypes enum
            if s == "greeting":
                return Chatbot.IntentionTypes.GREETING
            elif s == "task1":
                return Chatbot.IntentionTypes.TICKET_WALKTHROUGH
            elif s == "single_ticket" or s == "return_ticket":
                return Chatbot.IntentionTypes.SELECT_TICKET
            elif s == "none":
                return Chatbot.IntentionTypes.NONE
            elif s == "confirm":
                return Chatbot.IntentionTypes.CONFIRM
            elif s == "select_station":
                return Chatbot.IntentionTypes.SELECT_STATION
            elif s == "declaring_origin_station":
                return Chatbot.IntentionTypes.DECLARING_ORIGIN_STATION
            elif s == "declaring_destination_station":
                return Chatbot.IntentionTypes.DECLARING_DESTINATION_STATION
            elif s == "thanks":
                return Chatbot.IntentionTypes.THANKS
            elif s == "exit":
                return Chatbot.IntentionTypes.EXIT
            else:
                return Chatbot.IntentionTypes.UNSURE

    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")

        self.last_user_message = None # stores the most recent user input
        self.last_intention = None # stores the most recent intention
        self.last_intention_fact = None # stores the most recent Experta intention fact
        self.last_chatbot_message = None # stores the most recent chatbot message

        # load list of UK train stations from generate_stations.py
        with open("../chatbot_data/station_list.pickle", "rb") as f:
            self.station_dict = pickle.load(f)

        # load list of chatbot intentions / patterns / responses
        with open("../chatbot_data/intentions.json") as f:
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
        user_input = self.clean_text(user_input.lower())
        user_input_tokens = self.nlp(user_input)

        for intention in self.intentions["intentions"]:
            for pattern in self.intentions["intentions"][intention]["patterns"]:
                sm = SequenceMatcher(None, user_input, pattern).ratio()
                if sm > min_similarity:
                    self.last_intention = Chatbot.IntentionTypes.from_string(intention)
                    return self.last_intention
                    
        self.last_intention = Chatbot.IntentionTypes.UNSURE
        return self.last_intention
    
    def detect_ticket_type(self, text, min_similarity=0.9):
        # detect whether the text refers to a single ticket or a return ticket
        to_check = self.split_string(text)
        to_check = [self.nlp(self.clean_text(t)) for t in to_check]
        # text_tokens = self.nlp(self.clean_text(text))

        for text_tokens in to_check:
            for single_text in self.intentions["intentions"]["single_ticket"]["patterns"]:
                single_text_tokens = self.nlp(self.clean_text(single_text))
                if single_text_tokens.similarity(text_tokens) > min_similarity:
                    return TicketTypes.SINGLE
                
            for return_text in self.intentions["intentions"]["return_ticket"]["patterns"]:
                return_text_tokens = self.nlp(self.clean_text(return_text))
                if return_text_tokens.similarity(text_tokens) > min_similarity:
                    return TicketTypes.RETURN
            
        return False
    
    def detect_station_name(self, text):
        # find the most similar match in text from the list of
        # UK train stations. will only return a match if the
        # similarity to at least one station is over 60%
        text_tokens = self.nlp(self.clean_text(text))
        min_similarity = 0.9
        detected_stations = []
        to_check = text.split(" ")
        
        for part in to_check:
            part = part.lower()
            matches = get_close_matches(part, self.station_dict.keys())
            if len(matches) > 0:
                best_match = matches[0]

                sm = SequenceMatcher(None, part, best_match)
                score = sm.ratio()
                if score >= min_similarity:
                    detected_stations.append((best_match.title(), self.station_dict[best_match].upper(), self.find_station_type(text, best_match)))
            
        return None if len(detected_stations) == 0 else detected_stations
    
    def find_station_type(self, user_input, station_name):
        before_station_name = user_input[:user_input.find(station_name)]
        to_check = self.split_string(before_station_name)
        declarations_found = []
        for s in to_check:
            for intention in self.intentions["declaring_stations"]:
                matches = get_close_matches(s, self.intentions["declaring_stations"][intention]["patterns"])
                if len(matches) > 0:
                    best_match = matches[0]
                    sm = SequenceMatcher(None, s, best_match)
                    score = sm.ratio()
                    if score >= 0.8:
                        declarations_found.append(Chatbot.IntentionTypes.from_string(intention))
                
                
        return None if len(declarations_found) == 0 else declarations_found[len(declarations_found) - 1]
    
    def split_string(self, s):
        # turns a string into every possible combination 
        # of words e.g. "i want a ticket" turns into
        # ["i", "i want", "i want a", "i want a ticket", ...]
        split = [s]
        s = s.split(" ")
        for i in range(0, len(s)):
            current = ""
            for j in range(i, len(s)):
                current += f" {s[j]}"
                split.append(current)
        return split
    
    def detect_date(self, text):
        text_tokens = self.nlp(text)
        detected_day, detected_month = None, None
        detected_date = DateTime.find_valid_date(text)
        if detected_date:
            detected_day = int(detected_date.day)
            detected_month = int(detected_date.month)

        if detected_day == None or detected_month == None:
            return None
        return DateTime(day=detected_day, month=detected_month)

    def detect_time(self, text):
        text_tokens = self.nlp(text)
        detected_hour, detected_min = None, None
        detected_time = DateTime.find_valid_time(text)
        if detected_time:
            detected_min = int(detected_time.get_min())
            detected_hour = int(detected_time.get_hour())

        if detected_min == None or detected_hour == None:
            return None
        return DateTime(hour=detected_hour, minute=detected_min)
    
    def detect_adults(self, message):
        to_check = self.split_string(message)
        
        for text in to_check:
            matches = get_close_matches(text, self.intentions["adults"]["patterns"])
            if len(matches) > 0:
                best_match = matches[0]
                sm = SequenceMatcher(None, text, best_match)
                score = sm.ratio()
                if score >= 0.8:
                    adult_count = self.find_closest_number(message, best_match)
                    if adult_count:
                        return adult_count
        return None
    
    def detect_children(self, message):
        to_check = self.split_string(message)
        
        for text in to_check:
            matches = get_close_matches(text, self.intentions["children"]["patterns"])
            if len(matches) > 0:
                best_match = matches[0]
                sm = SequenceMatcher(None, text, best_match)
                score = sm.ratio()
                if score >= 0.8:
                    children_count = self.find_closest_number(message, best_match)
                    if children_count:
                        return children_count
        return None
    
    def find_closest_number(self, text, word):
        split_text = text.split(" ")
        print(f"{split_text}, {word}")
        index = split_text.index(word)
        before, after = None, None
        if index != 0:
            before = split_text[index - 1]
        if index != (len(split_text) - 1):
            after = split_text[index + 1]
        
        if before and before.isnumeric():
            return int(before) 
        elif after and after.isnumeric():
            return int(after)
        return None
    
    def detect_all_information(self, message):
        detected = {}
        
        # find any ticket types in message
        detected_ticket = self.detect_ticket_type(message)
        if detected_ticket:
            detected["ticket"] = detected_ticket
        
        # find any stations in message
        detected_stations = self.detect_station_name(message)
        if detected_stations:
            for station in detected_stations:
                name, code, type = station
                if type:
                    if type == Chatbot.IntentionTypes.DECLARING_ORIGIN_STATION:
                        detected["origin_station"] = (name, code)
                    elif type == Chatbot.IntentionTypes.DECLARING_DESTINATION_STATION:
                        detected["destination_station"] = (name, code)
                else:
                    if "name" not in self.origin_station_fact:
                        detected["origin_station"] = (name, code)
                    elif "name" not in self.destination_station_fact:
                        detected["destination_station"] = (name, code)

        # find any times in message
        detected_time = self.detect_time(message)
        if detected_time:
            detected["time"] = detected_time
        
        # find any dates in message
        detected_date = self.detect_date(message)
        if detected_date:
            detected["date"] = detected_date
            
        # find any adults in message
        detected_adults = self.detect_adults(message);
        if detected_adults:
            detected["adults"] = detected_adults
            
        # find any children in message
        detected_children = self.detect_children(message);
        if detected_children:
            detected["children"] = detected_children
            
        # return everything that was found
        return detected

    def send_bot_message(self, message):
        print(f"\n{message}\n")
        self.last_chatbot_message = message