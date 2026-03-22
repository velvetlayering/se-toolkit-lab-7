"""
LLM Client for intent routing.

Handles communication with the LLM API and manages the tool-calling loop.
"""

import json
import httpx
from typing import Any, Callable


class LLMClient:
    """Client for LLM API with tool calling support."""

    def __init__(
        self,
        base_url: str = "http://localhost:42005/v1",
        api_key: str = "",
        model: str = "coder-model",
    ):
        """
        Initialize the LLM client.

        Args:
            base_url: Base URL of the LLM API
            api_key: API key for authentication
            model: Model name to use
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        } if api_key else {}

    def register_tool(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        handler: Callable[..., Any],
    ) -> None:
        """
        Register a tool that the LLM can call.

        Args:
            name: Tool name
            description: Description of what the tool does
            parameters: JSON Schema for tool parameters
            handler: Async function to call when LLM invokes this tool
        """
        if not hasattr(self, "_tools"):
            self._tools: dict[str, dict[str, Any]] = {}
            self._handlers: dict[str, Callable[..., Any]] = {}

        self._tools[name] = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            },
        }
        self._handlers[name] = handler

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Get tool definitions in OpenAI-compatible format."""
        if not hasattr(self, "_tools"):
            return []
        return list(self._tools.values())

    async def chat(
        self,
        messages: list[dict[str, Any]],
        system_prompt: str | None = None,
    ) -> tuple[str, list[dict[str, Any]]]:
        """
        Send a chat message to the LLM.

        Args:
            messages: Conversation history
            system_prompt: Optional system prompt

        Returns:
            Tuple of (response text, list of tool calls)
        """
        payload = {
            "model": self.model,
            "messages": [],
        }

        if system_prompt:
            payload["messages"].append({"role": "system", "content": system_prompt})

        payload["messages"].extend(messages)

        # Add tool definitions if any are registered
        if hasattr(self, "_tools") and self._tools:
            payload["tools"] = self.get_tool_definitions()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers,
                json=payload,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()

        choice = data["choices"][0]["message"]
        content = choice.get("content", "")
        tool_calls = choice.get("tool_calls", [])

        return content, tool_calls

    async def route(
        self,
        user_message: str,
        system_prompt: str | None = None,
        debug: bool = False,
    ) -> str:
        """
        Route a user message through the LLM with tool calling.

        This implements the tool-calling loop:
        1. Send message to LLM
        2. If LLM calls tools, execute them
        3. Feed results back to LLM
        4. Repeat until LLM returns final answer

        Args:
            user_message: The user's input message
            system_prompt: Optional system prompt
            debug: If True, print debug info to stderr

        Returns:
            The LLM's final response
        """
        messages = [{"role": "user", "content": user_message}]
        max_iterations = 5  # Prevent infinite loops

        for _ in range(max_iterations):
            content, tool_calls = await self.chat(messages, system_prompt)

            # If no tool calls, return the content
            if not tool_calls:
                return content or "I didn't understand. Here's what I can help with:\n- List available labs\n- Show scores for a specific lab\n- Compare groups or learners\n- Check completion rates"

            # Execute tool calls
            tool_results = []
            for tool_call in tool_calls:
                function = tool_call["function"]
                name = function["name"]
                arguments = json.loads(function["arguments"])

                if debug:
                    print(f"[tool] LLM called: {name}({arguments})", file=__import__("sys").stderr)

                if name not in self._handlers:
                    result = f"Error: Unknown tool '{name}'"
                else:
                    try:
                        handler = self._handlers[name]
                        result = await handler(**arguments)
                        if debug:
                            result_str = str(result)
                            if len(result_str) > 100:
                                result_str = result_str[:100] + "..."
                            print(f"[tool] Result: {result_str}", file=__import__("sys").stderr)
                    except Exception as e:
                        result = f"Error: {str(e)}"

                tool_results.append({
                    "type": "function",
                    "id": tool_call["id"],
                    "name": name,
                    "content": json.dumps(result) if not isinstance(result, str) else result,
                })

            # Add assistant message and tool results to conversation
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": tool_calls,
            })

            for result in tool_results:
                messages.append({
                    "role": "tool",
                    "tool_call_id": result["id"],
                    "content": result["content"],
                })

            if debug:
                print(f"[summary] Feeding {len(tool_results)} tool result(s) back to LLM", file=__import__("sys").stderr)

        return "I'm having trouble processing this request. Please try rephrasing."


def create_llm_client() -> LLMClient:
    """Create an LLM client from environment variables."""
    import os
    from config import load_config

    # Load environment variables from .env.bot.secret
    load_config()

    base_url = os.getenv("LLM_API_BASE_URL", "http://localhost:42005/v1")
    api_key = os.getenv("LLM_API_KEY", "")
    model = os.getenv("LLM_API_MODEL", "coder-model")

    return LLMClient(base_url=base_url, api_key=api_key, model=model)
