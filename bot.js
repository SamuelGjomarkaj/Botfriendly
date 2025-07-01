const chatBtn = document.getElementById("chat-bubble");
const chatBox = document.getElementById("chat-popup");
const closeBtn = document.getElementById("close-chat");
const sendBtn = document.getElementById("send-btn");
const input = document.getElementById("chat-input");
const chatBody = document.getElementById("chat-body");

// Toggle Chat
chatBtn.onclick = () => chatBox.style.display = "flex";
closeBtn.onclick = () => chatBox.style.display = "none";

// Send Message
sendBtn.onclick = async () => {
    const msg = input.value.trim();
    if (!msg) return;

    // Append user message
    const userMsg = document.createElement("div");
    userMsg.className = "user-msg";
    userMsg.innerText = msg;
    chatBody.appendChild(userMsg);
    input.value = "";
    chatBody.scrollTop = chatBody.scrollHeight;

    // Show loading bot message
    const botMsg = document.createElement("div");
    botMsg.className = "bot-msg";
    botMsg.innerText = "Thinking... 🤖";
    chatBody.appendChild(botMsg);
    chatBody.scrollTop = chatBody.scrollHeight;

    try {
        const response = await fetch("/ask", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ question: msg }),
        });

        const data = await response.json();
        botMsg.innerHTML = data.response.replace(/\n/g, "<br>");
    } catch (err) {
        botMsg.innerHTML = "❌ Error getting response from AI.";
        console.error(err);
    }

    chatBody.scrollTop = chatBody.scrollHeight;
};

// Enter key also sends
input.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendBtn.click();
});
