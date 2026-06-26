import json
from app.agents.nodes._llm import get_llm
from app.agents.prompts.digest_prompts import get_tool_extract_prompt

async def tool_version_extractor_node(state):
    llm = get_llm()
    prompt = get_tool_extract_prompt(content=state["raw_content"])

    try:
        response = await llm.ainvoke(prompt)
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0]

        tools = json.loads(content)

        tokens_in = response.usage_metadata.get("input_tokens", 0) if hasattr(response, "usage_metadata") and response.usage_metadata else 0
        tokens_out = response.usage_metadata.get("output_tokens", 0) if hasattr(response, "usage_metadata") and response.usage_metadata else 0

        return {
            **state,
            "tools_versions": tools if isinstance(tools, list) else [],
            "total_tokens": state["total_tokens"] + tokens_in + tokens_out,
            "total_cost": state["total_cost"] + (tokens_in * 3 / 1_000_000) + (tokens_out * 15 / 1_000_000),
        }
    except Exception as e:
        return {**state, "tools_versions": [], "errors": state["errors"] + [f"Tool extraction failed: {e}"]}
