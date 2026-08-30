\# MCP Terminal Agent



A terminal-based AI filesystem agent powered by \*\*NVIDIA Nemotron\*\* and the \*\*Model Context Protocol (MCP)\*\*.



The agent allows an LLM to interact with a user-selected local directory through the real MCP filesystem server.



\## Architecture



```text

&#x20;                   Terminal

&#x20;                      │

&#x20;                      ▼

&#x20;               NVIDIA Nemotron

&#x20;                      │

&#x20;                      ▼

&#x20;                 MCP Client

&#x20;                      │

&#x20;                      ▼

&#x20;         Filesystem MCP Server

&#x20;                      │

&#x20;                      ▼

&#x20;             User's local folder

```



The MCP server is automatically started by the Python agent.



\## Features



\* NVIDIA Nemotron LLM

\* Real MCP filesystem server

\* Automatic MCP server startup

\* Dynamic MCP tool discovery

\* Dynamic allowed-directory discovery

\* Multi-step tool execution

\* Streaming AI responses

\* Continuous terminal chat

\* Conversation/thread memory

\* Unique UUID for every chat session

\* Local thread storage

\* User-selected filesystem root

\* Filesystem access controlled by the MCP server

\* API key stored through an environment variable



\## Requirements



Install:



\* Python 3.10+

\* Node.js and npm

\* An NVIDIA API key



The filesystem MCP server is launched through `npx`, so Node.js/npm must be available in the terminal.



\## Installation



\### 1. Clone the repository



```powershell

git clone <YOUR\_GITHUB\_REPOSITORY\_URL>

cd MCP-Terminal-Agent

```



\### 2. Create a virtual environment



Windows PowerShell:



```powershell

python -m venv .venv

```



Activate it:



```powershell

.venv\\Scripts\\Activate.ps1

```



\### 3. Install Python dependencies



```powershell

pip install -r requirements.txt

```



\### 4. Configure the NVIDIA API key



Do not put your API key inside the source code.



PowerShell:



```powershell

$env:NVIDIA\_API\_KEY="YOUR\_NVIDIA\_API\_KEY"

```



For Command Prompt:



```cmd

set NVIDIA\_API\_KEY=YOUR\_NVIDIA\_API\_KEY

```



\## Run



Specify the local directory that the MCP filesystem server should be allowed to access:



```powershell

python agent.py D:\\MyProject

```



For example:



```powershell

python agent.py D:\\MCP-Lab

```



The agent automatically launches:



```text

npx -y @modelcontextprotocol/server-filesystem D:\\MCP-Lab

```



You do \*\*not\*\* need to start the MCP server manually.



\## Example



```text

========================================

&#x20;       MCP TERMINAL AGENT

========================================



Thread: 4d7e1c2a-....

Filesystem: D:\\MCP-Lab

MCP tools: 15



Type 'exit' or 'quit' to stop.

========================================



You: list my files



AI: I found the following files...



You: read hello\_world.py



AI: The file contains...



You: what did that file do?



AI: It is a Python program that...

```



\## Multi-step tasks



The agent can decide to use multiple MCP tools when necessary.



For example:



```text

You: Find all Python files and explain what each one does.

```



The model may perform:



```text

search\_files

&#x20;     ↓

read\_text\_file

&#x20;     ↓

read\_text\_file

&#x20;     ↓

final response

```



The tool execution happens internally; the user sees the final AI response rather than the raw tool-call details.



\## Thread Memory



Every chat session receives a unique UUID:



```text

4d7e1c2a-....

```



Conversation history is stored locally:



```text

threads/

└── <thread-id>.json

```



Thread files are ignored by Git and are never intended to be committed to the repository.



Each user running the project has their own local threads.



\## Filesystem Security



The agent does not directly implement filesystem access.



Instead:



```text

LLM

&#x20;│

&#x20;▼

MCP Client

&#x20;│

&#x20;▼

Filesystem MCP Server

&#x20;│

&#x20;▼

Allowed directory

```



The filesystem MCP server determines which directories can be accessed.



For example:



```powershell

python agent.py D:\\MyProject

```



allows the MCP filesystem server to operate within the selected directory.



The LLM should not be treated as the security boundary. The MCP server provides the actual filesystem capability and access restrictions.



\## API Key Security



Never commit your NVIDIA API key.



The project reads:



```text

NVIDIA\_API\_KEY

```



from the environment.



Do not place API keys directly in `agent.py`.



\## Stopping the Agent



Type:



```text

exit

```



or:



```text

quit

```



You can also use:



```text

Ctrl+C

```



The Python agent closes the MCP connection and the automatically started MCP server process.



\## Project Structure



```text

MCP-Terminal-Agent/

│

├── agent.py

├── requirements.txt

├── README.md

├── .gitignore

└── threads/

```



The `threads/` directory is generated locally and is excluded from Git.



\## Technologies



\* Python

\* NVIDIA Nemotron

\* OpenAI-compatible NVIDIA API

\* Model Context Protocol (MCP)

\* MCP Filesystem Server

\* Node.js / npm



\## Disclaimer



This project is intended for local experimentation and learning with MCP and agentic AI.



Always review the directories you grant to filesystem tools before allowing an AI agent to operate on important files.



