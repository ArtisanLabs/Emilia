import pytest
from datetime import datetime
from dotenv import load_dotenv
from miabot.database.supabase import SupabaseDB, SupabaseConfig
from miabot.models.models import TelegramUser, TelegramMessage, PlanningStage
import logging
import os

# Define TEST_USER constant with two user IDs
TEST_USERS = [
    TelegramUser(chat_id=1, first_name="Test User 1", username="testuser1"),
    TelegramUser(chat_id=4503599627370495, first_name="Test User Max", username="testusermax")
]

TEST_MESSAGE = TelegramMessage(
    chat_id=1, 
    text="Test message", 
    message_id=1
)

# Load environment variables from .env file for testing
load_dotenv()

@pytest.fixture
def supabase_db(event_loop):
    """
    Fixture to initialize and return a SupabaseDB instance. This fixture handles loading the Supabase configuration
    from environment variables, initializing the SupabaseDB with the configuration and a logger. It ensures the
    database is initialized before returning the instance for testing.

    The fixture is a generator, which allows for setup before yielding the database instance to the test, and performs
    any necessary cleanup after the test completes. The cleanup involves synchronous calls that are executed in an
    asynchronous event loop to ensure compatibility with async database operations.

    Usage:
        @pytest.mark.asyncio
        async def test_some_db_interaction(supabase_db):
            db_instance = supabase_db
            # Use db_instance for testing
    """
    # Load Supabase configuration from environment variables
    config = SupabaseConfig(url=os.getenv("SUPABASE_URL"), key=os.getenv("SUPABASE_KEY"))
    # Initialize SupabaseDB with real config and a simple logger
    db = SupabaseDB(config=config, log=logging.getLogger("test_logger"))
    # Ensure the database is initialized

    yield db  # Yield the database instance to the test

    # After the test completes, perform cleanup here
    # Since the cleanup function is async, use the event loop to run it synchronously
    # event_loop.run_until_complete(db.delete_all_test_users_and_messages(TEST_USERS))

@pytest.mark.asyncio
async def test_get_postgres_version_real_db(supabase_db):
    """
    Test to verify that the get_postgres_version method of the SupabaseDB class
    correctly retrieves the PostgreSQL version from the database.
    
    This test relies on the supabase_db fixture for setup. It uses an actual
    database connection as specified by the environment variables to ensure
    that the get_postgres_version method functions as expected.
    
    The test demonstrates how to use a fixture that yields a database
    instance for interaction within an asynchronous test.
    """
    db = supabase_db
    await db.initialize_database()
    # Call the method under test
    version = await db.get_postgres_version()
    # Assert the expected outcome
    assert "PostgreSQL" in version


@pytest.mark.asyncio
async def test_upsert_telegram_user(supabase_db):
    """
    Test to verify that the upsert_telegram_user method of the SupabaseDB class
    correctly upserts a Telegram user into the database.
    """
    db = supabase_db
    await db.initialize_database()
    for test_user in TEST_USERS:
        # Upsert the test user into the database
        api_response = await supabase_db.upsert_telegram_user(test_user)
        # Assert that the upsert operation was successful
        # Since APIResponse doesn't have a status_code, we check if data is not None as an indication of success
        assert api_response.data is not None, f"Failed to upsert user with id: {test_user.chat_id}"
        # Additionally, verify that the upserted user data is present in the response
        assert len(api_response.data) > 0, "No data found for the upserted user."

@pytest.mark.asyncio
async def test_store_telegram_message(supabase_db):
    """
    Test to verify that the store_telegram_message method of the SupabaseDB class
    correctly stores a Telegram message into the database.
    """
    db = supabase_db
    await db.initialize_database()
    # Use the predefined TEST_MESSAGE and define a test emoji and stage
    test_emoji = "🚀"
    test_stage = "onboarding-start"

    # Store the TEST_MESSAGE in the database
    store_response = await db.store_telegram_message(TEST_MESSAGE, test_emoji, test_stage)
    # Assert that the store operation was successful
    assert store_response.data is not None, "Failed to store message."
    assert len(store_response.data) > 0, "No data found for the stored message."

    # Attempt to update the same message
    update_response = await db.store_telegram_message(TEST_MESSAGE, test_emoji, test_stage)
    # Assert that the update operation was successful and returned data
    assert update_response.data is not None, "Failed to update message."
    assert len(update_response.data) > 0, "No data found for the updated message."

