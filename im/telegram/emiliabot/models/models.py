from pydantic import BaseModel
from typing import Optional
from enum import Enum
from datetime import datetime

class PlanningStage(str, Enum):
    onboarding_start = 'onboarding-start'
    long_term_goals = 'long-term-goals'
    trimester_goals = 'trimester-goals'
    monthly_goals = 'monthly-goals'
    daily_habits = 'daily-habits'
    next_week_plan = 'next-week-plan'
    next_day_plan = 'next-day-plan'
    unknown = 'unknown'
    test = 'test'

class Voice(BaseModel):
  id: Optional[str] = None # Optional id for the voice
  name: Optional[str] = None # Optional name for the voice
  description: Optional[str] = None # Optional description for the voice

# Define a OnboardingStatus model with all stages of onboarding and boolean fields
class OnboardingStatus(BaseModel):
    """
    # DEPRECATED
    The OnboardingStatus model represents the onboarding status of a user.
    Each field corresponds to a stage in the onboarding process and is a boolean
    indicating whether the user has completed that stage.
    """
    onboarding_start: Optional[bool] = False  # Onboarding start status
    long_term_goals: Optional[bool] = False  # Long-term goals set status
    trimester_goals: Optional[bool] = False  # Trimester goals set status
    daily_habits: Optional[bool] = False  # Daily habits established status
    monthly_goals: Optional[bool] = False  # Monthly goals set status
    next_week_plan: Optional[bool] = False  # Next week plan set status
    next_day_plan: Optional[bool] = False  # Next day plan set status

# Define a Chat model with voices, current_voice, current_conversation and onboarding_status fields
class Chat(BaseModel):
    """
    The Chat model represents a chat session. It includes the current conversation,
    the current planning stage, and the onboarding status of the user.
    """
    current_conversation: Optional[bytes] = None  # Current conversation as a pickled object
    planning_stage: Optional[PlanningStage] = None  # Current planning stage
    onboarding_status: Optional[OnboardingStatus] = None  # Onboarding status

class TelegramUser(BaseModel):
    """
    Define a TelegramUser model to store user data in the database.
    This model includes fields for the user's first name, id, bot status,
    language code, last name, and username.
    """
    chat_id: Optional[int] = None  # Unique identifier for this user or bot
    first_name: Optional[str] = None  # User's first name
    last_name: Optional[str] = None  # User’s or bot’s last name
    username: Optional[str] = None  # User’s or bot’s username
    is_bot: Optional[bool] = False  # True, if this user is a bot
    language_code: Optional[str] = None  # IETF language tag of the user’s language


class UserStoredMessages(BaseModel):
    """
    Define a UserStoredMessages model to store user messages in the database.
    This model includes fields for the user's id, and a list of messages.
    """
    uuid: Optional[str] = None  # Unique identifier for this message
    user_id: Optional[int] = None  # Unique identifier for this user
    messages: Optional[str] = None  # Sotred messages
    emoji: Optional[str] = None  # Reaction emoji to the user's message
    stage: Optional[PlanningStage] = None

class TelegramMessage(BaseModel):
    """
    Define a TelegramMessage model to store user messages in the database.
    This model includes fields for the message's id, text, date, chat id, and user id.
    """
    message_id: Optional[int] = None  # Unique identifier for this message
    text: Optional[str] = None  # Text of the message
    date: Optional[datetime] = None  # Date and time when the message was sent
    chat_id: Optional[int] = None  # Unique identifier for the chat where the message was sent
    user_id: Optional[int] = None  # Unique identifier for the user who sent the message