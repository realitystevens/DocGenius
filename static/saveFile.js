import loadFiles from "./fileHandler.js";

const saveFileBtn = document.getElementById("saveFileBtn");
const fileInput = document.getElementById("file");
const fileSubmitServerMessage = document.querySelector('.file_submit_server_message')



saveFileBtn.addEventListener("click", async function (e) {
    e.preventDefault();

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    if (fileInput.files.length > 0) {
        try {
            const response = await fetch("/api/v1/save_file", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                throw new Error(`HTTP Error! ${response.statusText}. Status: ${response.status}`);
            }

            const data = await response.json();
            console.log('File saved successfully', data);
            fileSubmitServerMessage.textContent = "File saved successfully. Woohoo!";
            await loadFiles(); // Reload files after saving
            fileInput.value = ""; // Clear the file input
            setTimeout(() => {
                fileSubmitServerMessage.textContent = "";
            }, 2000);
        } catch (error) {
            console.error('Error saving file', error);
            fileSubmitServerMessage.textContent = "Error saving file (Check console for more details). You can give it a try and try again.";
        }
    } else {
        console.log("File input is missing. Please provide a file and try again.");
        fileSubmitServerMessage = "File input is missing. Please provide a file and try again.";
    }
});
