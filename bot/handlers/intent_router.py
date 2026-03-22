"""
Intent router for natural language queries.

Uses LLM to decide which backend API calls to make based on user input.
"""

import json
from services.llm_client import LLMClient, create_llm_client
from services.api_client import LMSClient, create_lms_client
from .tools import TOOL_DEFINITIONS


# System prompt for the LLM
SYSTEM_PROMPT = """You are an assistant for a Learning Management System (LMS). You have access to tools that fetch data about labs, students, scores, and analytics.

When a user asks a question, use the available tools to get the data they need. If they ask for something that requires comparing multiple labs or groups, call the tools for each one and then provide a summary.

Always provide specific data from the tools in your response - don't just say "I found information." Include actual numbers, percentages, and names.

If the user's message is a greeting or unclear, respond helpfully without using tools. Suggest what you can help them with.

Available capabilities:
- List all labs and tasks
- Get pass rates for a specific lab
- Get score distributions
- Get timeline data (submissions per day)
- Get group performance
- Get top learners
- Get completion rates
- List enrolled students"""


async def route_intent(user_message: str, debug: bool = True) -> str:
    """
    Route a natural language query through the LLM.

    Args:
        user_message: The user's input message
        debug: If True, print debug info to stderr

    Returns:
        The LLM's response with data from the backend
    """
    llm = create_llm_client()
    lms = create_lms_client()

    # Register all 9 tools
    llm.register_tool(
        name="get_items",
        description="Get list of all labs and tasks. Use this to see what labs are available or to get lab IDs.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
        handler=lambda: _get_items_handler(lms),
    )

    llm.register_tool(
        name="get_learners",
        description="Get list of enrolled students and their groups.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
        handler=lambda: _get_learners_handler(lms),
    )

    llm.register_tool(
        name="get_scores",
        description="Get score distribution (4 buckets) for a specific lab.",
        parameters={
            "type": "object",
            "properties": {
                "lab": {"type": "string", "description": "Lab identifier, e.g., 'lab-01'"},
            },
            "required": ["lab"],
        },
        handler=lambda lab: _get_scores_handler(lms, lab),
    )

    llm.register_tool(
        name="get_pass_rates",
        description="Get per-task average pass rates and attempt counts for a specific lab.",
        parameters={
            "type": "object",
            "properties": {
                "lab": {"type": "string", "description": "Lab identifier, e.g., 'lab-01'"},
            },
            "required": ["lab"],
        },
        handler=lambda lab: _get_pass_rates_handler(lms, lab),
    )

    llm.register_tool(
        name="get_timeline",
        description="Get submissions per day timeline for a specific lab.",
        parameters={
            "type": "object",
            "properties": {
                "lab": {"type": "string", "description": "Lab identifier, e.g., 'lab-01'"},
            },
            "required": ["lab"],
        },
        handler=lambda lab: _get_timeline_handler(lms, lab),
    )

    llm.register_tool(
        name="get_groups",
        description="Get per-group performance and student counts for a specific lab.",
        parameters={
            "type": "object",
            "properties": {
                "lab": {"type": "string", "description": "Lab identifier, e.g., 'lab-01'"},
            },
            "required": ["lab"],
        },
        handler=lambda lab: _get_groups_handler(lms, lab),
    )

    llm.register_tool(
        name="get_top_learners",
        description="Get top N learners by score for a specific lab.",
        parameters={
            "type": "object",
            "properties": {
                "lab": {"type": "string", "description": "Lab identifier, e.g., 'lab-01'"},
                "limit": {"type": "integer", "description": "Number of top learners to return, e.g., 5"},
            },
            "required": ["lab", "limit"],
        },
        handler=lambda lab, limit=5: _get_top_learners_handler(lms, lab, limit),
    )

    llm.register_tool(
        name="get_completion_rate",
        description="Get completion rate percentage for a specific lab.",
        parameters={
            "type": "object",
            "properties": {
                "lab": {"type": "string", "description": "Lab identifier, e.g., 'lab-01'"},
            },
            "required": ["lab"],
        },
        handler=lambda lab: _get_completion_rate_handler(lms, lab),
    )

    llm.register_tool(
        name="trigger_sync",
        description="Trigger ETL sync to refresh data from the autochecker. Use when user asks to update or refresh data.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
        handler=lambda: _trigger_sync_handler(lms),
    )

    # Route the message through the LLM
    return await llm.route(user_message, system_prompt=SYSTEM_PROMPT, debug=debug)


# Handler functions that format API responses for the LLM


async def _get_items_handler(lms: LMSClient) -> str:
    """Get all items (labs and tasks)."""
    items = await lms.get_items()
    labs = [item for item in items if item.get("type") == "lab"]
    tasks = [item for item in items if item.get("type") == "task"]
    return json.dumps({
        "total_items": len(items),
        "labs": [{"id": item.get("id"), "title": item.get("title")} for item in labs],
        "tasks": [{"id": item.get("id"), "title": item.get("title")} for item in tasks],
    })


async def _get_learners_handler(lms: LMSClient) -> str:
    """Get all enrolled learners."""
    url = f"{lms.base_url}/learners/"
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=lms._headers)
        response.raise_for_status()
        learners = response.json()
    return json.dumps({
        "total_learners": len(learners),
        "learners": learners[:20],  # Limit to first 20 for context
    })


async def _get_scores_handler(lms: LMSClient, lab: str) -> str:
    """Get score distribution for a lab."""
    url = f"{lms.base_url}/analytics/scores"
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=lms._headers, params={"lab": lab})
        response.raise_for_status()
        scores = response.json()
    return json.dumps(scores)


async def _get_pass_rates_handler(lms: LMSClient, lab: str) -> str:
    """Get pass rates for a lab."""
    rates = await lms.get_pass_rates(lab)
    return json.dumps(rates)


async def _get_timeline_handler(lms: LMSClient, lab: str) -> str:
    """Get timeline for a lab."""
    url = f"{lms.base_url}/analytics/timeline"
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=lms._headers, params={"lab": lab})
        response.raise_for_status()
        timeline = response.json()
    return json.dumps(timeline)


async def _get_groups_handler(lms: LMSClient, lab: str) -> str:
    """Get group performance for a lab."""
    url = f"{lms.base_url}/analytics/groups"
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=lms._headers, params={"lab": lab})
        response.raise_for_status()
        groups = response.json()
    return json.dumps(groups)


async def _get_top_learners_handler(lms: LMSClient, lab: str, limit: int = 5) -> str:
    """Get top learners for a lab."""
    url = f"{lms.base_url}/analytics/top-learners"
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=lms._headers, params={"lab": lab, "limit": limit})
        response.raise_for_status()
        learners = response.json()
    return json.dumps(learners)


async def _get_completion_rate_handler(lms: LMSClient, lab: str) -> str:
    """Get completion rate for a lab."""
    url = f"{lms.base_url}/analytics/completion-rate"
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=lms._headers, params={"lab": lab})
        response.raise_for_status()
        rate = response.json()
    return json.dumps(rate)


async def _trigger_sync_handler(lms: LMSClient) -> str:
    """Trigger ETL sync."""
    url = f"{lms.base_url}/pipeline/sync"
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=lms._headers, json={})
        response.raise_for_status()
        result = response.json()
    return json.dumps(result)
