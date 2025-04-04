## DocGenius

An AI Assistance that helps you get information from an uploaded PDF file.

Chat with your PDF file and get responses. Build using Python (Flask), Vanilla Javascript and Gemini AI API.

### Features

- **Upload Files**: Upload PDF, TXT, DOCX, or PPTX files to extract their content.
- **Chat with Files**: Ask questions about the uploaded files and get AI-generated responses.
- **Recent Files**: View and select recently uploaded files.
- **Recent Chats**: Access previous conversations for reference.
- **Dynamic Content**: All file and chat data are dynamically loaded and updated.

### Technologies Used

- **Backend**: Python (Flask)
- **Frontend**: HTML, CSS, Vanilla JavaScript
- **Database**: SQLite for storing extracted file content and chat conversations.
- **AI Integration**: Gemini AI API for generating responses to user queries.

### Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/realitystevens/DocGenius.git
    cd DocGenius
    ```

2. Create a virtual environment and activate it:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Set up environment variables:
    - Create a `.env` file in the root directory.
    - Add the following variables:
      ```
      ENV = development
      GOOGLE_API_KEY = "<gemini-api-key>"
      ```
    - Add a Gemini AI Key. Get an API key from [here](https://aistudio.google.com/app/apikey)

5. Run the application:
    ```bash
    python app.py
    ```

6. Open your browser and navigate to `http://127.0.0.1:5000`.

### Usage

1. **Upload a File**:
    - Use the "Add a new PDF" section to upload a file.
    - Supported formats: PDF, TXT, DOCX, PPTX.

2. **Extract Text**:
    - The uploaded file's content will be extracted and stored in the database.

3. **Chat with the File**:
    - Select a file from the "Recent Files" section.
    - Enter a question in the chatbox and click the send button.
    - View the AI-generated response in the chat conversation area.

4. **View Recent Chats**:
    - Access previous conversations in the "Recent Chats" section.

### Project Structure

```
DocGenius/
├── static/
│   ├── AIChatHandler.js       # Handles AI chat interactions
│   ├── fileHandler.js         # Manages file-related operations
│   ├── saveFile.js            # Handles file upload and saving
│   └── style.css              # Styling for the application
├── templates/
│   └── index.html             # Main HTML template
├── utils/
│   ├── app_utils.py           # Utility functions for logging and AI responses
│   ├── extractText.py         # Functions for extracting text from files
├── app.py                     # Flask application entry point
├── requirements.txt           # Python dependencies
└── README.md                  # Project documentation
```

### Contributing

Contributions are welcome! Feel free to fork the repository and submit a pull request.

### License

This project is licensed under the MIT License. See the `LICENSE` file for details.

### Author

Built by [Reality Stevens](http://linkedin.com/in/stevensreality).  
View the codebase on [GitHub](http://github.com/realitystevens/DocGenius).
