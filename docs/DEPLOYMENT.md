# Deployment Guide

## Backend Deployment

### Prerequisites
- Python 3.11+
- MongoDB Atlas account (or local MongoDB)
- OpenAI API key

### Local Development Setup

1. **Install dependencies**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. **Run server**
```bash
uvicorn main:app --reload --port 8000
```

### Production Deployment (Example: Railway/Render)

1. **Set environment variables** in your hosting platform:
   - `MONGODB_URL`
   - `OPENAI_API_KEY`
   - `SECRET_KEY`
   - `MONGODB_DB_NAME`

2. **Deploy**
   - Connect your repository
   - Set build command: `pip install -r requirements.txt`
   - Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Update CORS** in `config.py` to include your production URL

## Extension Deployment

### Development Load

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `extension/` directory

### Chrome Web Store (Production)

1. Create a zip file of the `extension/` directory
2. Go to Chrome Web Store Developer Dashboard
3. Upload zip file
4. Fill out store listing details
5. Submit for review

## MongoDB Setup

### MongoDB Atlas (Recommended)

1. Create account at mongodb.com/cloud/atlas
2. Create a new cluster
3. Create database user
4. Whitelist IP addresses (0.0.0.0/0 for development)
5. Get connection string
6. Update `MONGODB_URL` in `.env`

### Local MongoDB

```bash
# Install MongoDB locally
# Update MONGODB_URL to: mongodb://localhost:27017/
```

## Environment Variables

Required variables:
- `MONGODB_URL` - MongoDB connection string
- `OPENAI_API_KEY` - OpenAI API key
- `SECRET_KEY` - JWT secret key (generate with: `openssl rand -hex 32`)

Optional:
- `ANTHROPIC_API_KEY` - For Claude integration
- `API_HOST` - Server host (default: 0.0.0.0)
- `API_PORT` - Server port (default: 8000)
- `DEBUG` - Debug mode (default: True)

## Troubleshooting

### Backend won't start
- Check MongoDB connection string
- Verify all environment variables are set
- Check Python version (3.11+)

### Extension not working
- Check browser console for errors
- Verify API URL in `popup.js` matches backend
- Check CORS settings
- Verify authentication token is stored

### Analysis fails
- Verify OpenAI API key is valid
- Check API quota/limits
- Review error logs in backend

