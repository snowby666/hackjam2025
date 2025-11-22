from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional

from services.osint_service import OsintService
from services.ai_service import AIService
from api.auth import get_current_user

router = APIRouter()
osint_service = OsintService()
ai_service = AIService()

class OsintRequest(BaseModel):
    conversation_id: str

class OsintResult(BaseModel):
    username: str
    found_accounts: List[dict]
    risk_level: str # low, medium, high based on findings

@router.post("/check/{username}")
async def check_username(username: str, current_user: dict = Depends(get_current_user)):
    """Direct OSINT check for a username"""
    try:
        results = await osint_service.check_username(username)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze_context")
async def analyze_context_for_osint(
    request: OsintRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    1. Fetch conversation
    2. Use LLM to extract potential OSINT targets (usernames, emails)
    3. Run OSINT check on best candidate
    """
    from database import get_database
    from bson import ObjectId
    
    db = await get_database()
    
    # Get conversation
    try:
        conv = await db.conversations.find_one({"_id": ObjectId(request.conversation_id)})
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
    except:
        raise HTTPException(status_code=400, detail="Invalid ID")

    # Get latest analysis to find context or raw text if available
    # For now, we'll use the participant name if it looks like a username, 
    # or ask LLM to extract from the last screenshot (re-analysis cost)
    # BETTER: Use the extracted 'participant_name' from the analysis metadata
    
    target_username = conv.get("participant_name")
    
    if not target_username or target_username == "Unknown":
        return {"message": "No target username found in conversation metadata"}
        
    # Clean username (remove @, spaces)
    clean_username = target_username.replace("@", "").strip()
    if " " in clean_username:
        # If name has spaces (e.g. "John Doe"), it's likely a display name, not a username.
        # We could try to guess, but for OSINT we really need a handle.
        # Let's try to use LLM to guess a handle or return early.
        return {"message": "Participant name appears to be a full name, not a username. OSINT skipped."}

    # Run OSINT
    osint_results = await osint_service.check_username(clean_username)
    
    return osint_results

