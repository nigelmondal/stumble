// Dummy chat history for each buddy
const chatHistory = {
    Twinkle: [
        { text: "Hi there!", type: "received" },
        { text: "Hello, how are you?", type: "sent" },
        { text: "I'm good! What about you?", type: "received" },
    ],
    Niger: [
        { text: "Hey Niger!", type: "sent" },
        { text: "Hi, long time no see!", type: "received" },
    ],
    Ronit: [
        { text: "Ronit, are you coming to the meeting?", type: "sent" },
        { text: "Yes, I’ll be there.", type: "received" },
    ],
    Shrey: [
        { text: "How’s it going, Shrey?", type: "sent" },
        { text: "Pretty good! You?", type: "received" },
    ],
};

// Display chat for the selected buddy
function loadChat(buddyName) {
    const chatMessages = document.getElementById("chat-messages");
    chatMessages.innerHTML = ""; // Clear existing messages
    document.getElementById("chat-buddy").textContent = buddyName;

    if (chatHistory[buddyName]) {
        chatHistory[buddyName].forEach((msg) => {
            const messageDiv = document.createElement("div");
            messageDiv.classList.add("message", msg.type);
            messageDiv.textContent = msg.text;
            chatMessages.appendChild(messageDiv);
        });
    }
}

// Handle buddy list click
document.querySelectorAll(".buddy").forEach((buddy) => {
    buddy.addEventListener("click", (event) => {
        document
            .querySelectorAll(".buddy")
            .forEach((el) => el.classList.remove("active"));
        event.target.classList.add("active");
        loadChat(event.target.dataset.buddy);
    });
});

// Handle send button click
document.getElementById("send-btn").addEventListener("click", () => {
    const messageInput = document.getElementById("message");
    const messageText = messageInput.value.trim();

    if (messageText !== "") {
        const chatMessages = document.getElementById("chat-messages");
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", "sent");
        messageDiv.textContent = messageText;
        chatMessages.appendChild(messageDiv);
        messageInput.value = "";
    }
});

// Handle attachment button click
document.getElementById("attach-btn").addEventListener("click", () => {
    document.getElementById("file-input").click();
});

// Handle file input change
document.getElementById("file-input").addEventListener("change", (event) => {
    const file = event.target.files[0];
    if (file) {
        const chatMessages = document.getElementById("chat-messages");
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", "attachment", "sent");
        messageDiv.textContent = `📎 ${file.name}`;
        chatMessages.appendChild(messageDiv);
    }
});

// Initial load for Twinkle
loadChat("Twinkle");
