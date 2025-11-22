"""Conversation management endpoints"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from bson import ObjectId
from datetime import datetime

from database import get_database
from api.auth import get_current_user

router = APIRouter()


@router.get("/")
async def list_conversations(
    limit: int = 20,
    skip: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """List user's conversations"""
    
    db = await get_database()
    user_id = current_user["_id"]
    
    conversations = await db.conversations.find(
        {"user_id": user_id}
    ).sort("updated_at", -1).skip(skip).limit(limit).to_list(length=limit)
    
    for conv in conversations:
        conv["id"] = str(conv["_id"])
        if "user_id" in conv:
            conv["user_id"] = str(conv["user_id"])
        
        # Remove _id to avoid serialization issues if not handled by model
        if "_id" in conv:
            del conv["_id"]
            
        # Get latest analysis if exists (support both ObjectId and string conversation_id)
        latest_analysis = None
        try:
            latest_analysis = await db.analyses.find_one(
                {"conversation_id": ObjectId(conv["id"])},
                sort=[("timestamp", -1)]
            )
        except Exception:
            pass
        if not latest_analysis:
            latest_analysis = await db.analyses.find_one(
                {"conversation_id": conv["id"]},
                sort=[("timestamp", -1)]
            )
        if latest_analysis:
            conv["latest_interest_score"] = latest_analysis.get("interest_score")
            conv["latest_analysis_id"] = str(latest_analysis["_id"])
        else:
            conv["latest_interest_score"] = None
            conv["latest_analysis_id"] = None
    
    return conversations


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get specific conversation"""
    
    db = await get_database()
    user_id = current_user["_id"]
    
    try:
        conv_obj_id = ObjectId(conversation_id)
        conversation = await db.conversations.find_one({"_id": conv_obj_id})
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if conversation["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        conversation["id"] = str(conversation["_id"])
        conversation["user_id"] = str(conversation["user_id"])
        if "_id" in conversation:
            del conversation["_id"]
            
        return conversation
    except HTTPException:
        raise
    except:
        raise HTTPException(status_code=400, detail="Invalid conversation ID")


@router.post("/")
async def create_conversation(
    platform: str,
    participant_name: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Create new conversation"""
    
    db = await get_database()
    user_id = current_user["_id"]
    
    conversation = {
        "user_id": user_id,
        "platform": platform,
        "participant_name": participant_name,
        "screenshots": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.conversations.insert_one(conversation)
    
    return {
        "id": str(result.inserted_id),
        "message": "Conversation created successfully"
    }


@router.put("/{conversation_id}")
async def update_conversation(
    conversation_id: str,
    participant_name: Optional[str] = None,
    platform: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Update conversation"""
    
    db = await get_database()
    user_id = current_user["_id"]
    
    try:
        conv_obj_id = ObjectId(conversation_id)
        conversation = await db.conversations.find_one({"_id": conv_obj_id})
        if not conversation or conversation["user_id"] != user_id:
            raise HTTPException(status_code=404, detail="Conversation not found")
    except HTTPException:
        raise
    except:
        raise HTTPException(status_code=400, detail="Invalid conversation ID")
    
    update_data = {"updated_at": datetime.utcnow()}
    if participant_name is not None:
        update_data["participant_name"] = participant_name
    if platform is not None:
        update_data["platform"] = platform
    
    await db.conversations.update_one(
        {"_id": conv_obj_id},
        {"$set": update_data}
    )
    
    return {"message": "Conversation updated successfully"}


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete conversation"""
    
    db = await get_database()
    user_id = current_user["_id"]
    
    try:
        conv_obj_id = ObjectId(conversation_id)
        conversation = await db.conversations.find_one({"_id": conv_obj_id})
        if not conversation or conversation["user_id"] != user_id:
            raise HTTPException(status_code=404, detail="Conversation not found")
    except HTTPException:
        raise
    except:
        raise HTTPException(status_code=400, detail="Invalid conversation ID")
    
    # Delete conversation and associated analyses
    await db.conversations.delete_one({"_id": conv_obj_id})
    await db.analyses.delete_many({"conversation_id": conv_obj_id})
    
    return {"message": "Conversation deleted successfully"}


@router.get("/{conversation_id}/timeline")
async def get_conversation_timeline(
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get interest score timeline for conversation"""
    
    db = await get_database()
    user_id = current_user["_id"]
    
    try:
        conv_obj_id = ObjectId(conversation_id)
        conversation = await db.conversations.find_one({"_id": conv_obj_id})
        if not conversation or conversation["user_id"] != user_id:
            raise HTTPException(status_code=404, detail="Conversation not found")
    except HTTPException:
        raise
    except:
        raise HTTPException(status_code=400, detail="Invalid conversation ID")
    
    # Get all analyses for this conversation
    analyses = await db.analyses.find(
        {"conversation_id": conv_obj_id}
    ).sort("timestamp", 1).to_list(length=100)
    
    timeline = [
        {
            "timestamp": str(analysis["timestamp"]),
            "interest_score": analysis.get("interest_score", 50),
            "analysis_id": str(analysis["_id"])
        }
        for analysis in analyses
    ]
    
    return {"timeline": timeline}

