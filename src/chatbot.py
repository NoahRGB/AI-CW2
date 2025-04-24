from random import choice
import json
from enum import Enum

from date_time import DateTime
from ticket_types import TicketTypes
from cheapest_ticket import TicketTypes

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
        NONE=8,
        DECLARING_ORIGIN_STATION=9,
        DECLARING_DESTINATION_STATION=10,

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
            elif s == "none":
                return Chatbot.IntentionTypes.NONE
            elif s == "declaring_origin_station":
                return Chatbot.IntentionTypes.DECLARING_ORIGIN_STATION
            elif s == "declaring_destination_station":
                return Chatbot.IntentionTypes.DECLARING_DESTINATION_STATION
            return Chatbot.IntentionTypes.UNSURE


    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")

        self.last_message = None # stores the most recent user input
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

    def find_user_intention(self, user_input, min_similarity=0.7, look_for_stations=True, clean_input=True):
        # find what kind of message the user sent using Chatbot.IntentionTypes
        if clean_input:
            user_input = self.clean_text(user_input)
        user_input_tokens = self.nlp(user_input)

        for intention in self.intentions["intentions"]:
            for pattern in self.intentions["intentions"][intention]["patterns"]:
                sm = SequenceMatcher(None, user_input, pattern).ratio()
                if sm > min_similarity:
                    self.last_intention = Chatbot.IntentionTypes.from_string(intention)
                    return self.last_intention

        if look_for_stations:
            station_detect = self.detect_station_name(user_input)
            if station_detect:
                self.last_intention = Chatbot.IntentionTypes.SELECT_STATION
                return self.last_intention
                    
        self.last_intention = Chatbot.IntentionTypes.UNSURE
        return self.last_intention
    
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
    
    def find_user_ticket_intention(self, user_input):
        # detects whether the input is trying to declare an origin
        # station or a destination station
        to_check = self.split_string(user_input)
        for s in to_check:
            for intention in self.intentions["declaring_stations"]:
                for pattern in self.intentions["declaring_stations"][intention]["patterns"]:
                    similarity = self.nlp(s).similarity(self.nlp(pattern))
                    if similarity > 0.5:
                        return Chatbot.IntentionTypes.from_string(intention)
        return None


    def detect_ticket_type(self, text, min_similarity=0.5):
        # detect whether the text refers to a single ticket or a return ticket
        text_tokens = self.nlp(self.clean_text(text))

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
        
        to_check = text.split(" ")
        
        for text in to_check:
            matches = get_close_matches(text, self.station_dict.keys())
            if len(matches) > 0:
                best_match = matches[0]

                sm = SequenceMatcher(None, text, best_match)
                score = sm.ratio()
                if score >= min_similarity:
                    return best_match, self.station_dict[best_match]
            
        return None
        
    def detect_date_time(self, text):
        # returns one DateTime object for the detected date & time in the provided text
        # returns None if there is no date or time
        text_tokens = self.nlp(text)
        detected_hour, detected_min, detected_day, detected_month = -1, -1, -1, -1

        detected_date = DateTime.find_valid_date(text)
        if detected_date:
            detected_day = int(detected_date.day)
            detected_month = int(detected_date.month)

        detected_time = DateTime.find_valid_time(text)
        if detected_time:
            detected_min = int(detected_time.get_min())
            detected_hour = int(detected_time.get_hour())

        if detected_min == -1 or detected_hour == -1 or detected_day == -1 or detected_month == -1:
            return None
        return DateTime(hour=detected_hour, minute=detected_min, day=detected_day, month=detected_month)
        

    def send_bot_message(self, message):
        print(f"\n{message}\n")