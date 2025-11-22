"""Data validation utilities"""

from typing import Optional
import re


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_interest_score(score: int) -> bool:
    """Validate interest score is between 0-100"""
    return 0 <= score <= 100


def validate_attachment_style(style: str) -> bool:
    """Validate attachment style"""
    return style in ["secure", "anxious", "avoidant"]


def validate_dating_goal(goal: str) -> bool:
    """Validate dating goal"""
    return goal in ["casual", "serious", "exploring"]

