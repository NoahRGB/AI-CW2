
from chatbot import Chatbot
from chatbot_engine import ChatbotEngine

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

    # print(f"\n{chatbot_engine.facts}\n") # for debugging
    chatbot_engine.run()