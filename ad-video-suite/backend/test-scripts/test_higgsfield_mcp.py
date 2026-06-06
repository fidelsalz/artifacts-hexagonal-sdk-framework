#!/usr/bin/env python3
"""
test_higgsfield_mcp.py — Interactive OAuth + connectivity probe for Higgsfield MCP.

The subprocess must stay alive while you authenticate in the browser —
the CLI runs a local callback server that captures the OAuth code.
Once authenticated, the token is stored in ~/.claude/ and reused by
all subsequent agent runs without re-authenticating.

Usage:
    python test_higgsfield_mcp.py
"""
import asyncio
import re
import webbrowser

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
)

MCP_URL     = "https://mcp.higgsfield.ai/mcp"
SERVER_NAME = "claude.ai higgsfield"   # normalises to mcp__claude_ai_higgsfield__*

OPTIONS = ClaudeAgentOptions(
    mcp_servers={SERVER_NAME: {"type": "http", "url": MCP_URL}},
    strict_mcp_config=True,
    allowed_tools=[
        "mcp__claude_ai_higgsfield__balance",
        "mcp__claude_ai_higgsfield__list_workspaces",
        "mcp__claude_ai_higgsfield__models_explore",
        "mcp__claude_ai_higgsfield__show_plans_and_credits",
    ],
    permission_mode="dontAsk",
    model="claude-haiku-4-5-20251001",
)


def _extract_url(text: str) -> str | None:
    """Pull the first https URL that looks like an auth/oauth link."""
    m = re.search(r'https://\S+', text)
    return m.group(0).rstrip('.,)\'"') if m else None


async def _query(client: ClaudeSDKClient, prompt: str) -> tuple[str, str | None]:
    """Send prompt, collect full text response. Return (text, oauth_url|None)."""
    await client.query(prompt)
    full_text = ""
    oauth_url = None
    async for msg in client.receive_response():
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock) and block.text.strip():
                    full_text += block.text
                    url = _extract_url(block.text)
                    if url and not oauth_url:
                        oauth_url = url
        elif isinstance(msg, ResultMessage):
            cost = f"${msg.total_cost_usd:.4f}" if msg.total_cost_usd else "n/a"
            print(f"   [turn done — turns={msg.num_turns} cost={cost}]")
            break
    return full_text, oauth_url


async def main():
    print("=" * 60)
    print("Higgsfield MCP probe")
    print(f"  server : {SERVER_NAME}")
    print(f"  url    : {MCP_URL}")
    print("=" * 60)

    client = ClaudeSDKClient(OPTIONS)
    await client.connect()
    print("\n[ok] subprocess connected — keep this terminal open during auth\n")

    # --- Round 1: trigger auth flow -----------------------------------------
    text, oauth_url = await _query(
        client,
        "Check the Higgsfield MCP connection status. "
        "If authentication is needed, start the auth flow and show me the full URL. "
        "If already authenticated, call mcp__claude_ai_higgsfield__balance "
        "and mcp__claude_ai_higgsfield__list_workspaces and report the results.",
    )
    print("\n[agent]\n" + text[:1200])

    if oauth_url:
        print(f"\n[auth] URL detected: {oauth_url}")
        print("[auth] Opening in browser — complete login there.")
        webbrowser.open(oauth_url)
        input("\n[auth] Press Enter AFTER you have authenticated in the browser… ")

        # --- Round 2: verify tools work after auth ---------------------------
        print("\n[probe] Testing tools after authentication…")
        text2, _ = await _query(
            client,
            "Authentication should now be complete. "
            "Call mcp__claude_ai_higgsfield__balance. "
            "Then call mcp__claude_ai_higgsfield__list_workspaces. "
            "Then call mcp__claude_ai_higgsfield__models_explore. "
            "Report all results clearly.",
        )
        print("\n[agent]\n" + text2[:1200])
    else:
        print("\n[ok] No auth URL found — tools may already be working above.")

    await client.disconnect()
    print("\n[done] Subprocess disconnected.")
    print("If tools worked, the token is stored in ~/.claude/ and the image-generation")
    print("agent will use it automatically on its next run.")


if __name__ == "__main__":
    asyncio.run(main())
