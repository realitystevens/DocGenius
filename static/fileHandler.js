import { extractedFileTextInput } from "./AIChatHandler.js";

const fileList = document.getElementById("fileList");
const fileDisplayList = document.getElementById("fileDisplayList");



async function loadFiles() {
    try {
        const response = await fetch('/api/v1/files');
        if (!response.ok) {
            throw new Error(`
                Network response was not ok: ${response.statusText}. 
                Status: ${response.status}
            `);
        }
        const data = await response.json();
        if (data.files && Array.isArray(data.files)) {
            fileList.innerHTML = ""; // Clear current list to avoid duplicates
            data.files.forEach(file => {
                // Create a list item for each file in aside bar
                const fileListItem = document.createElement('li');
                fileListItem.className = "aside_list_item";
                fileListItem.innerHTML = 
                    `
                        <span class="material-symbols-outlined">picture_as_pdf</span>
                        <p class="aside_list_item_text">${file.file_name}</p>
                        <span class="material-symbols-outlined more_vert">more_vert</span>
                    `
                ;
                // Populate file extracted text to extractedFileTextInput when clicked
                fileListItem.addEventListener('click', () => {
                    console.log(`File Selected from aside bar: ${file.file_name}`);
                    extractedFileTextInput.value = file.extracted_text;
                });
                fileList.appendChild(fileListItem);

                // Create a list item for each file in the file display container
                const fileDisplayListItem = document.createElement('li');
                fileDisplayListItem.className = "pdf_display_item";
                fileDisplayListItem.innerHTML = 
                    `
                        <span class="material-symbols-outlined">picture_as_pdf</span>
                        <p class="pdfFileName">${file.file_name}</p>
                    `
                ;
                // Populate file extracted text to extractedFileTextInput when clicked
                fileDisplayListItem.addEventListener('click', () => {
                    console.log(`File Selected from display container: ${file.file_name}`);
                    extractedFileTextInput.value = file.extracted_text;
                });
                fileDisplayList.appendChild(fileDisplayListItem);
            });
        } else {
            let errorMessage = data.error.replace(/^"|"$/g, ''); // Removes leading and trailing quotes
            fileList.innerHTML = `<li>${errorMessage}</li>`;
        }
    } catch (error) {
        console.error('There was a problem with the fetch operation:', error);
        fileList.innerHTML = `<li>Error loading files. Please try again later.</li>`;
    }
}

// Call function to retrieve files when DOMContent loads
document.addEventListener('DOMContentLoaded', () => {
    console.log("Retrieving files from the server...");
    loadFiles();
    console.log("Files retrieved successfully.");
});


export default loadFiles;