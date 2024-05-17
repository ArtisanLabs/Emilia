const { createClient } = global.get('supabase');

// Set up Supabase client
const supabaseUrl = "https://api.supabase.emilia.artisanlabs.io";
const supabaseKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ewogICJyb2xlIjogImFub24iLAogICJpc3MiOiAic3VwYWJhc2UiLAogICJpYXQiOiAxNzE1NjYyODAwLAogICJleHAiOiAxODczNDI5MjAwCn0.LgYqHvU4k3Bp5iqmFhKY8YF6jaynYMlM5RDW3zg9E0U";
const supabase = createClient(supabaseUrl, supabaseKey, { db: { schema: 'emilia' } });

/**
 * Asynchronous function to get the current chatId and redbot_user_id for the user.
 * This function takes the user ID from msg.payload and retrieves the chatId and redbot_user_id from the 'user_current_chat' table.
 * 
 * @param {object} msg - The message object from Node-RED.
 * @returns {Promise<{chat_id: string, redbot_user_id: string}>} - A promise that resolves to an object containing the chatId and redbot_user_id.
 * @throws {Error} - Throws an error if the operation fails.
 */
async function getChatIdAndRedbotUserId(msg) {
    // Extract userId from msg
    const userId = msg.user_data.user_id;

    // Retrieve the chatId and redbot_user_id for the user
    const { data, error: selectError } = await supabase
        .from('user_current_chat')
        .select('chat_id, redbot_user_id')
        .eq('user_id', userId)
        .single();

    // If there is an error retrieving the record, throw an error
    if (selectError) {
        throw new Error(selectError.message);
    }

    // Return the chatId and redbot_user_id
    return { chat_id: data.chat_id, redbot_user_id: data.redbot_user_id };
}

try {
    // Get the chat ID and redbot_user_id using the user ID
    const { chat_id, redbot_user_id } = await getChatIdAndRedbotUserId(msg);

    // Store the chat ID and redbot_user_id in msg.user_data
    msg.user_data.flowise_chat_id = chat_id;
    msg.user_data.redbot_user_id = redbot_user_id;
} catch (error) {
    // Handle any errors by assigning the error message to msg.payload
    msg.payload = { error: error.message };
}

/*
 * Return the message with the user ID or error.
 */
return msg;