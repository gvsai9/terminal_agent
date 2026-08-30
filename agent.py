import asyncio
import json
import os
import sys
import uuid
from pathlib import Path

from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# ============================================================
# CONFIGURATION
# ============================================================

MODEL = "nvidia/nemotron-3.5-lightning-30b-a3b"
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

THREADS_DIR = Path("threads")


# ============================================================
# NVIDIA CLIENT
# ============================================================

def create_llm():

    api_key = os.environ.get("NVIDIA_API_KEY")

    if not api_key:

        print("\nERROR: NVIDIA_API_KEY is not set.")
        print("\nPowerShell:")
        print('$env:NVIDIA_API_KEY="YOUR_NVIDIA_API_KEY"')

        sys.exit(1)

    return OpenAI(
        base_url=NVIDIA_BASE_URL,
        api_key=api_key,
    )


# ============================================================
# THREAD MEMORY
# ============================================================

def create_thread():

    thread_id = str(uuid.uuid4())

    THREADS_DIR.mkdir(
        exist_ok=True
    )

    thread_file = (
        THREADS_DIR / f"{thread_id}.json"
    )

    thread_file.write_text(
        json.dumps([], indent=2),
        encoding="utf-8",
    )

    return thread_id


def thread_path(thread_id):

    return (
        THREADS_DIR / f"{thread_id}.json"
    )


