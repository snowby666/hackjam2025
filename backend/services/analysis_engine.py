"""Core analysis engine that processes AI responses and structures data"""

from typing import Dict, Any, Optional
from database.schemas import (
    Analysis, VibeReport, Flag, PowerDynamics, SuggestedReply
)
from datetime import datetime


class AnalysisEngine:
    """Process and structure AI analysis results"""
    
    @staticmethod
    def process_ai_response(
        ai_response: Dict[str, Any],
        conversation_id: str,
        user_id: str
    ) -> Analysis:
        """Convert AI response to structured Analysis model"""
        
        # Extract vibe report
        vibe_data = ai_response.get("vibe_report", {})
        vibe_report = VibeReport(
            overall_mood=vibe_data.get("overall_mood", "neutral"),
            engagement_level=vibe_data.get("engagement_level", "medium"),
            communication_style=vibe_data.get("communication_style", "secure"),
            emotional_temperature=vibe_data.get("emotional_temperature", 5.0)
        )
        
        # Extract red flags
        red_flags = []
        for flag_data in ai_response.get("red_flags", []):
            red_flags.append(Flag(
                type=flag_data.get("type", "unknown"),
                severity=flag_data.get("severity", "low"),
                evidence=flag_data.get("evidence", ""),
                detected_at=datetime.utcnow()
            ))
        
        # Extract green flags
        green_flags = []
        for flag_data in ai_response.get("green_flags", []):
            green_flags.append(Flag(
                type=flag_data.get("type", "unknown"),
                significance=flag_data.get("significance", "medium"),
                evidence=flag_data.get("evidence", "")
            ))
        
        # Extract power dynamics
        power_data = ai_response.get("power_dynamics", {})
        power_dynamics = PowerDynamics(
            leader=power_data.get("leader", "balanced"),
            effort_asymmetry=power_data.get("effort_asymmetry", 0.0),
            message_ratio=power_data.get("message_ratio")
        )
        
        # Extract suggested replies
        suggested_replies = []
        for reply_data in ai_response.get("suggested_replies", []):
            suggested_replies.append(SuggestedReply(
                text=reply_data.get("text", ""),
                tone=reply_data.get("tone", "direct"),
                success_probability=reply_data.get("success_probability", 0.5),
                risk_level=reply_data.get("risk_level", "low"),
                rationale=reply_data.get("rationale")
            ))
        
        # Create analysis object
        analysis = Analysis(
            conversation_id=conversation_id,
            user_id=user_id,
            interest_score=ai_response.get("interest_score", 50),
            vibe_report=vibe_report,
            red_flags=red_flags,
            green_flags=green_flags,
            power_dynamics=power_dynamics,
            suggested_replies=suggested_replies,
            wingman_notes=ai_response.get("wingman_notes", "Keep the conversation going!"),
            timestamp=datetime.utcnow(),
            raw_ai_response=ai_response.get("raw_ai_response")
        )
        
        return analysis
    
    @staticmethod
    def calculate_conversation_health(analysis: Analysis) -> float:
        """Calculate overall conversation health score (0-10)"""
        base_score = analysis.interest_score / 10  # Convert 0-100 to 0-10
        
        # Adjust for red flags
        red_flag_penalty = len(analysis.red_flags) * 0.5
        for flag in analysis.red_flags:
            if flag.severity == "high":
                red_flag_penalty += 1.0
            elif flag.severity == "medium":
                red_flag_penalty += 0.5
        
        # Boost for green flags
        green_flag_boost = len(analysis.green_flags) * 0.2
        
        # Adjust for power dynamics
        power_adjustment = abs(analysis.power_dynamics.effort_asymmetry) * -0.5
        
        health_score = base_score - red_flag_penalty + green_flag_boost + power_adjustment
        
        # Clamp between 0 and 10
        return max(0.0, min(10.0, health_score))
    
    @staticmethod
    def detect_overthinking_patterns(user_id: str, recent_analyses: list) -> Dict[str, Any]:
        """Detect if user is overthinking based on analysis patterns"""
        if len(recent_analyses) < 2:
            return {"is_overthinking": False, "reason": "Insufficient data"}
        
        # Check for rapid repeated analyses
        time_diffs = []
        for i in range(1, len(recent_analyses)):
            diff = (recent_analyses[i-1].timestamp - recent_analyses[i].timestamp).total_seconds()
            time_diffs.append(diff)
        
        avg_time_diff = sum(time_diffs) / len(time_diffs) if time_diffs else 0
        
        # If analyzing same conversation multiple times in short period
        if avg_time_diff < 300:  # Less than 5 minutes between analyses
            return {
                "is_overthinking": True,
                "reason": "Multiple analyses in short time period",
                "severity": "high" if avg_time_diff < 60 else "medium"
            }
        
        # Check for declining interest scores causing anxiety
        interest_scores = [a.interest_score for a in recent_analyses]
        if len(interest_scores) >= 3:
            recent_avg = sum(interest_scores[-3:]) / 3
            if recent_avg < 40:
                return {
                    "is_overthinking": True,
                    "reason": "Low interest scores may be causing anxiety",
                    "severity": "medium"
                }
        
        return {"is_overthinking": False, "reason": "Normal usage pattern"}

