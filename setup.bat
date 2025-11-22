@echo off
REM Screenshot Sherlock Setup Script for Windows

echo 📱 Setting up Screenshot Sherlock...

REM Backend setup
echo 🔧 Setting up backend...
cd backend

REM Create virtual environment
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing Python dependencies...
pip install -r requirements.txt
echo Installing Tookie-OSINT dependencies...
pip install -r tookie-osint/requirements.txt

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo Creating .env file...
    copy .env.example .env
    echo ⚠️  Please edit backend\.env with your API keys and MongoDB URL
)

cd ..

REM Extension setup
echo 🔌 Extension is ready to load in Chrome
echo.
echo To load extension:
echo 1. Open Chrome and go to chrome://extensions/
echo 2. Enable 'Developer mode'
echo 3. Click 'Load unpacked'
echo 4. Select the 'extension' directory
echo.
echo ✅ Setup complete!
echo.
echo Next steps:
echo 1. Edit backend\.env with your credentials
echo 2. Start backend: cd backend ^&^& venv\Scripts\activate ^&^& python main.py
echo    Or use: daphne -b 127.0.0.1 -p 8000 main:app
echo 3. Load extension in Chrome
echo 4. Start analyzing conversations!

pause

