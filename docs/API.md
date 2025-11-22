# Screenshot Sherlock API Documentation

## Base URL
```
http://localhost:8000/api
```

## Authentication

Most endpoints require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

## Endpoints

### Authentication

#### Register
```
POST /api/auth/register
```

Request body:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

Response:
```json
{
  "access_token": "jwt_token_here",
  "token_type": "bearer"
}
```

#### Login
```
POST /api/auth/login
```

Request body (form data):
```
username: user@example.com
password: password123
```

Response:
```json
{
  "access_token": "jwt_token_here",
  "token_type": "bearer"
}
```

#### Get Current User
```
GET /api/auth/me
```

Headers: `Authorization: Bearer <token>`

Response:
```json
{
  "id": "user_id",
  "email": "user@example.com",
  "preferences": {
    "attachment_style": "secure",
    "dating_goal": "serious",
    "communication_style": "direct"
  },
  "stats": {
    "total_analyses": 42,
    "overthinking_interventions": 15,
    "messages_prevented": 7
  }
}
```

### Screenshots

#### Upload Screenshot
```
POST /api/screenshot/upload
```

Headers: `Authorization: Bearer <token>`

Request (multipart/form-data):
- `image`: File (PNG/JPEG)
- `platform`: String (optional)
- `participant_name`: String (optional)
- `conversation_id`: String (optional)

Response:
```json
{
  "conversation_id": "conv_id",
  "screenshot_id": "screenshot_id",
  "message": "Screenshot uploaded successfully"
}
```

### Analysis

#### Analyze Screenshot
```
POST /api/analyze/
```

Headers: `Authorization: Bearer <token>`

Request body:
```json
{
  "conversation_id": "conv_id",
  "screenshot_index": 0
}
```

Response:
```json
{
  "id": "analysis_id",
  "conversation_id": "conv_id",
  "user_id": "user_id",
  "interest_score": 75,
  "vibe_report": {
    "overall_mood": "positive",
    "engagement_level": "high",
    "communication_style": "secure",
    "emotional_temperature": 7.5
  },
  "red_flags": [...],
  "green_flags": [...],
  "power_dynamics": {...},
  "suggested_replies": [...],
  "wingman_notes": "...",
  "timestamp": "2025-01-15T10:00:00Z"
}
```

#### Get Analysis
```
GET /api/analyze/{analysis_id}
```

Headers: `Authorization: Bearer <token>`

### Conversations

#### List Conversations
```
GET /api/conversations/?limit=20&skip=0
```

Headers: `Authorization: Bearer <token>`

#### Get Conversation Timeline
```
GET /api/conversations/{conversation_id}/timeline
```

Headers: `Authorization: Bearer <token>`

### Wingman Features

#### Get Reality Check
```
POST /api/wingman/reality-check/{analysis_id}
```

Headers: `Authorization: Bearer <token>`

#### Get Coaching Advice
```
GET /api/wingman/coaching/{analysis_id}
```

Headers: `Authorization: Bearer <token>`

#### Get Quick Stats
```
GET /api/wingman/quick-stats/{analysis_id}
```

Headers: `Authorization: Bearer <token>`

