"""Wingman service for real-time coaching features"""

from typing import Dict, Any, List
from services.analysis_engine import AnalysisEngine
from database.schemas import Analysis


class WingmanService:
    """Handle wingman coaching features"""
    
    @staticmethod
    async def get_reality_check(analysis: Analysis, user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Provide reality check to prevent overthinking"""
        
        interest_score = analysis.interest_score
        red_flags_count = len(analysis.red_flags)
        green_flags_count = len(analysis.green_flags)
        
        # Generate reality check message
        if interest_score >= 70:
            message = f"Stop overthinking! Interest score is {interest_score}/100. "
            message += f"You have {green_flags_count} green flags. "
            message += "This conversation is going well. Trust the process."
        elif interest_score >= 50:
            message = f"Interest score is {interest_score}/100 - this is neutral territory. "
            message += "Don't read into every detail. Give it time to develop naturally."
        else:
            message = f"Interest score is {interest_score}/100. "
            if red_flags_count > 0:
                message += f"There are {red_flags_count} red flags to consider. "
            message += "It's okay to move on if this isn't working. Your time is valuable."
        
        # Add attachment-specific advice
        attachment_style = user_preferences.get("attachment_style", "secure")
        if attachment_style == "anxious":
            message += " Remember: Your anxiety is not always accurate. Focus on the evidence."
        
        return {
            "message": message,
            "interest_score": interest_score,
            "recommendation": "continue" if interest_score >= 50 else "reconsider"
        }
    
    @staticmethod
    async def get_coaching_advice(analysis: Analysis) -> Dict[str, Any]:
        """Get personalized coaching advice"""
        
        advice = {
            "primary_advice": analysis.wingman_notes,
            "action_items": [],
            "warnings": []
        }
        
        # Add action items based on analysis
        if analysis.interest_score >= 70:
            advice["action_items"].append("Send one of the suggested replies within 30 minutes")
            advice["action_items"].append("Don't overthink - the conversation is healthy")
        
        if len(analysis.red_flags) > 0:
            high_severity = [f for f in analysis.red_flags if f.severity == "high"]
            if high_severity:
                advice["warnings"].append("Multiple high-severity red flags detected")
        
        # Power dynamics advice
        if analysis.power_dynamics.effort_asymmetry < -0.3:
            advice["action_items"].append("You're putting in more effort - consider matching their energy")
        elif analysis.power_dynamics.effort_asymmetry > 0.3:
            advice["action_items"].append("They're putting in more effort - show more engagement")
        
        return advice
    
    @staticmethod
    def format_quick_stats(analysis: Analysis) -> Dict[str, Any]:
        """Format quick stats for UI display"""
        health_score = AnalysisEngine.calculate_conversation_health(analysis)
        
        return {
            "interest_score": analysis.interest_score,
            "health_score": round(health_score, 1),
            "red_flags_count": len(analysis.red_flags),
            "green_flags_count": len(analysis.green_flags),
            "suggested_replies_count": len(analysis.suggested_replies),
            "engagement_level": analysis.vibe_report.engagement_level,
            "overall_mood": analysis.vibe_report.overall_mood
        }

