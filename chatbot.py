from random import choice
import json
from enum import Enum
from experta import *
from difflib import get_close_matches, SequenceMatcher
import spacy
import spacy.cli

import warnings
warnings.filterwarnings('ignore')

# spacy.cli.download("en_core_web_sm")
nlp = spacy.load("en_core_web_sm")
sentences_path = "./chatbot_data/sentences.txt"
responses_path = "./chatbot_data/responses.json"
intention_types = ["greeting", "exit", "task1"]

class IntentionTypes(Enum):
    GREETING=1,
    EXIT=2,
    TASK1=3,
    UNSURE=4,

def generate_sentences():
    # get sentences from sentences_path and turn them into
    # intention_labels and formatted sentences
    intention_labels, sentences = [], []
    with open(sentences_path) as file:
        for line in file:
            parts = line.split(" | ")
            if parts[0] == "task1":
                intention_labels.append("task1")
            elif parts[0] == "exit":
                intention_labels.append("exit")
            else: # greeting
                intention_labels.append("greeting")
            sentence_tokens = nlp(parts[1])
            sentences.append(sentence_tokens.text.lower().strip())
    return intention_labels, sentences

def clean_text(text):
    # turn text into tokens (stopwords + punctuation removed)
    tokens = nlp(text.lower())
    cleaned_text = ""
    for token in tokens:
        if not token.is_stop and not token.is_punct:
            cleaned_text = cleaned_text + token.text + " "
    return cleaned_text.strip()

def find_user_intention(user_input, intention_labels, sentences):
    # find what kind of message the user sents
    cleaned_user_input = clean_text(user_input)
    user_input_tokens = nlp(cleaned_user_input)
    similarities = {}
    for index, sentence in enumerate(sentences):
        cleaned_sentence = clean_text(sentence)
        sentence_tokens = nlp(cleaned_sentence)
        similarity = sentence_tokens.similarity(user_input_tokens)
        similarities[index] = similarity
    
    max_similarity_index = max(similarities, key=similarities.get)
    min_similarity = 0.7

    if similarities[max_similarity_index] > min_similarity:
        if intention_labels[max_similarity_index] == "greeting":
            return IntentionTypes.GREETING
            # print("You sent me a greeting message")
        elif intention_labels[max_similarity_index] == "exit":
            return IntentionTypes.EXIT
            # print("You sent me a goodbye message")
        elif intention_labels[max_similarity_index] == "task1":
            return IntentionTypes.TASK1
            # print("You sent me a task1 message")
    return IntentionTypes.UNSURE

def detect_ticket_type(text, min_similarity=0.5):
    single_options = ["single", "single ticket", "one way"]
    return_options = ["return", "both ways", "two ways", "open return", "round trip"]
    text_tokens = nlp(clean_text(text))
    for single_text in single_options:
        single_text_tokens = nlp(clean_text(single_text))
        if single_text_tokens.similarity(text_tokens) > min_similarity:
            return "single"
        
    for return_text in return_options:
        return_text_tokens = nlp(clean_text(return_text))
        if return_text_tokens.similarity(text_tokens) > min_similarity:
            return "return"
        
    return False

def send_bot_message(message):
    print(f"\n{message}\n")

class Intention(Fact):
    # information about current user intention
    # e.g. gretting, exit, task1, task2
    pass

class Ticket(Fact):
    # information about a ticket
    pass

class Chatbot(KnowledgeEngine):
    @DefFacts()
    def setup(self):
        yield Intention(type=IntentionTypes.UNSURE)
        
    @Rule(Intention(type=IntentionTypes.UNSURE))
    def unsure_message(self):
        send_bot_message("I'm unsure what you mean, but you can ask me about train tickets!")

    @Rule(Intention(type=IntentionTypes.GREETING))
    def greeting_message(self):
        send_bot_message(choice(responses["greeting"]))

    @Rule(Intention(type=IntentionTypes.EXIT))
    def exit_message(self):
        send_bot_message(choice(responses["exit"]))

    @Rule(Intention(type=IntentionTypes.TASK1))
    def task1_setup(self):
        send_bot_message(choice(responses["task1_setup"]))
        ticket_input = input()
        ticket_type = detect_ticket_type(ticket_input, 0.8)

        if ticket_type:
            if ticket_type == "single":
                chatbot_engine.declare(Ticket(type="single"))
            elif ticket_type == "return":
                chatbot_engine.declare(Ticket(type="return"))
        elif ticket_type == False:
            send_bot_message("I don't know that ticket type. Try again...")
            print(chatbot_engine.facts)

    @Rule(AND(Intention(type=IntentionTypes.TASK1), Ticket(type="single")))
    def single_ticket(self):
        send_bot_message("You want a single ticket.")
    
    @Rule(AND(Intention(type=IntentionTypes.TASK1), Ticket(type="return")))
    def return_ticket(self):
        send_bot_message("You want a return ticket.")
    



    
################################################################

intention_labels, sentences = generate_sentences()

with open(responses_path) as f:
    responses = json.load(f)

chatbot_engine = Chatbot()
chatbot_engine.reset()
intention_fact = chatbot_engine.facts[1]

while True:
    test_input = input()
    intention = find_user_intention(test_input, intention_labels, sentences)
    intention_fact = chatbot_engine.modify(intention_fact, type=intention)

    print(f"\n{chatbot_engine.facts}\n")
    chatbot_engine.run()
