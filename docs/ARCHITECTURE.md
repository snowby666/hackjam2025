# Screenshot Sherlock Architecture

## System Overview

Screenshot Sherlock is a Chrome extension with a FastAPI backend that uses AI to analyze text conversations and provide relationship coaching.

## Components

### 1. Chrome Extension (Frontend)
- **manifest.json**: Extension configuration
- **background.js**: Service worker for screenshot capture
- **content.js**: Content script for page interaction
- **popup/**: Main UI components
  - `popup.html`: Main popup interface
  - `popup.js`: Popup logic
  - `popup.css`: Styling
- **utils/**: Utility functions
  - `api.js`: API communication
  - `storage.js`: Chrome storage wrapper
  - `screenshot.js`: Screenshot capture

### 2. FastAPI Backend
- **main.py**: Application entry point
- **config.py**: Configuration management
- **api/**: API endpoints
  - `auth.py`: Authentication
  - `screenshot.py`: Screenshot upload
  - `analysis.py`: Analysis endpoints
  - `wingman.py`: Wingman features
  - `conversations.py`: Conversation management
- **services/**: Business logic
  - `ai_service.py`: OpenAI integration
  - `analysis_engine.py`: Analysis processing
  - `wingman_service.py`: Coaching features
  - `image_processor.py`: Image handling
- **database/**: Database layer
  - `mongodb.py`: MongoDB connection
  - `schemas.py`: Data models

### 3. Database (MongoDB)
Collections:
- `users`: User accounts and preferences
- `conversations`: Conversation metadata
- `analyses`: Analysis results
- `user_profiles`: User behavior patterns

## Data Flow

1. User captures screenshot via extension
2. Extension uploads to backend
3. Backend processes image
4. Backend sends to OpenAI GPT-4o Vision
5. AI returns analysis
6. Backend structures and stores analysis
7. Extension displays results

## Security

- JWT authentication for API access
- User-scoped data access
- Secure password hashing (bcrypt)
- CORS protection

## AI Integration

- **Primary**: OpenAI GPT-4o Vision for image analysis
- **Prompt Engineering**: Context-aware prompts based on user preferences
- **Response Parsing**: JSON extraction and validation

