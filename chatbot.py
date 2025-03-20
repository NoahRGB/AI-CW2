from experta import *
from difflib import get_close_matches, SequenceMatcher
import spacy
import spacy.cli

import warnings
warnings.filterwarnings('ignore')

nlp = spacy.load("en_core_web_sm")
sentences_path = "./chatbot_data/sentences.txt"

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
    # find what kind of message the user just sent was
    cleaned_user_input = clean_text(user_input)
    user_input_tokens = nlp(cleaned_user_input)
    similarities = {}
    for index, sentence in enumerate(sentences):
        cleaned_sentence = clean_text(sentence)
        sentence_tokens = nlp(cleaned_sentence)
        similarity = sentence_tokens.similarity(user_input_tokens)
        similarities[index] = similarity
    
    max_similarity_index = max(similarities, key=similarities.get)
    min_similarity = 0.75

    if similarities[max_similarity_index] > min_similarity:
        if intention_labels[max_similarity_index] == "greeting":
            print("You sent me a greeting message")
        elif intention_labels[max_similarity_index] == "exit":
            print("You sent me a goodbye message")
        elif intention_labels[max_similarity_index] == "task1":
            print("You sent me a task1 message")
        return True
    return False




class Ticket(Fact):
    # information about a ticket
    pass

class Chatbot(KnowledgeEngine):
    @Rule(Ticket(type="single"))
    def single_ticket(self):
        print("You want a single ticket.")
    
    @Rule(Ticket(type="return"))
    def return_ticket(self):
        print("You want a return ticket.")
    

intention_labels, sentences = generate_sentences()

test_input = "can you do train tickets?"
find_user_intention(test_input, intention_labels, sentences)

# chatbot_engine = Chatbot()
# chatbot_engine.reset()
# chatbot_engine.declare(Ticket(type="single"))
# chatbot_engine.run()