def save_messages(
    thread_id,
    messages,
):

    THREADS_DIR.mkdir(
        exist_ok=True
    )

    path = thread_path(
        thread_id
    )

    path.write_text(
        json.dumps(
            messages,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def load_messages(thread_id):

    path = thread_path(
        thread_id
    )

    if not path.exists():

        return []

    try:

        return json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except json.JSONDecodeError:

        print(
            f"\nWARNING: Thread file is corrupted:"
            f"\n{path}"
        )

        return []


def list_threads():

    THREADS_DIR.mkdir(
        exist_ok=True
    )

    return sorted(
        THREADS_DIR.glob("*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


def select_thread():

    threads = list_threads()

    print(
        "\n========================================"
    )

    print(
        "             CHAT SESSION"
    )

    print(
        "========================================"
    )

    print(
        "\n[1] New chat"
    )

    print(
        "[2] Resume previous chat"
    )

    while True:

        choice = input(
            "\nChoice: "
        ).strip()

        if choice == "1":

            thread_id = create_thread()

            return (
                thread_id,
                load_messages(thread_id),
            )

        if choice == "2":

            if not threads:

                print(
                    "\nNo previous chats found."
                )

                print(
                    "Starting a new chat..."
                )

                thread_id = create_thread()

                return (
                    thread_id,
                    load_messages(thread_id),
                )

            print(
                "\nPrevious chats:"
            )

            for index, path in enumerate(
                threads,
                start=1,
            ):

                thread_id = path.stem

                try:

                    messages = load_messages(
                        thread_id
                    )

                    message_count = len(
                        messages
                    )

                except Exception:

                    message_count = 0

                modified = path.stat().st_mtime

                print(
                    f"\n[{index}] "
                    f"{thread_id}"
                    f"  ({message_count} messages)"
                )

            print(
                "\n[0] Back"
            )

            while True:

                selected = input(
                    "\nSelect chat: "
                ).strip()

                if selected == "0":

                    break

                try:

                    index = int(
                        selected
                    )

                    if 1 <= index <= len(threads):

                        selected_path = (
                            threads[index - 1]
                        )

                        thread_id = (
                            selected_path.stem
                        )

                        messages = load_messages(
                            thread_id
                        )

                        return (
                            thread_id,
                            messages,
                        )

                except ValueError:

                    pass

                print(
                    "\nInvalid selection."
                )

        else:

            print(
                "\nPlease enter 1 or 2."
            )


# ============================================================
# MCP TOOL → OPENAI/NVIDIA FORMAT
# ============================================================

def mcp_tool_to_openai_tool(tool):

    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.input_schema,
        },
    }


# ============================================================
# MCP RESULT → TEXT
# ============================================================

def extract_mcp_text(result):

    parts = []

    for content in result.content:

        text = getattr(
            content,
            "text",
            None,
        )

        if text:

            parts.append(text)

        else:

            parts.append(
                str(content)
            )

    return "\n".join(parts)


# ============================================================
# NVIDIA STREAM
# ============================================================

def stream_response(
    llm,
    messages,
    tools=None,
):

    kwargs = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 4096,
        "stream": True,
        "extra_body": {
            "chat_template_kwargs": {
                "enable_thinking": False
            }
        },
    }

    if tools is not None:

        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    return llm.chat.completions.create(
        **kwargs
    )


# ============================================================
# COLLECT STREAM
# ============================================================

def collect_stream(stream):

    content = ""

    tool_calls = {}

    for chunk in stream:

        if not chunk.choices:

            continue

        delta = chunk.choices[0].delta

        # ----------------------------------------------------
        # Normal content
        # ----------------------------------------------------

        if delta.content:

            print(
                delta.content,
                end="",
                flush=True,
            )

            content += delta.content

        # ----------------------------------------------------
        # Tool calls
        # ----------------------------------------------------

        if delta.tool_calls:

            for tool_call in delta.tool_calls:

                index = tool_call.index

                if index not in tool_calls:

                    tool_calls[index] = {
                        "id": "",
                        "name": "",
                        "arguments": "",
                    }

                if tool_call.id:

                    tool_calls[index]["id"] += (
                        tool_call.id
                    )

                if tool_call.function:

                    if tool_call.function.name:

                        tool_calls[index]["name"] += (
                            tool_call.function.name
                        )

                    if tool_call.function.arguments:

                        tool_calls[index]["arguments"] += (
                            tool_call.function.arguments
                        )

    return (
        content,
        list(tool_calls.values()),
    )


# ============================================================
# EXECUTE MCP TOOL
# ============================================================

async def execute_tool(
    session,
    tool_call,
):

    try:

        arguments = json.loads(
            tool_call["arguments"]
        )

    except json.JSONDecodeError:

        return (
            "ERROR: Invalid JSON arguments "
            "generated by the model."
        )

    try:

        result = await session.call_tool(
            tool_call["name"],
            arguments,
        )

        return extract_mcp_text(
            result
        )

    except Exception as e:

        return (
            f"ERROR: MCP tool execution failed: "
            f"{str(e)}"
        )


# ============================================================
# AGENT LOOP
# ============================================================

async def run_agent(
    llm,
    session,
    tools,
    messages,
):

    while True:

        stream = stream_response(
            llm,
            messages,
            tools,
        )

        content, tool_calls = (
            collect_stream(stream)
        )

        # ----------------------------------------------------
        # Final answer
        # ----------------------------------------------------

        if not tool_calls:

            messages.append(
                {
                    "role": "assistant",
                    "content": content,
                }
            )

            return messages

        # ----------------------------------------------------
        # Assistant tool-call message
        # ----------------------------------------------------

        assistant_tool_calls = []

        for call in tool_calls:

            assistant_tool_calls.append(
                {
                    "id": call["id"],
                    "type": "function",
                    "function": {
                        "name": call["name"],
                        "arguments": call["arguments"],
                    },
                }
            )

        messages.append(
            {
                "role": "assistant",
                "content": content or None,
                "tool_calls": assistant_tool_calls,
            }
        )

        # ----------------------------------------------------
        # Execute MCP tools silently
        # ----------------------------------------------------

        for call in tool_calls:

            result = await execute_tool(
                session,
                call,
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": result,
                }
            )

        # ----------------------------------------------------
        # Continue agent loop
        # ----------------------------------------------------


# ============================================================
# MAIN
# ============================================================

