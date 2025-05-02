from flask import Flask
from flask import render_template, request

from chatbot import Chatbot
from chatbot_engine import ChatbotEngine
from fact_types import *

app = Flask(__name__)

chatbot = Chatbot()
chatbot_engine = ChatbotEngine(chatbot)

def declare_all_information(user_input):
  information = chatbot.detect_all_information(user_input)
  
  if "ticket" in information:
    if "type" not in chatbot.ticket_fact or chatbot.ticket_fact["pending"] == True:
      print(f"Updating ticket fact with {information['ticket']}")
      chatbot.ticket_fact = chatbot_engine.modify(chatbot.ticket_fact, type=information["ticket"])

  if "origin_station" in information:
    station, code = information["origin_station"]
    if chatbot.origin_station_fact["pending"] == True:
      chatbot.origin_station_fact = chatbot_engine.modify(chatbot.origin_station_fact, name=station, code=code)
      
  if "destination_station" in information:
    station, code = information["destination_station"]
    if chatbot.destination_station_fact["pending"] == True:
      chatbot.destination_station_fact = chatbot_engine.modify(chatbot.destination_station_fact, name=station, code=code)

  if "departure_time" in information:
    if chatbot.departure_time_fact["pending"] == True:
      chatbot.departure_time_fact = chatbot_engine.modify(chatbot.departure_time_fact, time=information["departure_time"])

  if "departure_date" in information:
    if chatbot.departure_date_fact["pending"] == True:
      chatbot.departure_date_fact = chatbot_engine.modify(chatbot.departure_date_fact, date=information["departure_date"])
  
  if "return_time" in information:
    if chatbot.return_time_fact["pending"] == True:
      chatbot.return_time_fact = chatbot_engine.modify(chatbot.return_time_fact, time=information["return_time"])

  if "return_date" in information:
    if chatbot.return_date_fact["pending"] == True:
      chatbot.return_date_fact = chatbot_engine.modify(chatbot.return_date_fact, date=information["return_date"])
      
  if "adults" in information:
    chatbot.adult_tickets_fact = chatbot_engine.modify(chatbot.adult_tickets_fact, count=information["adults"], pending=True)
    
  if "children" in information:
    chatbot.child_tickets_fact = chatbot_engine.modify(chatbot.child_tickets_fact, count=information["children"], pending=True)

# route to render the homepage
@app.route("/")
def home():
  return render_template("home.html")

# route to send a new chatbot message to the website
@app.post("/get_chatbot_message")
def get_chatbot_message():
  user_input = request.form.get("user_input")
  is_first_messsage = request.form.get("is_first_message") == "true"
  
  if is_first_messsage: # if the website has just loaded, just send "hey" to the chatbot
    chatbot_engine.reset()
    chatbot.find_user_intention("Hey")
    chatbot.last_intention_fact = chatbot_engine.modify(chatbot_engine.facts[1], type=chatbot.last_intention)
    chatbot.ticket_fact = chatbot_engine.declare(Ticket(pending=True))
    chatbot.origin_station_fact = chatbot_engine.declare(OriginStation(pending=True))
    chatbot.destination_station_fact = chatbot_engine.declare(DestinationStation(pending=True))
    chatbot.departure_time_fact = chatbot_engine.declare(DepartureTime(pending=True))
    chatbot.departure_date_fact = chatbot_engine.declare(DepartureDate(pending=True))
    chatbot.adult_tickets_fact = chatbot_engine.declare(AdultTickets(count=1, pending=False))
    chatbot.child_tickets_fact = chatbot_engine.declare(ChildTickets(count=0, pending=False))
    chatbot.return_time_fact = chatbot_engine.declare(ReturnTime(pending=True))
    chatbot.return_date_fact = chatbot_engine.declare(ReturnDate(pending=True))
    
  else: # otherwise, use the user's message
    chatbot.find_user_intention(user_input)
    chatbot.last_intention_fact = chatbot_engine.modify(chatbot.last_intention_fact, type=chatbot.last_intention)
    chatbot.last_message = user_input
  
  declare_all_information(user_input)
  print(f"\nRunning engine with facts:\n{chatbot_engine.facts}\n")
  chatbot_engine.run()
  return chatbot.last_chatbot_message

if __name__ == "__main__": # if you run this file
  app.run(debug=True)