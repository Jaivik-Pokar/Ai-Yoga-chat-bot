const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');

sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
});

function sendMessage() {
    const message = userInput.value.trim();
    if (message) {
        appendMessage(message, 'user-message');

        fetch('/get_response', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: 'user_input=' + encodeURIComponent(message)
        })
        .then(response => response.text())
        .then(data => {
            appendMessage(data, 'bot-message');
            handleImageResponses(chatMessages.lastChild);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        });

        userInput.value = '';
    }
}

function handleImageResponses(container) {
    const images = container.querySelectorAll('img');
    images.forEach(img => {
        img.style.maxWidth = '100%';
        img.style.height = 'auto';
    });
}

function appendMessage(message, messageClass) {
    const messageContainer = document.createElement('div');
    messageContainer.classList.add('message');

    const messageElement = document.createElement('div');
    messageElement.classList.add(messageClass);
    messageElement.innerHTML = message;

    messageContainer.appendChild(messageElement);
    chatMessages.appendChild(messageContainer);
}