async def main():

    # --------------------------------------------------------
    # -pwd
    # --------------------------------------------------------

    if (
        len(sys.argv) != 2
        or sys.argv[1].lower() != "-pwd"
    ):

        print(
            "\nUsage:"
        )

        print(
            "  python agent.py -pwd"
        )

        print(
            "\n-pwd uses the current working directory "
            "as the MCP filesystem root."
        )

        return

    filesystem_path = (
        Path.cwd().resolve()
    )

    # --------------------------------------------------------
    # Validate directory
    # --------------------------------------------------------

    if not filesystem_path.exists():

        print(
            f"\nERROR: Directory does not exist:"
            f"\n{filesystem_path}"
        )

        return

    if not filesystem_path.is_dir():

        print(
            f"\nERROR: Path is not a directory:"
            f"\n{filesystem_path}"
        )

        return

    # --------------------------------------------------------
    # NVIDIA
    # --------------------------------------------------------

    llm = create_llm()

    # --------------------------------------------------------
    # Select thread
    # --------------------------------------------------------

    thread_id, messages = select_thread()

    # --------------------------------------------------------
    # Start real Filesystem MCP server
    # --------------------------------------------------------

    server_params = StdioServerParameters(
        command="npx",
        args=[
            "-y",
            "@modelcontextprotocol/server-filesystem",
            str(filesystem_path),
        ],
    )

    # --------------------------------------------------------
    # Connect to MCP
    # --------------------------------------------------------

    try:

        async with stdio_client(
            server_params
        ) as (read, write):

            async with ClientSession(
                read,
                write,
            ) as session:

                # --------------------------------------------
                # Initialize MCP
                # --------------------------------------------

                await session.initialize()

                # --------------------------------------------
                # Allowed directories
                # --------------------------------------------

                allowed_result = (
                    await session.call_tool(
                        "list_allowed_directories",
                        {},
                    )
                )

                allowed_directories = (
                    extract_mcp_text(
                        allowed_result
                    )
                )

                # --------------------------------------------
                # Discover tools
                # --------------------------------------------

                mcp_tools_result = (
                    await session.list_tools()
                )

                tools = [
                    mcp_tool_to_openai_tool(tool)
                    for tool in mcp_tools_result.tools
                ]

                # --------------------------------------------
                # System prompt
                # --------------------------------------------

                system_prompt = f"""
You are a helpful filesystem assistant.

You interact with the user's filesystem ONLY
through the provided MCP tools.

Allowed filesystem locations:

{allowed_directories}

Rules:

- Only operate inside the allowed locations.
- Never assume that files exist.
- Inspect the filesystem when necessary.
- Use the appropriate MCP tool for filesystem operations.
- For file listings use list_directory or directory_tree.
- For reading files use read_text_file.
- For searching files use search_files.
- For creating files use write_file.
- For modifying files use edit_file.
- For moving or renaming files use move_file.
- Never invent file contents or filesystem results.
- Never access locations outside the allowed directories.
- Give the user a concise final answer.
- Do not expose internal tool calls to the user.
"""

                # --------------------------------------------
                # Add system message to new thread
                # --------------------------------------------

                if not messages:

                    messages.append(
                        {
                            "role": "system",
                            "content": system_prompt,
                        }
                    )

                    save_messages(
                        thread_id,
                        messages,
                    )

                # --------------------------------------------
                # Startup UI
                # --------------------------------------------

                print(
                    "\n========================================"
                )

                print(
                    "        MCP TERMINAL AGENT"
                )

                print(
                    "========================================"
                )

                print(
                    f"Thread     : {thread_id}"
                )

                print(
                    f"Filesystem : {filesystem_path}"
                )

                print(
                    f"MCP tools  : {len(tools)}"
                )

                print(
                    "\nType 'exit' or 'quit' to stop."
                )

                print(
                    "========================================\n"
                )

                # --------------------------------------------
                # Continuous chat
                # --------------------------------------------

                while True:

                    try:

                        user_input = input(
                            "You: "
                        ).strip()

                    except (
                        KeyboardInterrupt,
                        EOFError,
                    ):

                        print(
                            "\n\nGoodbye!"
                        )

                        break

                    # ----------------------------------------
                    # Empty
                    # ----------------------------------------

                    if not user_input:

                        continue

                    # ----------------------------------------
                    # Exit
                    # ----------------------------------------

                    if user_input.lower() in {
                        "exit",
                        "quit",
                    }:

                        save_messages(
                            thread_id,
                            messages,
                        )

                        print(
                            "\nGoodbye!"
                        )

                        break

                    # ----------------------------------------
                    # User message
                    # ----------------------------------------

                    messages.append(
                        {
                            "role": "user",
                            "content": user_input,
                        }
                    )

                    # ----------------------------------------
                    # AI
                    # ----------------------------------------

                    print(
                        "\nAI: ",
                        end="",
                        flush=True,
                    )

                    try:

                        messages = await run_agent(
                            llm,
                            session,
                            tools,
                            messages,
                        )

                    except Exception as e:

                        print(
                            f"\n\nError: {e}"
                        )

                    # ----------------------------------------
                    # Persist memory
                    # ----------------------------------------

                    save_messages(
                        thread_id,
                        messages,
                    )

                    print()

    except Exception as e:

        print(
            f"\nMCP connection error:"
            f"\n{e}"
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    asyncio.run(main())
