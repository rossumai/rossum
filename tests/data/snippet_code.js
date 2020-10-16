exports.rossum_hook_request_handler = ({
annotation: {
content
}
}) => {
try {
// Values over the threshold trigger a warning message
const TOO_BIG_THRESHOLD = 10;

// List of all datapoints of amount_due schema id
const [amountDueDatapoint] = findBySchemaId(content, "amount_due");

messages = [];
if (amountDueDatapoint.content.value >= TOO_BIG_THRESHOLD) {
    messages.push(createMessage("warning", "Value is too big", amountDueDatapoint.id));
}

// There should be only one datapoint of invoice_id schema id
const [invoiceIdDatapoint] = findBySchemaId(content, "invoice_id");

// "Replace" operation is returned to update the invoice_id value
const operations = [createReplaceOperation(invoiceIdDatapoint, invoiceIdDatapoint.content.value.replace(/-/g, ""))];

// Return messages and operations to be used to update current annotation data
return {
  messages,
  operations
};
} catch (e) {
// In case of exception, create and return error message. This may be useful for debugging.
const messages = [createMessage("error", "Error parsing annotation content")];
return {
  messages
};
}
}

// --- HELPER FUNCTIONS ---

// Return datapoints matching a schema id.
// @param {Object} content - the annotation content tree (see https://api.elis.rossum.ai/docs/#connector-api)
// @param {string} schemaId - the field's ID as defined in the extraction schema(see https://api.elis.rossum.ai/docs/#document-schema)
// @returns {Array} - the list of datapoints matching the schema ID

const findBySchemaId = (content, schemaId) =>
content.reduce((results, dp) =>
dp.schema_id === schemaId ? [...results, dp] :
dp.children ? [...results, ...findBySchemaId(dp.children, schemaId)] :
results, []);

// Create a message which will be shown to the user
// @param {number} datapointId - the id of the datapoint where the message will appear (null for "global" messages).
// @param {String} messageType - the type of the message, any of {info|warning|error}. Errors prevent confirmation in the UI.
// @param {String} messageContent - the message shown to the user
// @returns {Object} - the JSON message definition (see https://api.elis.rossum.ai/docs/#key-messages-optional)

const createMessage = (type, content, datapointId = null) => ({
    content: content,
    type: type,
    id: datapointId,
});

// Replace the value of the datapoint with a new value.
// @param {Object} datapoint - the content of the datapoint
// @param {string} - the new value of the datapoint
// @return {Object} - the JSON replace operation definition (see https://api.elis.rossum.ai/docs/#key-operations-optional)

const createReplaceOperation = (datapoint, newValue) => ({
    op: "replace",
    id: datapoint.id,
    value: {
        content: {
            value: newValue
        }
    }
});