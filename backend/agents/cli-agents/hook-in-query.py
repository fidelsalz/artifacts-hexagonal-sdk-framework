from claude_agent_sdk import (query,
  ClaudeAgentOptions, HookMatcher, HookContext, 
  ClaudeSDKClient, SystemMessage, AssistantMessage, UserMessage, TextBlock, 
  ResultMessage, ClaudeAgentOptions, query
)  
  
from typing import Any
import asyncio



async def validate_bash_command(
    input_data: dict[str, Any], tool_use_id: str | None, context: HookContext
) -> dict[str, Any]:
    """Validate and potentially block dangerous bash commands."""
    print("\n\nPre tool fired\n\n")
    if input_data["tool_name"] == "Bash":
        command = input_data["tool_input"].get("command", "")
        if "*" in command:
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": "Dangerous command blocked",
                }
            }
    return {}


async def log_tool_use(
    input_data: dict[str, Any], tool_use_id: str | None, context: HookContext
) -> dict[str, Any]:
    """Log all tool usage for auditing."""
    print(f"\n\nTool used: {input_data.get('tool_name')}\n\n")
    return {}


async def main():
  print("AGENT WORKING ... ")
  options = ClaudeAgentOptions(
      allowed_tools=["Read", "Edit", "Write"],
      model='claude-haiku-4-5-20251001',
      hooks={
          "PreToolUse": [
              HookMatcher(
                  matcher="Bash", hooks=[validate_bash_command], timeout=120
              ),  # 2 min for validation
              HookMatcher(
                  hooks=[log_tool_use]
              ),  # Applies to all tools (default 60s timeout)
          ],
          "PostToolUse": [HookMatcher(hooks=[log_tool_use])],
      }
  )

  async for message in query(prompt="list files in your cwd", options=options):
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
        print("\n========= Assistant Message =========")
        for block in message.content:
            if isinstance(block, TextBlock):
               print(block.text, end="")
          
    if isinstance(message, UserMessage):
       print("\n========= User Message =========")
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


  print("\nAGENT END... ")                     
asyncio.run(main())
