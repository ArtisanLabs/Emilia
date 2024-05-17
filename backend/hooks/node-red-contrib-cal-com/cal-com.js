/**
 * Function to retrieve the next two days of availability from cal.com
 * @param {string} apiKey - The API key for authentication
 * @param {string} userId - The user ID for which to retrieve availability
 * @returns {Promise<Object>} - A promise that resolves to the availability data
 */
async function getNextTwoDaysAvailability(apiKey, userId) {
    // Define the endpoint URL
    const endpoint = `https://api.cal.com/v1/users/${userId}/availability?days=2`;

    try {
        // Make the API request
        const response = await fetch(endpoint, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${apiKey}`,
                'Content-Type': 'application/json'
            }
        });

        // Check if the response is successful
        if (!response.ok) {
            throw new Error(`Error fetching availability: ${response.statusText}`);
        }

        // Parse the JSON response
        const data = await response.json();
        return data;
    } catch (error) {
        // Log and rethrow the error
        console.error('Error:', error);
        throw error;
    }
}


module.exports = function (RED) {
    function LowerCaseNode(config) {
        RED.nodes.createNode(this, config);
        var node = this;
        node.on('input', function (msg) {
            msg.payload = msg.payload.toLowerCase();
            node.send(msg);
        });
    }
    RED.nodes.registerType("lower-case", LowerCaseNode);
}
