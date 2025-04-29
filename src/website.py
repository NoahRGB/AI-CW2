from flask import Flask
from flask import render_template, request

from chatbot import Chatbot
from chatbot_engine import ChatbotEngine
from fact_types import *

app = Flask(__name__)

chatbot = Chatbot()
chatbot_engine = ChatbotEngine(chatbot)

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
    chatbot.origin_station_fact = chatbot_engine.declare(OriginStation(pending=True, needs_confirmation=False))
    chatbot.destination_station_fact = chatbot_engine.declare(DestinationStation(pending=True, needs_confirmation=False))


  else: # otherwise, use the user's message
    chatbot.find_user_intention(user_input)
    chatbot.last_intention_fact = chatbot_engine.modify(chatbot.last_intention_fact, type=chatbot.last_intention)
    chatbot.last_message = user_input
  
  print(f"\nRunning engine with facts:\n{chatbot_engine.facts}\n")
  chatbot_engine.run()
  return chatbot.last_chatbot_message

if __name__ == "__main__": # if you run this file
  app.run(debug=True)