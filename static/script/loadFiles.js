import { extractedFileTextInput } from "./AIChatHandler.js";

const sidebarFileList = document.getElementById("sidebarFileList")
const fileDisplay = document.getElementById("fileDisplay")



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
            // Clear current list to avoid duplicates
            fileDisplay.innerHTML = "";
            sidebarFileList.innerHTML = "";
            
            data.files.forEach(file => {
                // Create list item for each file in the sidebar
                const sidebarFileListItem = document.createElement('li');
                sidebarFileListItem.className = "aside_list_item";
                sidebarFileListItem.innerHTML = 
                    `
                        <span class="material-symbols-outlined">picture_as_pdf</span>
                        <p class="aside_list_item_text">${file.file_name}</p>
                        <span class="material-symbols-outlined more_vert">more_vert</span>
                    `
                ;
                sidebarFileList.appendChild(sidebarFileListItem);

                // Create list item for each file in file display container
                const fileDisplayList = document.createElement('li');
                fileDisplayList.className = "file_display_list";
                fileDisplayList.innerHTML = 
                    `
                        <span class="material-symbols-outlined">picture_as_pdf</span>
                        <p class="pdfFileName">${file.file_name}</p>
                    `
                ;
                fileDisplay.appendChild(fileDisplayList)

                // Populate file extracted text to extractedFileTextInput when clicked
                sidebarFileListItem.addEventListener('click', () => {
                    console.log(`File Selected from sidebar: ${file.file_name}`);
                    extractedFileTextInput.value = file.extracted_text;
                });

                fileDisplayList.addEventListener('click', () => {
                    console.log(`File Selected from file display container: ${file.file_name}`);
                    extractedFileTextInput.value = file.extracted_text;
                });
            });
        } else {
            let errorMessage = data.error.replace(/^"|"$/g, ''); // Removes leading and trailing quotes
            sidebarFileList.innerHTML = `<li>${errorMessage}</li>`;
        }
    } catch (error) {
        console.error('There was a problem with the fetch operation:', error);
        sidebarFileList.innerHTML = `<li>Error loading files. Please try again later.</li>`;
    }
}





// Call function to retrieve files when DOMContent loads
document.addEventListener('DOMContentLoaded', () => {
    console.log("Retrieving files from the server...");
    loadFiles();
    console.log("Files retrieved successfully.");
});


export default loadFiles;