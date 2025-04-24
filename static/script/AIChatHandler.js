const AISubmitBtn = document.getElementById("AISubmitBtn");
const extractedFileTextInput = document.getElementById("extractedFileText");
const questionInput = document.getElementById("question");
const initChatTitle = document.querySelector(".init_chat_title");
const chatContainer = document.querySelector(".chat_conversation_content")



async function fetchAIChatData() {
    try {
        const response = await fetch("/api/v1/conversations", {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        });

        if (!response.ok) {
            throw new Error(`
                Network response was not ok: ${response.statusText}. 
                Status: ${response.status}
            `);
        }

        const data = await response.json();
        console.log(data.conversations);

        if (data.conversations.length === 0) {
            initChatTitle.textContent = "Start a new conversation";
        }
        
        data.conversations.forEach(conversation => {
            const userMessageDiv = document.createElement("div");
            userMessageDiv.className = "user_message";
            userMessageDiv.textContent = conversation.user_question;
        
            const aiResponseDiv = document.createElement("div");
            aiResponseDiv.className = "ai_response";
            aiResponseDiv.textContent = conversation.ai_answer;
        
            // Append the user message and AI response to the chat container
            chatContainer.appendChild(userMessageDiv);
            chatContainer.appendChild(aiResponseDiv);
        });

    } catch (error) {
        console.error("Error fetching AI chat data:", error);
        initChatTitle.innerHTML = `An error occurred while loading the chat conversation data. <br> Please try again later`;
    }
}



async function askAI(e) {
    e.preventDefault();

    const formData = new FormData();
    formData.append("extractedFileText", extractedFileTextInput.value);
    formData.append("question", questionInput.value);

    try {
        const response = await fetch("/api/v1/ask_ai", {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            throw new Error(`
                Network response was not ok: ${response.statusText}. 
                Status: ${response.status}
            `);
        }

        const data = await response.json();
        console.log(data);

        questionInput.value = ""; // Clear the question input
        fetchAIChatData(); // Fetch the updated chat data
    } catch (error) {
        console.error("Error asking AI:", error);
    }
}


AISubmitBtn.addEventListener("click", askAI);


document.addEventListener("DOMContentLoaded", function() {
    console.log('Chat conversation data loading...');
    fetchAIChatData();
    console.log('Chat conversation data loaded successfully.');
});

export { extractedFileTextInput, questionInput };
