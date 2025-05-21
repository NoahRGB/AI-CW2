from flask import Flask
from flask import render_template, request
from datetime import date, time, datetime
import re

from date_time import DateTime
from chatbot import Chatbot
from database import insert_query, getRecents, createDatabase, deleteTable, openRecent, existingQuery
from chatbot_engine import ChatbotEngine
from fact_types import *

app = Flask(__name__)

chatbot = Chatbot()
chatbot_engine = ChatbotEngine(chatbot)

createDatabase()

def get_station_code(name):
  import pickle
  with open("../chatbot_data/station_list.pickle", "rb") as file:
    stations = pickle.load(file)
    if stations.get(name.lower()):
      return stations.get(name.lower()).upper()

def declare_all_information(user_input):
  # finds all the information in user_input using chatbot.detect_all_information
  # and then modifies all the appropriate KnowledgeEngine facts
  
  information = chatbot.detect_all_information(user_input)
  
  print(information)
  
  if "origin_station" not in information:
    station = re.search(r"from\s+([A-Za-z\s]+?)\s+to", user_input, re.IGNORECASE)
    if station:
      origin_name = station.group(1).strip().title()
      origin_code = get_station_code(origin_name)
      if origin_code:
        information["origin_station"] = (origin_name, origin_code)

  if "departure_date" not in information:
    dateRe = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", user_input)
    if dateRe:
      dateString = dateRe.group(0)
      y, m, d = dateString.split("-")
      information["departure_date"] = DateTime(year =int(y), month = int(m), day = int(d))
  
  if "ticket" in information:
    if "type" not in chatbot.ticket_fact or chatbot.ticket_fact["pending"] == True:
      chatbot.ticket_fact = chatbot_engine.modify(chatbot.ticket_fact, type=information["ticket"])
      chatbot.last_intention_fact = chatbot_engine.modify(chatbot.last_intention_fact, type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH)

  if "origin_station" in information:
    station, code = information["origin_station"]
    if chatbot.origin_station_fact["pending"] == True:
      chatbot.origin_station_fact = chatbot_engine.modify(chatbot.origin_station_fact, name=station, code=code)
      chatbot.last_intention_fact = chatbot_engine.modify(chatbot.last_intention_fact, type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH)
      
  if "destination_station" in information:
    station, code = information["destination_station"]
    if chatbot.destination_station_fact["pending"] == True:
      chatbot.destination_station_fact = chatbot_engine.modify(chatbot.destination_station_fact, name=station, code=code)
      chatbot.last_intention_fact = chatbot_engine.modify(chatbot.last_intention_fact, type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH)

  if "departure_time" in information:
    if chatbot.departure_time_fact["pending"] == True:
      chatbot.departure_time_fact = chatbot_engine.modify(chatbot.departure_time_fact, time=information["departure_time"])
      chatbot.last_intention_fact = chatbot_engine.modify(chatbot.last_intention_fact, type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH)

  if "departure_date" in information:
    if chatbot.departure_date_fact["pending"] == True:
      chatbot.departure_date_fact = chatbot_engine.modify(chatbot.departure_date_fact, date=information["departure_date"])
      chatbot.last_intention_fact = chatbot_engine.modify(chatbot.last_intention_fact, type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH)
  
  if "return_time" in information:
    if chatbot.return_time_fact["pending"] == True:
      chatbot.return_time_fact = chatbot_engine.modify(chatbot.return_time_fact, time=information["return_time"])
      chatbot.last_intention_fact = chatbot_engine.modify(chatbot.last_intention_fact, type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH)

  if "return_date" in information:
    if chatbot.return_date_fact["pending"] == True:
      chatbot.return_date_fact = chatbot_engine.modify(chatbot.return_date_fact, date=information["return_date"])
      chatbot.last_intention_fact = chatbot_engine.modify(chatbot.last_intention_fact, type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH)
      
  if "adults" in information:
    chatbot.adult_tickets_fact = chatbot_engine.modify(chatbot.adult_tickets_fact, count=information["adults"], pending=True)
    chatbot.last_intention_fact = chatbot_engine.modify(chatbot.last_intention_fact, type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH)
    
  if "children" in information:
    chatbot.child_tickets_fact = chatbot_engine.modify(chatbot.child_tickets_fact, count=information["children"], pending=True)
    chatbot.last_intention_fact = chatbot_engine.modify(chatbot.last_intention_fact, type=Chatbot.IntentionTypes.TICKET_WALKTHROUGH)

  if "current_station" in information:
    station, code = information["current_station"]
    if chatbot.current_station_fact["pending"] == True:
      chatbot.current_station_fact = chatbot_engine.modify(chatbot.current_station_fact, name=station, code=code, pending=True)

  if "current_time" in information:
    if chatbot.current_time_fact["pending"] == True:
      chatbot.current_time_fact = chatbot_engine.modify(chatbot.current_time_fact, time=information["current_time"], pending=True)

  if "current_delay" in information:
    if chatbot.current_delay_fact["pending"] == True:
      chatbot.current_delay_fact = chatbot_engine.modify(chatbot.current_delay_fact, amount=information["current_delay"], pending=True)

  if "direction" in information:
    if chatbot.direction_fact["pending"] == True:
      chatbot.direction_fact = chatbot_engine.modify(chatbot.direction_fact, to_nrw=information["direction"], pending=True)

