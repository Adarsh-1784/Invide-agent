import { ResilientLLM, ProviderRegistry } from 'resilient-llm';
import dotenv from 'dotenv';
dotenv.config({ path: '.env.local' });

ProviderRegistry.configure('coralbricks', {
    baseUrl: process.env.CORAL_BRICKS_BASE_URL || 'https://inference.coralbricks.ai/v1',
    type: 'openai-compatible', // Instructs resilient-llm to use OpenAI format
    apiKey: process.env.CORAL_BRICKS_API_KEY || 'cb_XUvfFDd2GjOR9jzYG5a6TPvuEXG9K.....'
});

const apiKey = process.env.CORAL_BRICKS_API_KEY || 'cb_XUvfFDd2GjOR9jzYG5a6TPvuEXG9K.....';

const llm = new ResilientLLM({
    aiService: 'coralbricks',
    model: 'deepseek-v4.1-flash-fast',
    apiKey: apiKey,
    maxTokens: 2048,
    temperature: 0.7,
    retries: 0,
});

async function main() {
    try {
        console.log("Sending ping to Coral Bricks...");
        const response = await llm.chat([{ role: "user", content: "Ping" }]);
        console.log("Response:", response);
    } catch (err) {
        console.error("DEBUG ERROR STACK:");
        console.error(err);
    }
}

main();
