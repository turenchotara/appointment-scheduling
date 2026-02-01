# Appointment Scheduling Assistant

An AI-powered appointment scheduling chatbot built with FastAPI, LangGraph, and ChromaDB. The assistant helps users book appointments, check availability, and answer frequently asked questions.

## Features

- **Conversational AI Agent**: Natural language interface for scheduling appointments
- **Multi-LLM Support**: Configurable to use Azure OpenAI or Google Gemini
- **FAQ Knowledge Base**: RAG-powered FAQ retrieval using ChromaDB vector store
- **Appointment Management**: Check availability and book appointments via Cal.com API
- **Session Management**: Maintains conversation context across messages

## Project Structure

```
appointment-scheduling/
├── backend/
│   ├── __init__.py              # Package initialization and FastAPI app
│   ├── main.py                  # Entry point
│   ├── settings.py              # Configuration settings
│   ├── logging_config.py        # Logging setup
│   ├── module_loader.py         # Dynamic module loading
│   ├── app_factory.py           # FastAPI application factory
│   ├── agent/
│   │   ├── scheduling_agent.py  # LangGraph agent workflow
│   │   ├── llm_config.py        # LLM configuration
│   │   ├── state.py             # Agent state definitions
│   │   ├── tool_node.py         # Tool execution node
│   │   └── prompt.py            # System prompt
│   ├── api/
│   │   ├── chat.py              # Chat endpoints
│   │   └── calendly_integration.py  # Appointment booking endpoints
│   ├── models/
│   │   └── schema.py            # Pydantic models
│   ├── protocols/
│   │   ├── llm.py               # LLM protocol interface
│   │   └── vector_store.py      # Vector store protocol interface
│   ├── rag/
│   │   ├── faq.py               # FAQ management
│   │   └── vector_store.py      # ChromaDB implementation
│   ├── tools/
│   │   ├── availability_tool.py # Check availability tool
│   │   ├── booking_tool.py      # Book appointment tool
│   │   └── retrieve.py          # FAQ retrieval tool
│   └── data/
│       └── clinic_info.json     # FAQ and clinic data
├── frontend/
│   └── src/
│       └── App.tsx              # React chat interface
├── requirements.txt
└── .env                         # Environment variables
```

## Installation

### Prerequisites

- Python 3.12+
- Node.js 18+ (for frontend)

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd appointment-scheduling
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # or
   .venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install sentence_transformers
   ```

4. **Configure environment variables**
   
   Create a `.env` file in the project root:
   ```env
   # Application Data Paths
   FAQ_DATA_PATH=backend/data/clinic_info.json
   DB_PATH=backend/data/chroma_db
   COLLECTION_NAME=faq_collection
   SCHEDULE_FILE_PATH=backend/doctor_schedule.json

   # Cal.com API Settings
   API_KEY=your_cal_com_api_key

   # Azure OpenAI Settings
   AZURE_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_DEPLOYMENT=gpt-4.1
   AZURE_API_KEY=your_azure_api_key
   AZURE_API_VERSION=2024-02-15-preview

   # Google Gemini Settings (optional)
   GOOGLE_API_KEY=your_google_api_key
   ```

5. **Run the backend**
   ```bash
   cd /path/to/appointment-scheduling
   uvicorn backend:app --host 0.0.0.0 --port 8000
   ```
   
   Or with auto-reload for development:
   ```bash
   uvicorn backend:app --host 0.0.0.0 --port 8000 --reload
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Run the development server**
   ```bash
   npm run dev
   ```

## API Endpoints

### Chat Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/chat` | Send a chat message |
| POST | `/training-faq` | Index FAQ documents |
| GET | `/search-faq/{query}` | Search FAQ directly |

### Calendly Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/calendly/availability` | Get available time slots |
| POST | `/api/calendly/book` | Book an appointment |

## Usage

### Training the FAQ

Before using the chat, index the FAQ documents:

```bash
curl -X POST http://localhost:8000/training-faq
```

### Chat Example

```bash
curl "http://localhost:8000/chat?user_query=What%20appointments%20are%20available&session_id=user123"
```

### Check Availability

```bash
curl "http://localhost:8000/api/calendly/availability?date=2024-11-04&appointment_type=General%20Consultation"
```

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   FastAPI   │────▶│  LangGraph  │
│   (React)   │     │   Backend   │     │    Agent    │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
                    ▼                          ▼                          ▼
            ┌───────────────┐         ┌───────────────┐         ┌───────────────┐
            │  Availability │         │    Booking    │         │  FAQ Retrieval│
            │     Tool      │         │     Tool      │         │     Tool      │
            └───────┬───────┘         └───────┬───────┘         └───────┬───────┘
                    │                         │                         │
                    ▼                         ▼                         ▼
            ┌───────────────┐         ┌───────────────┐         ┌───────────────┐
            │   Cal.com     │         │   Cal.com     │         │   ChromaDB    │
            │     API       │         │     API       │         │ Vector Store  │
            └───────────────┘         └───────────────┘         └───────────────┘
```

## Configuration

### Switching LLM Providers

In `backend/agent/scheduling_agent.py`, change the provider:

```python
# Use Azure OpenAI (default)
model_with_tools = get_llm_with_tools(tools, provider="azure")

# Use Google Gemini
model_with_tools = get_llm_with_tools(tools, provider="gemini")
```

## Development

### Code Quality

The codebase follows:
- **Type Hints**: Comprehensive type annotations throughout
- **SOLID Principles**: 
  - Single Responsibility: Separate modules for logging, config, app factory
  - Dependency Inversion: Protocol-based abstractions for LLM and VectorStore
- **Documentation**: Docstrings for all public functions and classes

### Adding New Tools

1. Create a new tool in `backend/tools/`
2. Define a Pydantic schema for the tool arguments
3. Decorate the function with `@tool(args_schema=YourSchema)`
4. Add the tool to `backend/tools/__init__.py`

## License

MIT License
