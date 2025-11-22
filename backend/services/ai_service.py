"""AI Service for OpenAI GPT-4o Vision and Claude integration"""

import json
import base64
import re
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from config import settings
from utils.prompts import get_contextual_prompt

logger = logging.getLogger(__name__)


class AIService:
    """Handle AI API calls"""
    
    def __init__(self):
        self.openai_client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url
        )
        self.model = settings.openai_model
    
    async def analyze_screenshot(
        self,
        image_bytes: bytes,
        user_preferences: Optional[Dict[str, Any]] = None,
        conversation_stage: Optional[str] = None,
        osint_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze screenshot using GPT-4o Vision"""
        
        # Encode image to base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Get contextual prompt
        prompt = get_contextual_prompt(user_preferences, conversation_stage)
        
        # Add OSINT context if available
        if osint_context:
            osint_summary = "\n=== OSINT BACKGROUND CHECK ===\n"
            if osint_context.get("found_accounts"):
                osint_summary += f"Target Username: {osint_context.get('username')}\n"
                osint_summary += "Found Profiles (with content summary):\n"
                for acc in osint_context['found_accounts']:
                    osint_summary += f"- {acc['site']}: {acc['url']}\n"
                    if acc.get('page_summary'):
                        osint_summary += f"  Content Preview: {acc['page_summary']}\n"
                
                osint_summary += "\nINSTRUCTIONS FOR OSINT INTEGRATION:\n"
                osint_summary += "1. Cross-reference the conversation with these found profiles.\n"
                osint_summary += "2. Detect inconsistencies (e.g., lying about job, location, interests).\n"
                osint_summary += "3. Use profile content to suggest deeper conversation topics.\n"
                osint_summary += "4. Assess 'Catfish' risk if profile data mismatches the conversation.\n"
            else:
                osint_summary += f"No public profiles found for username '{osint_context.get('username')}'. This might suggest a fake profile or privacy-conscious user.\n"
            
            prompt += "\n" + osint_summary
        
        logger.info(f"Sending request to OpenAI model: {self.model}")
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Analyze this screenshot of a text conversation. Provide your analysis in the exact JSON format specified."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            # Extract response content
            content = response.choices[0].message.content
            logger.info("Received response from OpenAI")
            logger.debug(f"Raw content: {content[:100]}...")
            
            # Try to parse JSON from response
            # Sometimes GPT returns markdown code blocks
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            # Parse JSON
            try:
                analysis = json.loads(content)
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract JSON from text
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                else:
                    logger.error(f"Failed to parse JSON. Content: {content}")
                    raise ValueError("Could not parse JSON from AI response")
            
            # Store raw response for debugging
            analysis["raw_ai_response"] = content
            
            return analysis
            
        except Exception as e:
            logger.error(f"AI analysis failed: {str(e)}")
            raise Exception(f"AI analysis failed: {str(e)}")

    async def extract_metadata(self, image_bytes: bytes) -> Dict[str, Any]:
        """Extract comprehensive profile information from image for OSINT"""
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        prompt = """Analyze this screenshot for any identifying information about the other person (the participant).
        Extract the following fields if visible or inferred from context:
        
        1. Platform Name (e.g., iMessage, Tinder, Instagram)
        2. Participant Name (Display Name)
        3. Username/Handle (starts with @ or url)
        4. Age (if visible)
        5. Location/City
        6. Job/Occupation
        7. School/University
        8. Phone Number (if visible)
        9. Email (if visible)
        10. Interests/Keywords (list of 3-5 topics mentioned)
        
        Return valid JSON only. Use "Unknown" or null for missing fields.
        Structure:
        {
            "platform": "...",
            "participant_name": "...",
            "username": "...",
            "age": "...",
            "location": "...",
            "occupation": "...",
            "education": "...",
            "contact": { "phone": "...", "email": "..." },
            "interests": ["...", "..."]
        }"""

        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}}
                    ]}
                ],
                max_tokens=300
            )
            content = response.choices[0].message.content.strip()
            if content.startswith("```json"): 
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            return json.loads(content.strip())
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            return {"platform": "Unknown", "participant_name": "Unknown", "error": str(e)}

    async def generate_reply_suggestions(
        self,
        conversation_context: str,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> list:
        """Generate reply suggestions based on conversation context"""
        
        # Build preference context
        pref_context = ""
        if user_preferences:
            style = user_preferences.get('communication_style', 'direct')
            goal = user_preferences.get('dating_goal', 'serious')
            
            pref_context = f"""
USER PREFERENCES:
- Communication Style: {style}
- Dating Goal: {goal}
Please tailor the replies to match this style and goal.
"""

        prompt = f"""Based on this conversation context, suggest 3 reply options:

{conversation_context}

{pref_context}

Provide 3 reply suggestions in JSON format:
{{
  "suggestions": [
    {{
      "text": "reply text here",
      "tone": "enthusiastic/playful/mysterious/direct",
      "success_probability": 0.75,
      "risk_level": "low/medium/high",
      "rationale": "why this works"
    }}
  ]
}}"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a dating coach helping craft perfect text replies."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.8
            )
            
            content = response.choices[0].message.content
            # Parse JSON (similar to analyze_screenshot)
            content = content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            result = json.loads(content.strip())
            return result.get("suggestions", [])
            
        except Exception as e:
            raise Exception(f"Reply generation failed: {str(e)}")

