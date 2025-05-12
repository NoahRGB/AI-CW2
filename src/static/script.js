x
let isChatbotTurn = false;
let isFirstMessage = true;
let inputBox = document.getElementById("input-box");
let chatbox = document.getElementById("chatbox");
let loader = document.getElementById("loader");

const turnOnLoader = () => {
  chatbox.appendChild(loader);
}

const turnOffLoader = () => {
  loader.remove();
}

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
    turnOffLoader();
    console.log("Message: " + chatbot_message)
    isChatbotTurn = false;
    addToChatbox(chatbot_message, false);
  });
}

const sendMessage = () => {
  let userMessage = inputBox.value;
  if (isFirstMessage | userMessage != "") {
    !isFirstMessage && addToChatbox(userMessage, true)
    isChatbotTurn = true;
    turnOnLoader();
    getChatbotMessage(userMessage);
    inputBox.value = ""
  } else {
    alert("Please enter a message before sending");
  }
}

document.body.addEventListener("keypress", event => {
  if (event.key == "Enter") {
    event.preventDefault();
    sendMessage();
  }
});

sendMessage();
isFirstMessage = false;