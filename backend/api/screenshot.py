"""Screenshot upload and management endpoints"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import Optional
from bson import ObjectId
from datetime import datetime

from database import get_database
from database.schemas import ScreenshotData, ScreenshotMetadata
from api.auth import get_current_user
from services.image_processor import ImageProcessor

router = APIRouter()


@router.post("/upload")
async def upload_screenshot(
    image: UploadFile = File(...),
    platform: Optional[str] = Form(None),
    participant_name: Optional[str] = Form(None),
    conversation_id: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """Upload screenshot for analysis"""
    
    # Read image data
    image_bytes = await image.read()
    
    # Process image
    processor = ImageProcessor()
    try:
        processed = await processor.process_screenshot(
            base64.b64encode(image_bytes).decode('utf-8')
        )
    except Exception as e:
        # If base64 encoding fails, use raw bytes
        processed = await processor.process_screenshot(
            base64.b64encode(image_bytes).decode('utf-8')
        )
    
    db = await get_database()
    user_uuid = current_user.get("uuid")
    
    # Create or update conversation
    if conversation_id:
        try:
            conv_obj_id = ObjectId(conversation_id)
            conversation = await db.conversations.find_one({"_id": conv_obj_id})
            if not conversation or conversation["user_id"] != user_uuid:
                raise HTTPException(status_code=404, detail="Conversation not found")
        except:
            raise HTTPException(status_code=400, detail="Invalid conversation ID")
    else:
        # Create new conversation
        conversation = {
            "user_id": user_uuid, # Use UUID
            "platform": platform or "unknown",
            "participant_name": participant_name,
            "screenshots": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        result = await db.conversations.insert_one(conversation)
        conv_obj_id = result.inserted_id
    
    # Add screenshot to conversation
    screenshot_data = {
        "image_data": base64.b64encode(image_bytes).decode('utf-8'),
        "uploaded_at": datetime.utcnow(),
        "metadata": {
            "width": processed.get("width"),
            "height": processed.get("height")
        } if processed.get("width") else None
    }
    
    await db.conversations.update_one(
        {"_id": conv_obj_id},
        {
            "$push": {"screenshots": screenshot_data},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    return {
        "conversation_id": str(conv_obj_id),
        "screenshot_id": str(ObjectId()),  # Generate ID for reference
        "message": "Screenshot uploaded successfully"
    }


import base64  # Add base64 import

