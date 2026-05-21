# EchoMind

EchoMind is an AI-powered conversational intelligence platform built to eliminate the tedious process of manual transcription, meeting analysis, and knowledge retrieval. By orchestrating workflows through **Google Gemini 2.5 Flash**, EchoMind transforms your raw audio, video, and text documents into searchable, structured intelligence dashboards.

## Features List

- **Transcription**: High-fidelity Whisper-tier AI transcriptions mapped to the Gemini backbone.
- **Diarization**: Advanced speaker separation dynamically formatted as an interactive chat UI.
- **Summary**: Automatic generation of engagement metrics and customized summary overviews.
- **Insights**: Actionable takeaways mapped using strict JSON parsing logic.
- **Sentiment Analysis**: Dynamic sentiment evaluation highlighting emotional keywords.
- **RAG Q&A**: Chat against your uploaded context seamlessly using Google Gemini embeddings.
- **Language Selection**: Generate transcriptions, summaries, and Q&A in English, Hindi, Urdu, or default.
- **Custom Summary**: Modify the length and format (Bullet points, Action Items, etc.) of your intelligent reports.
- **Admin Dashboard**: Secure portal for platform owners to manage active usage and users.
- **Profile & History**: Keep track of and replay past conversations directly from the user dashboard.
- **PDF Report**: Download intelligent reports securely offline via TXT and PDF generations.

## Technologies Used

- **HTML, Tailwind CSS, JavaScript**: Core frontend structure, styling, and interactive UI.
- **Flask (Python)**: Framework running the core HTTP server and API routing.
- **SQLite**: Dedicated lightweight RDBMS managing user states and document records.
- **Google Gemini API**: Artificial Intelligence core spanning embeddings, generative summarization, and RAG.
- **Chart.js**: Dynamic radar and polar metric charting on the client-side.

## Installation Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-repo/echomind.git
   cd echomind
   ```

2. **Establish the Virtual Environment**:
   ```bash
   python -m venv .venv
   # On Windows
   .venv\Scripts\activate
   # On Mac/Linux
   source .venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables Config**:
   Create a `.env` file at the root folder specifying:
   ```env
   SECRET_KEY=super-secret-production-key-placeholder
   GEMINI_API_KEY=your_google_ai_gemini_api_key
   ```

## How to Run

1. Ensure your virtual environment is activated and `.env` is properly configured.
2. Run the server locally:
   ```bash
   python app.py
   ```
3. The Flask app will be accessible at: `http://localhost:5000`

## Project Structure

```text
├── app.py                   # Main Flask Application Entry Point
├── /database
│   └── db.py                # SQLAlchemy DB Bootstrap
├── /models                  # Data Access Logic
│   ├── user.py              # User Accounts and Auth
│   └── document.py          # Upload and Relationship records
├── /routes                  # Web and API routing
│   ├── api.py               # Asynchronous API Logic mapped to Gemini UI calls
│   ├── auth.py              # User Login & Signup Logic
│   ├── pages.py             # Landing generic templated pages
│   ├── profile.py           # User specific historical pages
│   └── admin.py             # Administrative control dashboard
├── /templates               # HTML View templates (Jinja2)
├── /utils                   # Machine Learning Helper Files
│   ├── gemini_helper.py     # Invokes LLM Prompting & File Uploads
│   └── rag_helper.py        # Maps Vector Embeddings 
└── requirements.txt         # Standard PyPi dependencies
```

## Future Improvements

- **Scalable Document Store**: Migrating towards Pinecone / ChromaDB external stores instead of RAM arrays built into `rag_helper.py` dictionary pools.
- **Enterprise IAM Roles**: Strict permission mapping using OAuth2 workflows over native SQLite user tracking.
- **Websocket Transcription Streaming**: Removing HTTP wait overhead via continuous Server-Sent-Events formatting.