@pytest.mark.asyncio
async def test_store_telegram_message_existing_record(supabase_db):
    """
    Test to verify that the store_telegram_message method correctly updates an existing record
    in the database when a message with the same chat_id, text, and emoji already exists.
    """
    db = supabase_db
    await db.initialize_database()
    # Use the predefined TEST_MESSAGE and define a test emoji and stage
    test_emoji = "🚀"
    test_stage = "onboarding-start"

    # Initially store the TEST_MESSAGE in the database
    initial_store_response = await db.store_telegram_message(TEST_MESSAGE, test_emoji, test_stage)
    assert initial_store_response.data is not None, "Failed to initially store message."
    assert len(initial_store_response.data) > 0, "No data found for the initially stored message."

    # Attempt to store the same message again, expecting it to update the existing record
    update_response = await db.store_telegram_message(TEST_MESSAGE, test_emoji, test_stage)
    assert update_response.data is not None, "Failed to update existing message."
    assert len(update_response.data) > 0, "No data found for the updated message."

    # Verify that the update operation did not create a new record but updated the existing one
    # This can be done by checking the count of records matching the message criteria
    records_response = await db.client.table("user_stored_messages")\
        .select("*")\
        .eq("chat_id", TEST_MESSAGE.chat_id)\
        .eq("messages", TEST_MESSAGE.text)\
        .eq("emoji", test_emoji)\
        .execute()

    assert len(records_response.data) == 1, "More than one record found for the message, indicating a new record was created instead of updating."

@pytest.mark.asyncio
async def test_get_stored_messages_by_planning_stage(supabase_db):
    """
    Test to verify that the get_stored_messages_by_planning_stage method of the SupabaseDB class
    correctly retrieves stored messages by planning stage for a given user and does not retrieve
    messages for other users.
    """
    db = supabase_db
    await db.initialize_database()
    # Define test messages for both users with distinct stages
    test_message_user_1 = TelegramMessage(
        chat_id=1, 
        text="Test message for user 1", 
        message_id=2
    )
    test_message_user_max = TelegramMessage(
        chat_id=4503599627370495, 
        text="Test message for user max", 
        message_id=3
    )
    test_stage_user_1 = "onboarding-start"
    test_stage_user_max = "onboarding-start"

    # Store messages for both users
    await db.store_telegram_message(test_message_user_1, "🚀", test_stage_user_1)
    await db.store_telegram_message(test_message_user_max, "🌟", test_stage_user_max)

    # Retrieve stored messages by planning stage for user 1
    stored_messages_user_1 = await db.get_stored_messages_by_planning_stage(test_message_user_1.chat_id)

    # Assert that the retrieved messages for user 1 contain the expected stage and message
    assert test_stage_user_1 in stored_messages_user_1, "Test stage not found in the retrieved messages for user 1."
    assert "Test message for user 1" in stored_messages_user_1[test_stage_user_1], "Test message not found in the retrieved messages for user 1."

    # Assert that messages for user max are not retrieved for user 1
    assert "Test message for user max" not in stored_messages_user_1.get(test_stage_user_max, ""), "User max's message was incorrectly retrieved for user 1."

    # Cleanup: Delete the test messages to maintain test environment integrity
    await db.delete_all_test_users_and_messages(TEST_USERS)



@pytest.mark.asyncio
async def test_create_planning_stages_for_user(supabase_db):
    """
    Test to verify that the create_planning_stages_for_user method of the SupabaseDB class
    correctly creates planning stage records for a new user.
    """
    db = supabase_db
    await db.initialize_database()

    # Define a test user
    test_user = TelegramUser(
        chat_id=TEST_USERS[0].chat_id,
        first_name=TEST_USERS[0].first_name,
        last_name=TEST_USERS[0].last_name
    )

    # Insert the test user into the database
    await db.upsert_telegram_user(test_user)
    
    # Call the method under test
    await db.create_planning_stages_for_user(TEST_USERS[0].chat_id)
    # Assert the expected outcome
    response = await db.client.table("onboarding_planning_stages").select("*").eq("chat_id", TEST_USERS[0].chat_id).execute()
    assert len(response.data) == 7, "Planning stages for user not created correctly."

