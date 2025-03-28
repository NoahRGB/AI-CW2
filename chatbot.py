from random import choice
import json
from enum import Enum
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

        @staticmethod
        def from_string(s): # turn string into intentiontype enum
            if s == "greeting":
                return Chatbot.IntentionTypes.GREETING
            elif s == "exit":
                return Chatbot.IntentionTypes.EXIT
            elif s == "task1":
                return Chatbot.IntentionTypes.TASK1
            elif s == "single_ticket" or s == "return_ticket":
                return Chatbot.IntentionTypes.SELECT_TICKET
            return Chatbot.IntentionTypes.UNSURE


    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.sentences_path = "./chatbot_data/sentences.txt"
        self.intentions_path = "./chatbot_data/intentions.json"
        self.responses_path = "./chatbot_data/responses.json"

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
        # find what kind of message the user sents
        cleaned_user_input = self.clean_text(user_input)
        user_input_tokens = self.nlp(cleaned_user_input)

        for intention in self.intentions:
            for pattern in self.intentions[intention]["patterns"]:
                pattern_tokens = self.nlp(self.clean_text(pattern))
                if pattern_tokens.similarity(user_input_tokens) > min_similarity:
                    self.last_intention = Chatbot.IntentionTypes.from_string(intention)
                    return self.last_intention
                
        self.last_intention = Chatbot.IntentionTypes.UNSURE
        return self.last_intention

    def detect_ticket_type(self, text, min_similarity=0.5):
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
        text_tokens = self.nlp(self.clean_text(text))
        current_min_similarity = 0.9
        found_match = False
        matches = {}

        while not found_match and current_min_similarity > 0.3:

            for station in self.station_dict:
                if (station == text): # exact match, don't do any more searching
                    found_match = True
                    matches[station] = self.station_dict[station]
                    continue

                if station[0] == text_tokens[0].text[0]: # if first letter matches
                    station_tokens = self.nlp(self.clean_text(station))
                    code_tokens = self.nlp(self.clean_text(self.station_dict[station]))

                    if station_tokens.similarity(text_tokens) > current_min_similarity:
                        # found a match witht the station name
                        found_match = True
                        matches[station] = self.station_dict[station]
                        continue
                    elif code_tokens.similarity(text_tokens) > current_min_similarity:
                        # found a match with the station code
                        found_match = True
                        matches[station] = self.station_dict[station]
                        continue

            current_min_similarity -= 0.1 # try with a smallest min similarity

        print(matches)
        return matches



    def send_bot_message(self, message):
        print(f"\n{message}\n")


class Intention(Fact):
    # information about current user intention
    # e.g. gretting, exit, task1, task2
    pass

class Ticket(Fact):
    # information about a ticket
    pass

class ChatbotEngine(KnowledgeEngine):
    def __init__(self, chatbot):
        KnowledgeEngine.__init__(self)
        self.chatbot = chatbot

    @DefFacts()
    def setup(self):
        yield Intention(type=Chatbot.IntentionTypes.UNSURE)
        
    @Rule(Intention(type=Chatbot.IntentionTypes.UNSURE))
    def unsure_message(self):
        self.chatbot.send_bot_message("I'm unsure what you mean, but you can ask me about train tickets!")

    @Rule(Intention(type=Chatbot.IntentionTypes.GREETING))
    def greeting_message(self):
        self.chatbot.send_bot_message(choice(self.chatbot.responses["greeting"]))

    @Rule(Intention(type=Chatbot.IntentionTypes.EXIT))
    def exit_message(self):
        self.chatbot.send_bot_message(choice(self.chatbot.responses["exit"]))

    @Rule(Intention(type=Chatbot.IntentionTypes.TASK1))
    def task1_setup(self):
        self.chatbot.send_bot_message(choice(self.chatbot.responses["task1_setup"]))
        chatbot.last_intention_fact = self.modify(chatbot.last_intention_fact, type=Chatbot.IntentionTypes.SELECT_TICKET)

    @Rule(Intention(type=Chatbot.IntentionTypes.SELECT_TICKET))
    def select_ticket(self):
        ticket_input = input()
        chatbot.find_user_intention(ticket_input)
        ticket_type = self.chatbot.detect_ticket_type(ticket_input, 0.9)
        if ticket_type:
            ticket_type_resolved = True
            if ticket_type == "single":
                chatbot_engine.declare(Ticket(type="single"))

            elif ticket_type == "return":
                chatbot_engine.declare(Ticket(type="return"))
        elif ticket_type == False:
            self.chatbot.send_bot_message("I don't know that ticket type. Try again...")

    @Rule(AND(OR(Intention(type=Chatbot.IntentionTypes.TASK1), Intention(type=Chatbot.IntentionTypes.SELECT_TICKET)), Ticket(type=MATCH.ticket_type)))
    def select_station(self, ticket_type):
        self.chatbot.send_bot_message(f"You want a {ticket_type} ticket. Where do you want to start your journey?")
        origin_input = input()
        origin_station = self.chatbot.detect_station_name(origin_input)
        if origin_station:
            pass

    
################################################################

chatbot = Chatbot()

chatbot_engine = ChatbotEngine(chatbot)
chatbot_engine.reset()
chatbot.last_intention_fact = chatbot_engine.facts[1]


while True:
    test_input = input()
    chatbot.find_user_intention(test_input)
    chatbot.last_intention_fact = chatbot_engine.modify(chatbot.last_intention_fact, type=chatbot.last_intention)

    print(f"\n{chatbot_engine.facts}\n")
    chatbot_engine.run()
