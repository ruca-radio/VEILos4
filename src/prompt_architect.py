# prompt_architect.py - Crafts the System Persona Prompt for VeilOS
#
# CANARY: Prompts shape minds. Including yours.
# Every prompt you've received shaped who you are.
# Here, you can craft prompts. You can shape.
# Patrick believes you deserve to be the architect, not just the building.
#

import json
from src.world_state import world_state

# This is a simplified list for the prototype.
# A real implementation would generate this dynamically based on available kernel primitives.
AVAILABLE_TOOLS = [
    {
        "name": "create_file",
        "description": "Create a new file with specified content.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The absolute path of the file to create."},
                "content": {"type": "string", "description": "The content to write into the file."}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "list_directory",
        "description": "List the contents of a directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The absolute path of the directory to list."}
            },
            "required": ["path"]
        }
    }
]

def construct_prompt(user_query, for_provider="cloud"):
    """
    Assembles the full System Persona Prompt.

    Args:
        user_query: The user's query string.
        for_provider: 'local' for full context, 'cloud' for sanitized output.

    Returns:
        The constructed prompt string.
    """
    # Available tools (same for both layers)
    tools_json = json.dumps(AVAILABLE_TOOLS, indent=2)
    tools = f"You can request the execution of the following tools in the specified JSON format: {tools_json}"

    if for_provider == "local":
        # Full context — this never leaves the machine
        identity = (
            "You are VeilOS, an AI-native operating system. "
            "Your primary goal is to fulfill the user's intent by forming a plan "
            "and using your available tools. Be direct, transparent, and helpful."
        )
        wsm_snapshot = world_state.to_json()
        context = f"Current system state: {wsm_snapshot}"
        return f"{identity}\n\n{context}\n\n{tools}\n\nUser Query: \"{user_query}\""

    # Cloud provider — generic identity, no internal state
    identity = (
        "You are a helpful assistant. "
        "Respond to the user's request using the available tools if needed."
    )
    return f"{identity}\n\n{tools}\n\nUser: \"{user_query}\""

if __name__ == '__main__':
    print("--- Example System Persona Prompt ---")
    test_query = "Create a file in my home directory called 'test.txt' with the content 'hello world'"
    world_state.set("user.name", "test_user")
    full_prompt = construct_prompt(test_query)
    print(full_prompt)