@pytest.mark.asyncio
async def test_start_onboarding_stage(supabase_db):
    """
    Test to verify that the start_onboarding_stage method of the SupabaseDB class
    correctly marks a specific onboarding stage as started for a given user.
    """
    db = supabase_db
    await db.initialize_database()
    # Call the method under test
    response = await db.start_onboarding_stage(TEST_USERS[0].chat_id, "onboarding-start")
    # Assert the expected outcome
    assert response.data is not None, "Failed to start onboarding stage."
    assert response.data[0]["started_at"] is not None, "Onboarding stage not started."

@pytest.mark.asyncio
async def test_complete_onboarding_stage(supabase_db):
    """
    Test to verify that the complete_onboarding_stage method of the SupabaseDB class
    correctly marks a specific onboarding stage as completed for a given user.
    """
    db = supabase_db
    await db.initialize_database()
    # Call the method under test
    response = await db.complete_onboarding_stage(TEST_USERS[0].chat_id, "onboarding-start")
    # Assert the expected outcome
    assert response.data is not None, "Failed to complete onboarding stage."
    assert isinstance(datetime.fromisoformat(response.data[0]["completed_at"]), datetime), "Onboarding stage not completed."

@pytest.mark.asyncio
async def test_get_existing_telegram_user(supabase_db):
    """
    Test to verify that the get_telegram_user method of the SupabaseDB class
    correctly fetches an existing user from the database.
    """
    db = supabase_db
    await db.initialize_database()
    # Call the method under test
    user = await db.get_telegram_user(TEST_USERS[0].chat_id)
    # Assert the expected outcome
    assert user is not None, "Failed to fetch user."
    assert user.chat_id == TEST_USERS[0].chat_id, "Fetched user does not match expected user."

@pytest.mark.asyncio
async def test_get_non_existent_telegram_user(supabase_db):
    """
    Test to verify that the get_telegram_user method of the SupabaseDB class
    returns None when trying to fetch a non-existent user from the database.
    """
    db = supabase_db
    await db.initialize_database()
    # Call the method under test with a non-existent user id
    non_existent_user = await db.get_telegram_user(999999)  # Assuming 999999 is not a valid chat_id
    # Assert the expected outcome
    assert non_existent_user is None, "Non-existent user was incorrectly fetched."

@pytest.mark.asyncio
async def test_get_onboarding_status(supabase_db):
    """
    Test to verify that the get_onboarding_status method of the SupabaseDB class
    correctly fetches the onboarding status for a given user.
    """
    db = supabase_db
    await db.initialize_database()
    # Call the method under test
    onboarding_status = await db.get_onboarding_status(TEST_USERS[0].chat_id)
    # Assert the expected outcome
    assert onboarding_status is not None, "Failed to fetch onboarding status."
    # Exclude 'test' and 'unknown' stages
    valid_stages = [stage for stage in PlanningStage if stage.value not in ['test', 'unknown']]
    assert all(stage in onboarding_status for stage in valid_stages), "Onboarding status does not contain all valid stages."

@pytest.mark.asyncio
async def test_get_current_onboarding_stage(supabase_db):
    """
    Test to verify that the get_current_onboarding_stage method of the SupabaseDB class
    correctly fetches the current onboarding stage for a given user.
    """
    db = supabase_db
    await db.initialize_database()
    # Call the method under test
    current_stage = await db.get_current_onboarding_stage(TEST_USERS[0].chat_id)
    # Assert the expected outcome
    assert current_stage is not None, "Failed to fetch current onboarding stage."
    # Convert the current_stage to PlanningStage enum before checking if it's valid
    assert PlanningStage(current_stage) in PlanningStage, "Fetched stage is not a valid PlanningStage."

@pytest.mark.asyncio
async def test_delete_all_test_users_and_messages(supabase_db):
    """
    Test to verify that the delete_all_test_users_and_messages method of the SupabaseDB class
    correctly deletes all test users and their stored messages from the database.
    """
    db = supabase_db
    await db.initialize_database()
    # Call the method under test
    await db.delete_all_test_users_and_messages(TEST_USERS)
    # Assert the expected outcome
    for test_user in TEST_USERS:
        user = await db.get_telegram_user(test_user.chat_id)
        assert user is None, "Failed to delete user."
