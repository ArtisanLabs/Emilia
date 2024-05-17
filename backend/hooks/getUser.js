const { createClient } = global.get('supabase');

// Set up Supabase client
const supabaseUrl = "https://api.supabase.emilia.artisanlabs.io";
const supabaseKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ewogICJyb2xlIjogImFub24iLAogICJpc3MiOiAic3VwYWJhc2UiLAogICJpYXQiOiAxNzE1NjYyODAwLAogICJleHAiOiAxODczNDI5MjAwCn0.LgYqHvU4k3Bp5iqmFhKY8YF6jaynYMlM5RDW3zg9E0U";
const supabase = createClient(supabaseUrl, supabaseKey, { db: { schema: 'emilia' } });

/**
 * Function to get a user ID by lead ID. If the lead exists, it will return the associated user ID.
 * If the lead does not exist, it will throw an error.
 * @param {string} leadId - The ID of the lead.
 * @returns {Promise<{id: string}>} - A promise that resolves to an object containing the user ID.
 * @throws {Error} - Throws an error if the operation fails.
 */
async function getUserIdByLeadId(leadId) {
    // Check if the lead exists and get the associated user ID
    const { data: leadData, error: fetchError } = await supabase
        .from('leads')
        .select('user_id')
        .eq('lead_id', leadId)
        .single();

    // If there is an error or no lead found, throw an error
    if (fetchError) {
        throw new Error(fetchError.message);
    }

    // Return the user ID
    return { id: leadData.user_id };
}

const leadPayload = msg.payload;
const leadId = leadPayload["Lead ID"];

try {
    // Get the user ID by lead ID
    const { id: userId } = await getUserIdByLeadId(leadId);

    // Assign the user ID to msg.user_data
    msg.user_data = { user_id: userId };
} catch (error) {
    // Handle any errors by assigning the error message to msg.payload
    msg.payload = { error: error.message };
}

/*
 * Return the message with the user ID or error.
 */
return msg;
