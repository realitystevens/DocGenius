## DocGenius

An AI Assistance that helps you get information from an uploaded PDF file.

Chat with your PDF file and get responses. Build using Python (Flask), Vanilla Javascript and Gemini AI API and Redis Caching DB


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
      ENV = "development"
      GOOGLE_API_KEY = "<gemini-api-key>"
      REDIS_HOST = "<redis-host>"
      REDIS_PASSWORD = "<redis-password>"
      ```
    - Get a Google Gemini AI API key from [here](https://aistudio.google.com/app/apikey)
    - Get a Redis Cache DB from [here](https://console.upstash.com/redis)

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



- Contributions are welcome! Feel free to fork the repository and submit a pull request.

Built by [Reality Stevens](http://linkedin.com/in/stevensreality). [realitystevens.me](http://realitystevens.me/)  
