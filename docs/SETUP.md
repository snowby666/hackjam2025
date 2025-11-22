# Quick Setup Guide

## Backend Setup (5 minutes)

1. **Navigate to backend directory**
```bash
cd backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
```

Edit `.env` and add:
- Your MongoDB connection string
- Your OpenAI API key
- A secret key for JWT (generate with: `openssl rand -hex 32`)

5. **Start the server**
```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

## Extension Setup (2 minutes)

1. **Open Chrome Extensions**
   - Navigate to `chrome://extensions/`
   - Enable "Developer mode" (toggle in top right)

2. **Load Extension**
   - Click "Load unpacked"
   - Select the `extension/` directory

3. **Configure API URL** (if needed)
   - Edit `extension/popup/popup.js`
   - Update `API_BASE_URL` if your backend is not on localhost:8000

4. **Test**
   - Click the extension icon
   - Click "Capture Screenshot"
   - You'll need to register/login first

## First Time Usage

1. **Register Account**
   - Open extension popup
   - The extension will prompt for login/register
   - Create an account with email/password

2. **Capture Screenshot**
   - Navigate to a page with text messages
   - Click extension icon
   - Click "Capture Screenshot"
   - Wait for analysis (3-5 seconds)

3. **View Results**
   - Analysis will show:
     - Interest score
     - Vibe report
     - Red/green flags
     - Suggested replies
     - Wingman advice

## Troubleshooting

### Backend Issues
- **Port already in use**: Change port in `.env` or kill process on port 8000
- **MongoDB connection failed**: Check connection string in `.env`
- **OpenAI API error**: Verify API key and check quota

### Extension Issues
- **Extension not loading**: Check `manifest.json` for errors
- **Screenshot fails**: Ensure you're on a page (not chrome:// pages)
- **API errors**: Check browser console (F12) for error messages
- **CORS errors**: Verify backend CORS settings allow extension origin

## Next Steps

- Read `docs/API.md` for API documentation
- Read `docs/ARCHITECTURE.md` for system design
- Customize prompts in `backend/utils/prompts.py`
- Add your own features!

