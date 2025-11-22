from pydantic import BaseModel, EmailStr, Field, ConfigDict, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from typing import Optional, List, Dict, Any, Annotated
from datetime import datetime
from bson import ObjectId
import uuid


class PyObjectId(str):
    """Custom type for handling MongoDB ObjectId"""
    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: Any
    ) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.str_schema(),
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return handler(core_schema.str_schema())


# User Models
class UserPreferences(BaseModel):
    attachment_style: str = "secure"  # secure, anxious, avoidant
    dating_goal: str = "serious"  # casual, serious, exploring
    communication_style: str = "direct"  # direct, playful, deep
    advanced_mode: bool = False # Enable OSINT background checks


class UserStats(BaseModel):
    total_analyses: int = 0
    overthinking_interventions: int = 0
    messages_prevented: int = 0


class User(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    created_at: datetime = Field(default_factory=datetime.utcnow)
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    stats: UserStats = Field(default_factory=UserStats)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


# Conversation Models
class ScreenshotMetadata(BaseModel):
    width: int
    height: int


class ScreenshotData(BaseModel):
    image_data: str  # base64 or URL
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[ScreenshotMetadata] = None


class Conversation(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: str # UUID string
    platform: str  # iMessage, WhatsApp, etc.
    participant_name: Optional[str] = None
    screenshots: List[ScreenshotData] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


# Analysis Models
class VibeReport(BaseModel):
    overall_mood: str
    engagement_level: str
    communication_style: str
    emotional_temperature: float = 0.0


class Flag(BaseModel):
    type: str
    severity: Optional[str] = None
    significance: Optional[str] = None
    evidence: str
    detected_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


class PowerDynamics(BaseModel):
    leader: str
    effort_asymmetry: float = 0.0
    message_ratio: Optional[float] = None


class SuggestedReply(BaseModel):
    text: str
    tone: str
    success_probability: float
    risk_level: str = "low"
    rationale: Optional[str] = None


class Analysis(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    conversation_id: PyObjectId
    user_id: str # Changed from PyObjectId to str to support UUID
    interest_score: int
    vibe_report: VibeReport
    red_flags: List[Flag] = []
    green_flags: List[Flag] = []
    power_dynamics: PowerDynamics
    suggested_replies: List[SuggestedReply] = []
    wingman_notes: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    raw_ai_response: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


# User Profile Models
class UserProfile(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: str # Changed from PyObjectId to str to support UUID
    attachment_style: str
    triggers: List[str] = []
    patterns: Dict[str, Any] = {}
    conversation_stats: Dict[str, Any] = {}

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
