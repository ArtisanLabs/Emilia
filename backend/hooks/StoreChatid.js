const { createClient } = global.get('supabase');

// Set up Supabase client
const supabaseUrl = "https://api.supabase.emilia.artisanlabs.io";
const supabaseKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ewogICJyb2xlIjogImFub24iLAogICJpc3MiOiAic3VwYWJhc2UiLAogICJpYXQiOiAxNzE1NjYyODAwLAogICJleHAiOiAxODczNDI5MjAwCn0.LgYqHvU4k3Bp5iqmFhKY8YF6jaynYMlM5RDW3zg9E0U";
const supabase = createClient(supabaseUrl, supabaseKey, { db: { schema: 'emilia' } });

/**
 * Node-RED function to store the current chatId for the user.
 * This function takes the user ID and chatId from msg.payload and stores them in the 'user_current_chat' table.
 * If the user already has a chatId stored, it updates the existing record with the new chatId.
 * 
 * @param {object} msg - The message object from Node-RED.
 * @returns {Promise<void>} - A promise that resolves when the operation is complete.
 * @throws {Error} - Throws an error if the operation fails.
 */
async function storeChatIdUpsert(msg) {
    // Extract userId and chatId from msg
    const userId = msg.user_data.user_id;
    const chatId = msg.payload.chatId;

    // Upsert the chatId for the user
    const { error: upsertError } = await supabase
        .from('user_current_chat')
        .upsert({ user_id: userId, chat_id: chatId, updated_at: new Date() }, { onConflict: ['user_id'] });

    // If there is an error upserting the record, throw an error
    if (upsertError) {
        throw new Error(upsertError.message);
    }
}

await storeChatIdUpsert(msg);
