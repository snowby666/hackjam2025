# 📱 Screenshot Sherlock: The Ultimate Text Analysis Wingman

**Stop overthinking. Start winning. Your AI wingman that reads texts better than you do.**

## 🎯 What It Does

Screenshot Sherlock is an AI-powered Chrome extension that analyzes text conversations in real-time, provides instant psychological insights, and acts as your personal wingman to prevent overthinking and self-sabotage.

## 🚀 Quick Start

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
python main.py
# Or use: daphne -b 127.0.0.1 -p 8000 main:app
```

### Extension Setup

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `extension/` directory

## 🏗️ Architecture

- **Backend**: FastAPI (Python) with MongoDB
- **Frontend**: Chrome Extension (JavaScript/React)
- **AI**: OpenAI GPT-4o Vision for image analysis
- **Database**: MongoDB Atlas

## 📋 Features

- 📸 One-click screenshot capture
- 🧠 AI-powered conversation analysis
- 🛰️ **OSINT background check** support via Tookie-OSINT when “Advanced Mode” is enabled
- 📊 Interest score (0-100)
- 🚩 Red/Green flag detection
- 💬 Smart reply suggestions
- 🕊️ Real-time wingman coaching
- 🚨 Overthinking intervention system

## 📚 Documentation

See `docs/` directory for detailed API documentation and architecture details.

## 🔐 Environment Variables

See `.env.example` for required configuration. When enabling OSINT mode you’ll also want to create a `backend/.env.local` (or override your `.env`) with:

```
OSINT_ENABLED=true
TOOKIE_BASE_PATH=backend/tookie-osint
PYTHONIOENCODING=utf-8
```

The backend automatically handles UUID mapping and rate limits—just make sure MongoDB is reachable before running scans.

## 🏆 Built for Hackathon 2025

*Because everyone deserves a wingman who actually knows what they're talking about.* 🕵️‍♀️🕊️
