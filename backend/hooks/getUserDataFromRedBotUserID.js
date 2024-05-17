const { createClient } = global.get('supabase');

// Set up Supabase client
const supabaseUrl = "https://api.supabase.emilia.artisanlabs.io";
const supabaseKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ewogICJyb2xlIjogImFub24iLAogICJpc3MiOiAic3VwYWJhc2UiLAogICJpYXQiOiAxNzE1NjYyODAwLAogICJleHAiOiAxODczNDI5MjAwCn0.LgYqHvU4k3Bp5iqmFhKY8YF6jaynYMlM5RDW3zg9E0U";
const supabase = createClient(supabaseUrl, supabaseKey, { db: { schema: 'emilia' } });

/**
 * Asynchronous function to get the user data from RedBot user ID.
 * This function takes the user ID from msg.payload and retrieves the chatId and redbot_user_id from the 'user_current_chat' table.
 * 
 * @param {object} msg - The message object from Node-RED.
 * @returns {Promise<[object, {emilia_user: boolean}]>} - A promise that resolves to an array containing the message object and an object with emilia_user set to true if user data exists, or false if it does not.
 * @throws {Error} - Throws an error if the operation fails.
 */
async function getUserDataFromRedBotUserID(msg) {
    // Extract userId from msg.payload
    const userId = msg.payload.userId;

    // Retrieve the chatId and redbot_user_id for the user
    const { data, error: selectError } = await supabase
        .from('user_current_chat')
        .select('chat_id, user_id')
        .eq('redbot_user_id', userId)
        .single();

    // If there is an error retrieving the record, return [msg, {emilia_user: false}]
    if (selectError) {
        return [msg, { emilia_user: false }];
    }

    // Store the chat ID, user ID, and redbot_user_id in msg.user_data
    msg.user_data = {
        flowise_chat_id: data.chat_id,
        user_id: data.user_id,
        redbot_user_id: userId
    };

    // Return [msg, {emilia_user: true}] if user data exists
    return [msg, { emilia_user: true }];
}


/**
 * Asynchronous function to get the lead data using user_id.
 * This function takes the user ID from msg.user_data and retrieves the lead data from the 'leads' table.
 * 
 * @param {object} msg - The message object from Node-RED.
 * @returns {Promise<void>} - A promise that resolves when the operation is complete.
 * @throws {Error} - Throws an error if the operation fails.
 */
async function getLeadDataFromUserId(msg) {
    // Extract userId from msg.user_data
    const userId = msg.user_data.user_id;

    // Retrieve the lead data for the user
    const { data, error: selectError } = await supabase
        .from('leads')
        .select('*')
        .eq('user_id', userId);

    // If there is an error retrieving the record, throw an error
    if (selectError) {
        throw new Error(selectError.message);
    }

    // Store the lead data in msg.user_lead_data
    msg.user_lead_data = data;
}


/**
 * Call the getUserDataFromRedBotUserID function and handle the response.
 * If the user exists, fill lead data and return [msg, null].
 * If the user does not exist, return [null, msg].
 */
try {
    // Call the getUserDataFromRedBotUserID function
    const [updatedMsg, userStatus] = await getUserDataFromRedBotUserID(msg);

    // Check if the user exists
    if (userStatus.emilia_user) {
        // If the user exists, call the getLeadDataFromUserId function to fill lead data
        await getLeadDataFromUserId(updatedMsg);
        // Return [msg, null]
        return [updatedMsg, null];
    } else {
        // If the user does not exist, return [null, msg]
        return [null, updatedMsg];
    }
} catch (error) {
    // Handle any errors by assigning the error message to msg.payload
    msg.payload = { error: error.message };
    // Return [null, msg] in case of an error
    return [null, msg];
}

