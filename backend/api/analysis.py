"""Analysis endpoints"""

from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel

from database import get_database
from database.schemas import Analysis
from api.auth import get_current_user
from services.ai_service import AIService
from services.analysis_engine import AnalysisEngine

router = APIRouter()
ai_service = AIService()


class AnalysisRequest(BaseModel):
    conversation_id: str
    screenshot_index: int = 0


@router.post("/")
async def analyze_screenshot(
    request: AnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    """Analyze a screenshot from a conversation"""
    
    db = await get_database()
    user_id = current_user["_id"]
    conversation_id = request.conversation_id
    screenshot_index = request.screenshot_index
    
    # Get conversation
    try:
        conv_obj_id = ObjectId(conversation_id)
        conversation = await db.conversations.find_one({"_id": conv_obj_id})
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if conversation["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
    except:
        raise HTTPException(status_code=400, detail="Invalid conversation ID")
    
    # Get screenshot
    screenshots = conversation.get("screenshots", [])
    if screenshot_index >= len(screenshots):
        raise HTTPException(status_code=404, detail="Screenshot not found")
    
    screenshot = screenshots[screenshot_index]
    image_data = screenshot["image_data"]
    
    # Decode base64 image
    import base64
    image_bytes = base64.b64decode(image_data)
    
    # Get user preferences for context
    user_preferences = current_user.get("preferences", {})
    
    # Determine conversation stage (simplified - could be enhanced)
    screenshot_count = len(screenshots)
    conversation_stage = "early" if screenshot_count <= 3 else "established"
    
    # Analyze with AI
    try:
        ai_response = await ai_service.analyze_screenshot(
            image_bytes,
            user_preferences,
            conversation_stage
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    
    # Process AI response into structured format
    engine = AnalysisEngine()
    analysis = engine.process_ai_response(
        ai_response,
        str(conv_obj_id),
        str(user_id)
    )
    
    # Update conversation with extracted metadata (platform/participant)
    update_data = {}
    if "platform" in ai_response and ai_response["platform"]:
        update_data["platform"] = ai_response["platform"]
    if "participant_name" in ai_response and ai_response["participant_name"]:
        update_data["participant_name"] = ai_response["participant_name"]
    
    if update_data:
        await db.conversations.update_one(
            {"_id": conv_obj_id},
            {"$set": update_data}
        )
    
    # Save analysis to database
    analysis_dict = analysis.model_dump(by_alias=True, exclude={"id"})
    result = await db.analyses.insert_one(analysis_dict)
    
    # Update user stats
    await db.users.update_one(
        {"_id": user_id},
        {"$inc": {"stats.total_analyses": 1}}
    )
    
    # Return analysis with ID
    analysis_dict["id"] = str(result.inserted_id)
    # Remove _id to avoid serialization issues with raw ObjectId
    if "_id" in analysis_dict:
        del analysis_dict["_id"]
    
    return analysis_dict


@router.get("/{analysis_id}")
async def get_analysis(
    analysis_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get analysis by ID"""
    
    db = await get_database()
    user_id = current_user["_id"]
    
    try:
        if not ObjectId.is_valid(analysis_id):
             raise HTTPException(status_code=400, detail="Invalid analysis ID format")
             
        analysis_obj_id = ObjectId(analysis_id)
        analysis = await db.analyses.find_one({"_id": analysis_obj_id})
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
            
        # Verify ownership (ObjectId vs str check)
        # existing data might use ObjectId, new might use str for user_id
        analysis_user_id = analysis.get("user_id")
        if str(analysis_user_id) != str(user_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        analysis["id"] = str(analysis["_id"])
        if "_id" in analysis:
            del analysis["_id"]
            
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@router.get("/conversation/{conversation_id}")
async def get_conversation_analyses(
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all analyses for a conversation"""
    
    db = await get_database()
    user_id = current_user["_id"]
    
    try:
        conv_obj_id = ObjectId(conversation_id)
        # Verify conversation belongs to user
        conversation = await db.conversations.find_one({"_id": conv_obj_id})
        if not conversation or conversation["user_id"] != user_id:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get analyses
        analyses = await db.analyses.find(
            {"conversation_id": conv_obj_id}
        ).sort("timestamp", -1).to_list(length=100)
        
        for analysis in analyses:
            analysis["id"] = str(analysis["_id"])
        
        return analyses
    except HTTPException:
        raise
    except:
        raise HTTPException(status_code=400, detail="Invalid conversation ID")

