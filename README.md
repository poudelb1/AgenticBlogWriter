# CrewAI Multi-Agent Blog Generator

## Description

This project provides a web interface and a FastAPI backend to generate blog posts automatically. It uses the CrewAI framework to orchestrate multiple AI agents (Researcher, Writer, Editor, Image Generator) that collaborate to create content on a given topic, complete with a title, Markdown body, and an illustrative image URL.

## Features

* **Web UI:** Simple frontend built with HTML, CSS, and JavaScript to input topics and display results.
* **FastAPI Backend:** Robust API endpoint to handle blog generation requests.
* **Multi-Agent System:** Uses CrewAI to manage a sequence of specialized AI agents.
* **Research:** An agent searches the web (using Serper) for the latest information.
* **Writing:** An agent drafts the blog post based on research.
* **Editing:** An agent refines the draft, suggests a title, and formats the output.
* **Image Generation:** An agent generates a relevant image URL (using OpenAI's DALL-E via API).
* **Markdown Output:** Blog body is provided in Markdown format, rendered in the UI.

## Tech Stack

* **Backend:** Python 3.10+, FastAPI, Uvicorn, CrewAI, Langchain, OpenAI API
* **Frontend:** HTML, CSS, Vanilla JavaScript, Marked.js (for Markdown rendering)
* **Search:** Serper API (via google-search-results)
* **Environment:** python-dotenv

## Setup Instructions

1.  **Prerequisites:**
    * Python 3.10 or later installed.
    * `pip` (Python package installer).
    * Git (for cloning the repository).

2.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd <repository-directory>
    ```

3.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **API Key Configuration:**
    * You need API keys from OpenAI and Serper.
    * Create a file named `.env` in the root project directory.
    * Add your keys to the `.env` file like this:

        ```dotenv
        OPENAI_API_KEY=your_openai_api_key_here
        SERPER_API_KEY=your_serper_api_key_here

        # Optional: You can override default host/port here if needed
        # HOST=127.0.0.1
        # PORT=8080
        ```
    * **Important:** Replace `your_openai_api_key_here` and `your_serper_api_key_here` with your actual keys. Keep this file secure and do not commit it to public repositories.

## Running the Application

1.  **Start the Backend Server:**
    * Make sure your virtual environment is activated.
    * Run the FastAPI application using Uvicorn:
        ```bash
        # Option 1: Simple run
        python app.py

        # Option 2: Run with auto-reload (useful for development)
        uvicorn app:app --reload
        ```
    * The backend server will typically start on `http://localhost:8000`. You'll see log messages in your terminal.

2.  **Open the Frontend:**
    * Navigate to the project directory in your file explorer.
    * Double-click the `index.html` file, or right-click and choose "Open with" your preferred web browser (Chrome, Firefox, Edge, etc.).

## Usage

1.  Once the backend is running and the `index.html` page is open in your browser:
2.  Enter the desired topic for your blog post in the input field (e.g., "The impact of AI on creative writing").
3.  Click the "Generate Blog" button.
4.  Wait for the process to complete. You'll see a loading indicator. This may take a minute or more depending on the complexity and API response times.
5.  The generated blog title, image, and formatted body (rendered from Markdown) will appear on the page.
6.  If an error occurs, an error message will be displayed. Check the backend terminal logs for more details.

## Project Structure