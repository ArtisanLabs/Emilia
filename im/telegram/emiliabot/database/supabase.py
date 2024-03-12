# Import the AsyncClient from supabase instead of the synchronous Client
import asyncio
import logging

from datetime import datetime
from abc import ABC, abstractmethod
from supabase._async.client import create_client, AsyncClient
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from postgrest.base_request_builder import APIResponse

from emiliabot.models.models import TelegramUser, TelegramMessage, PlanningStage


class SupabaseConfig(BaseModel):
    """
    Define a SupabaseConfig model to store Supabase configuration.
    This model includes fields for the Supabase URL and API key.
    """

    url: Optional[str] = Field(None, env="SUPABASE_URL")  # Supabase URL
    key: Optional[str] = Field(None, env="SUPABASE_KEY")  # Supabase API key


class SupabaseDB(ABC):
    """
    Define a SupabaseDB class to create a Supabase client using the provided configuration.
    """

    def __init__(self, config: SupabaseConfig, log: logging.Logger) -> None:
        # Use the asynchronous client instead of the synchronous one
        self.log = log
        self.config = config
        self.client: AsyncClient = None

    async def initialize_database(self):
        if not self.client:  # Initialize client asynchronously if not already done
            self.client = await create_client(self.config.url, self.config.key)

    async def upsert_telegram_user(self, user: TelegramUser) -> APIResponse:
        """
        Define a method to upsert a Telegram user into the database.
        """
        # Upsert the user into the database and return the API response
        return (
            await self.client.table("telegram_users")
            .upsert(user.model_dump(), on_conflict=["chat_id"])
            .execute()
        )

    async def store_telegram_message(
        self, message: TelegramMessage, emoji: str, planning_stage: str
    ) -> APIResponse:
        """
        This method is used to store a Telegram message into the database.
        It takes a TelegramMessage object as input and inserts it into the
        'user_stored_messages' table in the database. If a message with the
        same id already exists, it updates the existing record.
        """

        # Create a dictionary to store the message
        message_dict = {
            "chat_id": message.chat_id,
            "messages": message.text,
            "emoji": emoji,
            "stage": planning_stage,
            "stored_at": "now()",
        }

        # Check if a record with the same message and emoji already exists
        existing_record = (
            await self.client.table("user_stored_messages")
            .select("*")
            .eq("messages", message.text)
            .eq("emoji", emoji)
            .execute()
        )

        if existing_record.data:
            # If the record exists, update the stored_at
            self.log.info(
                f"Updating existing record for message: {message.text} and emoji: {emoji}"
            )
            response = (
                await self.client.table("user_stored_messages")
                .update({"stored_at": "now()"})
                .eq("messages", message.text)
                .eq("emoji", emoji)
                .execute()
            )
        else:
            # If the record does not exist, insert a new one
            response = (
                await self.client.table("user_stored_messages")
                .insert(message_dict)
                .execute()
            )

        return response

    async def get_stored_messages_by_planning_stage(
        self, chat_id: int
    ) -> Dict[str, str]:
        """
        Retrieves the stored messages from the database for a given user and planning stage.

        This method executes a SQL query to fetch the messages. It then iterates over each planning stage and
        concatenates all stored messages for the given user and planning stage. If no messages are found for a
        particular stage, it assigns "Not defined yet" to that stage.

        Args:
            chat_id (int): The ID of the user for whom to retrieve the messages.

        Returns:
            Dict[str, str]: A dictionary where the keys are the planning stages and the values are the concatenated
            messages for that stage. If no messages are found for a stage, the value is "Not defined yet".
        """
        # Execute SQL query to get stored messages
        response = (
            await self.client.table("user_stored_messages")
            .select("*")
            .eq("chat_id", chat_id)
            .execute()
        )

        """
        The following code block will iterate over each planning stage and 
        concatenate all stored messages for the given user and planning stage.
        If no messages are found for a particular stage, it assigns "Not defined yet" to that stage.
        """

        # Exclude 'test' and 'unknown' stages
        planning_stages = [
            stage.value
            for stage in PlanningStage
            if stage.value not in ["test", "unknown"]
        ]

        # Initialize an empty dictionary to store the messages
        stored_messages_by_stage = {}

        # Iterate over each planning stage
        for stage in planning_stages:
            # Filter the response data by the current planning stage
            # Exclude 'test' and 'unknown' stages
            if stage not in ["test", "unknown"]:
                stage_messages = [msg for msg in response.data if msg["stage"] == stage]

                # Check if there are messages for the current stage
                if stage_messages:
                    # Concatenate the messages and store them in the dictionary
                    stored_messages_by_stage[stage] = "\n\n".join(
                        [msg["messages"] for msg in stage_messages]
                    )
                else:
                    # If no messages are found for the current stage, assign "Not defined yet"
                    stored_messages_by_stage[stage] = "Not defined yet"

        return stored_messages_by_stage

    async def get_postgres_version(self) -> str:
        """
        This method retrieves the PostgreSQL version from the database.
        It executes a SQL query to fetch the version and returns it as a string.
        """
        # Execute SQL query to get PostgreSQL version
        response = await self.client.rpc("get_postgres_version", {}).execute()
        self.log.info(response)
        # Return the version as a string
        return f"PostgreSQL version: {response}"

    async def delete_all_test_users_and_messages(self, test_users: List[TelegramUser]):
        """
        This method deletes all test users and their stored messages from the database.
        It is intended to be used in testing environments to clean up after tests.
        The method receives a list of TelegramUser objects representing the test users to be deleted.
        """
        # Extract user IDs from the list of TelegramUser objects
        test_chat_ids = [user.chat_id for user in test_users]

        # Execute delete query for each test user ID for both users and their messages
        for chat_id in test_chat_ids:
            await self.client.table("onboarding_planning_stages").delete().eq(
                "chat_id", chat_id
            ).execute()
            await self.client.table("user_stored_messages").delete().eq(
                "chat_id", chat_id
            ).execute()
            await self.client.table("telegram_users").delete().eq(
                "chat_id", chat_id
            ).execute()

    async def create_planning_stages_for_user(self, chat_id: int) -> None:
        """
        This method creates planning stage records for a new user.
        """
        # Get the planning stages from the PlanningStage enum
        planning_stages = [
            stage.value
            for stage in PlanningStage
            if stage.value not in ["test", "unknown"]
        ]
        for stage in planning_stages:
            await self.client.table("onboarding_planning_stages").insert(
                {
                    "chat_id": chat_id,
                    "stage": stage,
                }
            ).execute()

    async def start_onboarding_stage(self, chat_id: int, stage: str) -> APIResponse:
        """
        This method marks a specific onboarding stage as started for a given user.
        The current time is converted to a string format that is JSON serializable.
        """
        # Convert current time to string format
        current_time = datetime.now().isoformat()
        response = (
            await self.client.table("onboarding_planning_stages")
            .update({"started_at": current_time})
            .eq("chat_id", chat_id)
            .eq("stage", stage)
            .execute()
        )
        return response

    async def complete_onboarding_stage(self, chat_id: int, stage: str) -> APIResponse:
        """
        This method marks a specific onboarding stage as completed for a given user.
        The current time is converted to a string format that is JSON serializable.
        """
        # Convert current time to string format
        current_time = datetime.now().isoformat()
        response = (
            await self.client.table("onboarding_planning_stages")
            .update({"completed_at": current_time})
            .eq("chat_id", chat_id)
            .eq("stage", stage)
            .execute()
        )
        return response

    async def get_telegram_user(self, chat_id: int) -> Optional[TelegramUser]:
        """
        This method fetches a user from the database.
        If multiple records are found, only the first one is returned.
        """
        response = (
            await self.client.table("telegram_users")
            .select("*")
            .eq("chat_id", chat_id)
            .limit(1)
            .execute()
        )
        if response.data:
            return TelegramUser(**response.data[0])
        else:
            return None

    async def get_onboarding_status(self, chat_id: int) -> Optional[Dict[str, bool]]:
        """
        This method fetches the onboarding status for a given user.
        The status is determined by checking if the 'completed_at' field is not None.
        If 'completed_at' is not None, the stage is considered completed.
        """
        response = (
            await self.client.table("onboarding_planning_stages")
            .select("*")
            .eq("chat_id", chat_id)
            .execute()
        )
        if response.data:
            onboarding_status = {
                stage["stage"]: stage["completed_at"] is not None
                for stage in response.data
            }
            return onboarding_status
        else:
            return None

    async def get_current_onboarding_stage(self, chat_id: int) -> Optional[str]:
        """
        This method fetches the current onboarding stage for a given user.
        The stage is determined by checking the 'started_at' field. The stage with
        the latest 'started_at' timestamp is considered the current stage.
        """
        # Fetch all records from the "onboarding_planning_stages" table
        # where the "chat_id" matches the given chat_id and "started_at" is not None.
        # The records are ordered in descending order by the "started_at" field.
        # Fetch all records from the "onboarding_planning_stages" table
        # where the "chat_id" matches the given chat_id and "started_at" is not None.
        # The records are ordered in descending order by the "started_at" field.
        # Fetch all records from the "onboarding_planning_stages" table
        # where the "chat_id" matches the given chat_id and "started_at" is not None.
        # The records are ordered in descending order by the "started_at" field.
        response = (
            await self.client.table("onboarding_planning_stages")
            .select("*")
            .eq("chat_id", chat_id)
            .not_.is_("started_at", "null")
            .order("started_at", desc=True)
            .execute()
        )
        # If there are any records, return the "stage" field of the first record.
        # Otherwise, return None.
        if response.data:
            return response.data[0]["stage"]
        else:
            return None
