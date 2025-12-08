# Frontend Chat Assistant

A minimal React + TypeScript chat interface for the appointment scheduling backend.

## Features

- Single-page chat interface
- Session management with automatic session ID generation
- Markdown rendering for messages
- Clean, minimal UI with plain CSS
- Reload session functionality

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:3000`

## Configuration

The API endpoint is configured in `src/App.tsx`:
```typescript
const API_ENDPOINT = '/api/chat'
```

The Vite dev server is configured to proxy `/api` requests to `http://localhost:8000` (see `vite.config.ts`). Adjust this if your backend runs on a different port.

## Backend API Contract

The frontend expects the backend to accept:
- **Endpoint**: `POST /api/chat`
- **Request body**:
  ```json
  {
    "sessionId": "string",
    "message": "user message text"
  }
  ```
- **Response**: Should contain a message field (e.g., `{ "message": "..." }` or `{ "response": "..." }`)

The response parsing in `App.tsx` tries multiple common field names (`message`, `response`, `text`). Adjust if your backend uses a different format.

## Build

To build for production:
```bash
npm run build
```

The output will be in the `dist` folder.

