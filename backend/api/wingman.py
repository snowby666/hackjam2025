"""Wingman coaching endpoints"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel

from database import get_database
from database.schemas import Analysis
from api.auth import get_current_user
from services.wingman_service import WingmanService
from services.analysis_engine import AnalysisEngine

router = APIRouter()


class ReplyRequest(BaseModel):
    conversation_context: str
    current_message: Optional[str] = None


@router.post("/suggest-reply")
async def suggest_reply(
    request: ReplyRequest,
    current_user: dict = Depends(get_current_user)
):
    """Get AI-generated reply suggestions"""
    
    from services.ai_service import AIService
    ai_service = AIService()
    
    user_preferences = current_user.get("preferences", {})
    
    try:
        suggestions = await ai_service.generate_reply_suggestions(
            request.conversation_context,
            user_preferences
        )
        return {"suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate replies: {str(e)}")


@router.post("/reality-check/{analysis_id}")
async def reality_check(
    analysis_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get reality check intervention for overthinking"""
    
    db = await get_database()
    user_id = current_user["_id"]
    
    try:
        analysis_obj_id = ObjectId(analysis_id)
        analysis_doc = await db.analyses.find_one({"_id": analysis_obj_id})
        if not analysis_doc or analysis_doc["user_id"] != user_id:
            raise HTTPException(status_code=404, detail="Analysis not found")
    except:
        raise HTTPException(status_code=400, detail="Invalid analysis ID")
    
    # Convert to Analysis model
    analysis = Analysis(**analysis_doc)
    user_preferences = current_user.get("preferences", {})
    
    # Get reality check
    service = WingmanService()
    reality_check = await service.get_reality_check(analysis, user_preferences)
    
    # Update intervention stats
    await db.users.update_one(
        {"_id": user_id},
        {"$inc": {"stats.overthinking_interventions": 1}}
    )
    
    return reality_check


@router.get("/coaching/{analysis_id}")
async def get_coaching(
    analysis_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get personalized coaching advice"""
    
    db = await get_database()
    user_id = current_user["_id"]
    
    try:
        analysis_obj_id = ObjectId(analysis_id)
        analysis_doc = await db.analyses.find_one({"_id": analysis_obj_id})
        if not analysis_doc or analysis_doc["user_id"] != user_id:
            raise HTTPException(status_code=404, detail="Analysis not found")
    except:
        raise HTTPException(status_code=400, detail="Invalid analysis ID")
    
    analysis = Analysis(**analysis_doc)
    service = WingmanService()
    coaching = await service.get_coaching_advice(analysis)
    
    return coaching


@router.get("/quick-stats/{analysis_id}")
async def get_quick_stats(
    analysis_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get quick stats for UI display"""
    
    db = await get_database()
    user_id = current_user["_id"]
    
    try:
        analysis_obj_id = ObjectId(analysis_id)
        analysis_doc = await db.analyses.find_one({"_id": analysis_obj_id})
        if not analysis_doc or analysis_doc["user_id"] != user_id:
            raise HTTPException(status_code=404, detail="Analysis not found")
    except:
        raise HTTPException(status_code=400, detail="Invalid analysis ID")
    
    analysis = Analysis(**analysis_doc)
    service = WingmanService()
    stats = service.format_quick_stats(analysis)
    
    return stats


@router.post("/scenario")
async def run_scenario(
    scenario_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Run scenario simulation (placeholder for future feature)"""
    return {
        "message": "Scenario simulation coming soon",
        "scenario": scenario_data
    }

