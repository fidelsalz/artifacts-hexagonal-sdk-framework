import asyncio
from typing import Any
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeSDKClient,
    ClaudeAgentOptions,
    HookMatcher,
    HookContext,
    ResultMessage,
    SystemMessage,
    AssistantMessage,
    UserMessage, 
    TextBlock, 
    query
)

async def pre_tool_logger(
    input_data: dict[str, Any], tool_use_id: str | None, context: HookContext
) -> dict[str, Any]:
    """Log all tool usage before execution."""
    tool_name = input_data.get("tool_name", "unknown")
    print(f"[PRE-TOOL] About to use: {tool_name}")

    # You can modify or block the tool execution here
    if tool_name == "Bash" and "rm -rf" in str(input_data.get("tool_input", {})):
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": "Dangerous command blocked",
            }
        }
    return {}


async def post_tool_logger(
    input_data: dict[str, Any], tool_use_id: str | None, context: HookContext
) -> dict[str, Any]:
    """Log results after tool execution."""
    tool_name = input_data.get("tool_name", "unknown")
    print(f"[POST-TOOL] Completed: {tool_name}")
    return {}


async def user_prompt_modifier(
    input_data: dict[str, Any], tool_use_id: str | None, context: HookContext
) -> dict[str, Any]:
    """Add context to user prompts."""
    original_prompt = input_data.get("prompt", "")

    # Add a timestamp as additional context for Claude to see
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": f"[Submitted at {timestamp}] Original prompt: {original_prompt}",
        }
    }



async def main():
# Load project settings to include CLAUDE.md files

  options = ClaudeAgentOptions(
        hooks={
            "PreToolUse": [
                HookMatcher(hooks=[pre_tool_logger]),
                HookMatcher(matcher="Bash", hooks=[pre_tool_logger]),
            ],
            "PostToolUse": [HookMatcher(hooks=[post_tool_logger])],
            "UserPromptSubmit": [HookMatcher(hooks=[user_prompt_modifier])],
        },
        allowed_tools=["Read", "Write", "Bash"],
        model='claude-haiku-4-5-20251001',
        permission_mode="acceptEdits",
    )
    
  async for message in query(
    prompt="""
        hi, list files in your cwd
          
      """,
    options=options,
    
  ):
     if isinstance(message, SystemMessage):
        print("\n========= System Message =========")
        system_msg=message
        uuid = system_msg.data.get('uuid')
        model = system_msg.data.get('model')
        session_id = system_msg.data.get('session_id')
        claude_version = system_msg.data.get('claude_code_version')
        cwd = system_msg.data.get('cwd')
        permission_mode = system_msg.data.get('permissionMode')
        tools = system_msg.data.get('tools')
        agents = system_msg.data.get('agents')
        
        print(f"UUID: {uuid}")
        print(f"Model: {model}")
        print(f"Session ID: {session_id}")
        print(f"Claude Version: {claude_version}")
        print(f"CWD: {cwd}")
        print(f"Permission Mode: {permission_mode}")
        print(f"Tools count: {len(tools) if tools else 0}")
        print(f"Agents: {agents}")
     
     
     
     if isinstance(message, AssistantMessage):
        #print("\n========= Assistant Message =========")
        for block in message.content:
            if isinstance(block, TextBlock):
               print("- ",block.text, end="")
     
     
     if isinstance(message, UserMessage):
       print("\n      -User Message-")
       print(message)
     
     
     if isinstance(message, ResultMessage):
        print("\n\n========= Result Message =========")
        result_msg=message
        # Method 1: Extract individual values directly
        session_id = result_msg.session_id
        duration_ms = result_msg.duration_ms
        duration_api_ms = result_msg.duration_api_ms
        num_turns = result_msg.num_turns
        total_cost_usd = result_msg.total_cost_usd

        print("=== Basic Numerical Data ===")
        print(f"Session ID: {session_id}")
        print(f"Duration (ms): {duration_ms}")
        print(f"Duration API (ms): {duration_api_ms}")
        print(f"Number of turns: {num_turns}")
        print(f"Total cost (USD): ${total_cost_usd:.6f}")

        # Method 2: Extract usage data (tokens)
        input_tokens = result_msg.usage.get('input_tokens', 0)
        cache_creation_tokens = result_msg.usage.get('cache_creation_input_tokens', 0)
        cache_read_tokens = result_msg.usage.get('cache_read_input_tokens', 0)
        output_tokens = result_msg.usage.get('output_tokens', 0)
        total_tokens = input_tokens + cache_creation_tokens + cache_read_tokens + output_tokens

        print("\n=== Token Usage ===")
        print(f"Input tokens: {input_tokens:,}")
        print(f"Cache creation tokens: {cache_creation_tokens:,}")
        print(f"Cache read tokens: {cache_read_tokens:,}")
        print(f"Output tokens: {output_tokens:,}")
        print(f"Total tokens: {total_tokens:,}")

        # Method 3: Extract nested server tool usage
        server_tool_use = result_msg.usage.get('server_tool_use', {})
        web_search_requests = server_tool_use.get('web_search_requests', 0)
        web_fetch_requests = server_tool_use.get('web_fetch_requests', 0)

        print("\n=== Server Tool Usage ===")
        print(f"Web search requests: {web_search_requests}")
        print(f"Web fetch requests: {web_fetch_requests}")
                     
        #print(message)

asyncio.run(main())
