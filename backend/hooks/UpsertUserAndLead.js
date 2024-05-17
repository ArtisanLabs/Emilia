const { createClient } = global.get('supabase');

// Set up Supabase client
const supabaseUrl = "https://api.supabase.emilia.artisanlabs.io";
const supabaseKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ewogICJyb2xlIjogImFub24iLAogICJpc3MiOiAic3VwYWJhc2UiLAogICJpYXQiOiAxNzE1NjYyODAwLAogICJleHAiOiAxODczNDI5MjAwCn0.LgYqHvU4k3Bp5iqmFhKY8YF6jaynYMlM5RDW3zg9E0U";
const supabase = createClient(supabaseUrl, supabaseKey, { db: { schema: 'emilia' } });

/**
 * Function to get or create a user by email. If the user already exists, it will return the user ID.
 * If the user is new, it will create the user, set the state in sales_pipeline_states as 'ad_potential_lead',
 * and return the user ID along with a flag indicating the user is new.
 * @param {string} email - The email of the user.
 * @param {string} name - The name of the user.
 * @returns {Promise<{id: string, new: boolean}>} - A promise that resolves to an object containing the user ID and a flag indicating if the user is new.
 * @throws {Error} - Throws an error if the operation fails.
 */
async function getOrCreateUser(email, name) {
    // Check if the user already exists
    const { data: existingUser, error: fetchError } = await supabase
        .from('users')
        .select('id')
        .eq('email', email)
        .single();

    // If there is an error other than "No rows found", throw an error
    if (fetchError && fetchError.code !== 'PGRST116') { // PGRST116: No rows found
        throw new Error(fetchError.message);
    }

    // If user exists, return the user ID and new flag as false
    if (existingUser) {
        return { id: existingUser.id, is_new: false };
    }

    // If user does not exist, create the user
    const { data: newUserData, error: newUserError } = await supabase
        .from('users')
        .insert({ email: email, name: name })
        .select()
        .single();

    // If there is an error creating the user, throw an error
    if (newUserError) {
        throw new Error(newUserError.message);
    }

    // Set the state in sales_pipeline_states as 'ad_potential_lead' for the new user
    const { error: stateError } = await supabase
        .from('sales_pipeline_states')
        .insert({ user_id: newUserData.id, name: 'ad_potential_lead' });

    // If there is an error setting the state, throw an error
    if (stateError) {
        throw new Error(stateError.message);
    }

    // Return the new user ID and new flag as true
    return { id: newUserData.id, is_new: true };
}

async function upsertLead(lead) {
    const { data, error } = await supabase
        .from('leads')
        .upsert(lead, { onConflict: ['lead_id'] });

    if (error) {
        throw new Error(error.message);
    }

    return data;
}


const leadPayload = msg.payload;
const email = leadPayload["Field data"]["Work email"];
const full_name = leadPayload["Field data"]["Full name"];

const { id: userId, is_new: is_new } = await getOrCreateUser(email, full_name);

const lead = {
    lead_id: leadPayload["Lead ID"],
    user_id: userId,
    field_data: leadPayload["Field data"],
    date_created: leadPayload["Date created"],
    ad_id: leadPayload["Ad ID"] || '000000000000000000',
    form_id: leadPayload["Form ID"] || '000000000000000',
    page_id: leadPayload["Page ID"] || '000000000000000',
    ad_group_id: leadPayload["Ad group ID"] || '000000000000000000'
};

try {
    // Upsert the lead and select the single row
    const { data, error } = await supabase
        .from('leads')
        .upsert(lead, { onConflict: ['lead_id'] })
        .select()
        .single();

    // Check for errors
    if (error) {
        throw new Error(error.message);
    }

    // Assign the data to msg.payload
    msg.payload = data;
    // node.send(msg);
} catch (error) {
    // Handle any errors by assigning the error message to msg.payload
    msg.payload = { error: error.message };
    // node.send(msg);
}


/*
 * Check if the user is new and return the message accordingly.
 * If the user is new, send the message to the second output.
 * Otherwise, send the message to the first output.
 */
if (is_new) {
    // If the user is new, send the message to the second output
    return [null, msg];
} else {
    // If the user is not new, send the message to the first output
    return [msg, null];
}
