
let isChatbotTurn = false;
let isFirstMessage = true;
let inputBox = document.getElementById("input-box");
let chatbox = document.getElementById("chatbox");

const addToChatbox = (message, isUser) => {
  if (isUser) {
    chatbox.innerHTML += `\n<div class="chatbox-message-container"><div class="chatbox-message user-message">${message}</div></div>`
  } else {
    chatbox.innerHTML += `\n<div class="chatbox-message-container"><div class="chatbox-message chatbot-message">${message}</div></div>`
  }
  chatbox.scrollTop = chatbox.scrollHeight;
}

const getChatbotMessage = userInput => {
  $.post("/get_chatbot_message", { user_input: userInput, is_first_message: isFirstMessage }, chatbot_message => {
    console.log("Message: " + chatbot_message)
    isChatbotTurn = false;
    addToChatbox(chatbot_message, false);
  });
}

const sendMessage = () => {
  let userMessage = inputBox.value;
  !isFirstMessage && addToChatbox(userMessage, true)
  isChatbotTurn = true;
  getChatbotMessage(userMessage);
  inputBox.value = ""
}

document.body.addEventListener("keypress", event => {
  if (event.key == "Enter") {
    event.preventDefault();
    sendMessage();
  }
});

sendMessage();
isFirstMessage = false;