# route to render the homepage
@app.route("/")
def home():
  return render_template("home.html", recent_queries=getRecents())

# route to send a new chatbot message to the website
@app.post("/get_chatbot_message")
def get_chatbot_message():
  user_input = request.form.get("user_input")
  is_first_messsage = request.form.get("is_first_message") == "true"
  is_saved_query = request.form.get("saved_query") == "true"
  
  if is_first_messsage and len(chatbot_engine.facts) <=1: # if the website has just loaded, just send "hey" to the chatbot
    chatbot_engine.reset()
    chatbot.find_user_intention("Hey")
    
    # initialise all the facts for the KnowledgeEngine
    chatbot.last_intention_fact = chatbot_engine.modify(chatbot_engine.facts[1], type=chatbot.last_intention)
    
    # facts for part 1 (cheapest ticket)
    chatbot.ticket_fact = chatbot_engine.declare(Ticket(pending=True))
    chatbot.origin_station_fact = chatbot_engine.declare(OriginStation(pending=True))
    chatbot.destination_station_fact = chatbot_engine.declare(DestinationStation(pending=True))
    chatbot.departure_time_fact = chatbot_engine.declare(DepartureTime(pending=True))
    chatbot.departure_date_fact = chatbot_engine.declare(DepartureDate(pending=True))
    chatbot.adult_tickets_fact = chatbot_engine.declare(AdultTickets(count=1, pending=False))
    chatbot.child_tickets_fact = chatbot_engine.declare(ChildTickets(count=0, pending=False))
    chatbot.return_time_fact = chatbot_engine.declare(ReturnTime(pending=True))
    chatbot.return_date_fact = chatbot_engine.declare(ReturnDate(pending=True))
    
    # facts for part 2 (delay prediction)
    chatbot.current_station_fact = chatbot_engine.declare(CurrentStation(pending=True))
    chatbot.current_time_fact = chatbot_engine.declare(CurrentTime(pending=True))
    chatbot.current_delay_fact = chatbot_engine.declare(CurrentDelay(pending=True))
    chatbot.direction_fact = chatbot_engine.declare(Direction(pending=True))

  else: # otherwise, use the user's message
    # find all the information that was in the user's message
    chatbot.find_user_intention(user_input)
    
    if chatbot.last_intention == Chatbot.IntentionTypes.TICKET_WALKTHROUGH:
      chatbot.doing_task_1 = True
    elif chatbot.last_intention == Chatbot.IntentionTypes.DELAY_WALKTHROUGH:
      chatbot.doing_task_1 = False

    chatbot.last_intention_fact = chatbot_engine.modify(chatbot.last_intention_fact, type=chatbot.last_intention)
    chatbot.last_message = user_input
    
    declare_all_information(user_input)
  
  print(f"\nRunning engine with facts:\n{chatbot_engine.facts}\n")
  print(f"\n Doing task 1? {chatbot.doing_task_1}")
  chatbot_engine.run()
  
  if chatbot.doing_task_1:
    try:
      dep_loc = chatbot.origin_station_fact
      destination = chatbot.destination_station_fact
      dep_time = chatbot.departure_time_fact
      dep_date = chatbot.departure_date_fact
      if (not dep_loc["pending"] and not destination["pending"] and not dep_time["pending"] and not dep_date["pending"] and 'name' in dep_loc and 'name' in destination and 'time' in dep_time and 'date' in dep_date):
        dep_time_time = time(int(dep_time["time"].get_hour()), int(dep_time["time"].get_min()))
        dep_date_date = date(int(dep_date["date"].get_year()), int(dep_date["date"].get_month()), int(dep_date["date"].get_day()))
        if not existingQuery(dep_loc["name"], destination["name"], dep_time_time, dep_date_date):
          insert_query(dep_loc["name"], destination["name"], dep_time_time, dep_date_date)
        
    except Exception as e:
      print("error inserting into database: ", e)
      
  return chatbot.last_chatbot_message

if __name__ == "__main__": # if you run this file
  app.run(debug=True)
  
  
  
  
  
        #   "task1": {
        #     "patterns": [
        #         "ticket",
        #         "cheapest",
        #         "cost",
        #         "Can you find the cheapest tickets?",
        #         "Can you find me some train tickets?",
        #         "I need train tickets",
        #         "plan a train journey for me",
        #         "plan a journey",
        #         "journey planner",
        #         "task 1",
        #         "do task 1",
        #         "link me to train tickets",
        #         "i want to travel on a train",
        #         "i want to get somewhere via train",
        #         "plan my train journey",
        #         "train journey"
        #     ]
        # },
        # "task2": {
        #     "patterns": [
        #         "task 2",
        #         "do task 2",
        #         "predict delays",
        #         "delays",
        #         "predict delays on my journey",
        #         "predict delays to london",
        #         "predict delays to london liverpool street",
        #         "predict delays to norwich",
        #         "i want to predict delays to london",
        #         "i want to predict delays to norwich",
        #         "what will my delay be?",
        #         "delay finder",
        #         "delay calculator",
        #         "can you predict delays?",
        #         "can you calculate what my delay will be",
        #         "can you find how long my train will be delayed?",
        #         "how long will my train be delayed?",
        #         "delay prediction"
        #     ]
        # },