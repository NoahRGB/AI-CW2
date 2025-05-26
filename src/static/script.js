let isChatbotTurn = false;
let isFirstMessage = true;
let inputBox = document.getElementById("input-box");
let chatbox = document.getElementById("chatbox");
let loader = document.getElementById("loader");

const turnOnLoader = () => {
  chatbox.appendChild(loader);
  chatbox.scrollTop = chatbox.scrollHeight;
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

const getChatbotMessage = (userInput) => {

  if (isFirstMessage) {
    console.log("Resetting chatbot");

    $.get("/reset_chatbot", { }, res => {

      $.post("/get_chatbot_message", { user_input: userInput, is_first_message: isFirstMessage }, chatbot_message => {
        turnOffLoader();
        console.log("Message: " + chatbot_message)
        isChatbotTurn = false;
        addToChatbox(chatbot_message, false);
        isFirstMessage = false;
      });
    });
  } else {
      $.post("/get_chatbot_message", { user_input: userInput, is_first_message: isFirstMessage }, chatbot_message => {
        turnOffLoader();
        console.log("Message: " + chatbot_message)
        isChatbotTurn = false;
        addToChatbox(chatbot_message, false);
      });
  }

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

function load_query(dep_loc, destination, time, date){
  const query = `I am travelling from ${dep_loc} to ${destination} at ${time} on ${date}`;
  addToChatbox(query, true);
  turnOnLoader();
  $.post("/get_chatbot_message", {
    user_input: query,
    is_first_message: true,
    saved_query: true
  }, chatbot_message=>{
    turnOffLoader();
    addToChatbox(chatbot_message, false);

  });
  isFirstMessage = false;
}

sendMessage();