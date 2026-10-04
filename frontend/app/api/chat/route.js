import { NextResponse } from 'next/server';
import { ResilientLLM, ProviderRegistry } from 'resilient-llm';

// Register Coral Bricks as a custom OpenAI-compatible provider
// The user can define CORAL_BRICKS_BASE_URL in their .env
ProviderRegistry.configure('coralbricks', {
    baseUrl: process.env.CORAL_BRICKS_BASE_URL || 'https://api.coralbricks.com/v1',
    type: 'openai-compatible' // Instructs resilient-llm to use OpenAI format
});

const toolsDefinition = [
    {
        type: "function",
        function: {
            name: "execute_sql_query",
            description: "Execute a read-only SQL query to retrieve data about waste logic.",
            parameters: {
                type: "object",
                properties: { query: { type: "string" } },
                required: ["query"]
            }
        }
    },
    {
        type: "function",
        function: {
            name: "generate_chart",
            description: "Generate a chart image from data and return the URL.",
            parameters: {
                type: "object",
                properties: { chart_type: { type: "string" }, title: { type: "string" }, x_label: { type: "string" }, y_label: { type: "string" }, data: { type: "string" } },
                required: ["chart_type", "title", "data"]
            }
        }
    },
    {
        type: "function",
        function: {
            name: "generate_campus_map",
            description: "Generate a Folium interactive HTML map of a campus location.",
            parameters: {
                type: "object",
                properties: { location_id: { type: "string" } },
                required: ["location_id"]
            }
        }
    },
    {
        type: "function",
        function: {
            name: "get_campus_info",
            description: "Retrieve physical bounds/status of a campus location.",
            parameters: {
                type: "object",
                properties: { location_id: { type: "string" } },
                required: ["location_id"]
            }
        }
    }
];

export async function POST(req) {
    try {
        const { message, history } = await req.json();

        const apiKey = process.env.CORAL_BRICKS_API_KEY || 'cb_XUvfFDd2GjOR9jzYG5a6TPvuEXG9K.....';

        const llm = new ResilientLLM({
            aiService: 'coralbricks',
            model: 'deepseek-v4-lite',
            apiKey: apiKey,
            maxTokens: 2048,
            temperature: 0.7,
            retries: 3,
            backoffFactor: 2
        });

        const messages = [];
        messages.push({
            role: 'system',
            content: 'You are the EcoNITH Campus Environmental Agent. You manage waste insights. Identify tools to get data if needed.'
        });

        if (history) {
            messages.push(...history);
        }
        messages.push({ role: 'user', content: message });

        let currentResponse = null;
        let toolRounds = 0;
        const MAX_ROUNDS = 5;

        // Agent Loop Processing (Max 5 tool rounds to avoid loops)
        while (toolRounds < MAX_ROUNDS) {
            // We pass the active history + tools payload to resilient-llm
            const response = await llm.chat(messages, { tools: toolsDefinition });

            const { content, toolCalls } = response;

            if (toolCalls && toolCalls.length > 0) {
                toolRounds++;
                // Push Assistant intent to history so the LLM remembers what tools it tried to call
                const assistantMessage = { role: 'assistant', content: content || null, tool_calls: toolCalls };
                messages.push(assistantMessage);

                // Execute Tools against Python API
                for (const tc of toolCalls) {
                    const functionName = tc.function.name;
                    const args = JSON.parse(tc.function.arguments);

                    let toolResult = "";
                    try {
                        // Re-route the tool execution to the Python backend that actually has sqlite/matplotlib!
                        const pyUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
                        const pyRes = await fetch(`${pyUrl}/api/tools/execute`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ tool_name: functionName, tool_args: args })
                        });
                        const data = await pyRes.json();
                        toolResult = JSON.stringify(data);
                    } catch (e) {
                        toolResult = JSON.stringify({ error: `Tool execution failed: ${e.message}` });
                    }

                    // Push strictly tool responses back to the model Context
                    messages.push({
                        role: 'tool',
                        tool_call_id: tc.id,
                        name: functionName,
                        content: toolResult
                    });
                }
            } else {
                // No tool calls means the LLM finished answering!
                currentResponse = content;
                break;
            }
        }

        if (!currentResponse) {
            currentResponse = "I reached my maximum tool iteration limit and could not resolve your query.";
        }

        return NextResponse.json({
            response: currentResponse,
            mode: "coralbricks_deepseek",
            rounds: toolRounds
        });

    } catch (error) {
        console.error("Agent Orchestration Error:", error);
        // Standard structured error handling from resilient-llm if available
        return NextResponse.json({ error: error.message || "Failed to process agent request" }, { status: 500 });
    }
}
