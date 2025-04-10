"""
DeeperChat
Author: Brianna Thorez
https://github.com/BriannaThorez/DeeperChat
"""
#main.py    
#--- IMPORTS ---
#System level imports
import os
import re
import sys
import json
from typing import Iterator, Optional, List, Dict 

#External packages which need to be installed via requirements
from utilities.requirements import check_and_install_requirements#install requirements
check_and_install_requirements()
import requests
import pyperclip  

#Utility module scripts
from utilities.terminal_resize import increase_terminal_buffer
increase_terminal_buffer()
from utilities.dynamic_importer import dynamic_import
from utilities.setup_config import ensure_config
from utilities.token_counter import truncate_history_by_tokens
#Program-related module scripts
from cognition_handler import ResponseHandler

# Attempt to import expansive module versions with fallback to default module with source tracking
prompt_handler, import_error, source = dynamic_import("prompt_handler")
if prompt_handler:
    enhance_prompt = prompt_handler.enhance_prompt
    print(f"\n[System] Using {source}/prompt_handler.py")
    if import_error:  # This would only happen if there were warnings from previous attempts
        print(f"Warning: {import_error.splitlines()[0]}")
else:
    print("\n[System] Error: Could not import prompt_handler!")
    if import_error:
        print(f"Reason: {import_error.splitlines()[0]}")
    sys.exit(1)

#--- END IMPORTS ---

# ==============================================
# Rich Display Module for code blocks
# ==============================================
try:
    from rich.syntax import Syntax
    from rich.console import Console
    from rich.theme import Theme
    RICH_AVAILABLE = True
    # Define custom theme with black background
    # Force true black background (RGB: 0,0,0)
    custom_theme = Theme({
        "background": "on #000000",  # True black
        "code": "white on #000000",
        "keyword": "bold #56B6C2",    # Cyan
        "string": "#98C379",          # Green
        "number": "#D19A66",          # Orange
        "comment": "italic #5C6370",  # Gray
    })
    
    console = Console(theme=custom_theme)
    
    # Built-in dark themes available in Rich:
    # "monokai", "native", "fruity", "perldoc", "tango", "rrt", "xcode"
    SYNTAX_THEME = "monokai"  # The best dark theme option

except ImportError:
    RICH_AVAILABLE = False
def display_code_blocks(blocks: list[dict]):
    """Handle multiple code blocks with numbered copy options"""
    for i, block in enumerate(blocks, 1):
        print(f"\n{'━'*30}\nCode Block {i}/{len(blocks)}")
                    
        if RICH_AVAILABLE:
            syntax = Syntax(
                block['content'],
                block['language'],
                theme=SYNTAX_THEME,
                background_color="#000000",  # Force black background
                line_numbers=False,
                word_wrap=True
            )
            console.print(syntax)
        else:
            print(f"```{block['language']}")
            print(block['content'])
            print("```")

        dark_blue_bg = "\033[48;2;0;0;95m"
        white_text = "\033[38;2;255;255;255m"
        reset = "\033[0m"
        print(f"{dark_blue_bg}{white_text}📋 [Press ({i}) to copy this block]{reset}")
        print(f"{'━'*30}\n")
        
    print("Select a number to copy (or Enter to continue): ", end='', flush=True)
    try:
        choice = input()
        if choice.isdigit() and 0 < int(choice) <= len(blocks):
            pyperclip.copy(blocks[int(choice)-1]['content'])
            print(f"✓ Copied Block {choice}!")
    except Exception:
        pass

# ==============================================
# API Streaming Function
# ==============================================
def stream_deepseek_api(history: List[Dict[str, str]], api_key: str) -> Iterator[str]:
    """
    Streams response from DeepSeek API using conversation history.

    Args:
        history: A list of message dictionaries, e.g.,
                 [{"role": "user", "content": "Hello"},
                  {"role": "assistant", "content": "Hi there!"}]
        api_key: The DeepSeek API key.

    Yields:
        String chunks of the API response.
    """
    url = "https://api.deepseek.com/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }

    data = {
        "model": "deepseek-chat",
        "messages": history, # <-- Use the provided history
        "stream": True,
        "max_tokens": 8000,
        "temperature": 0.1
    }

    try:
        with requests.post(url, headers=headers, json=data, stream=True) as response:
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data:'):
                        json_data = decoded_line[5:].strip()
                        if json_data != '[DONE]':
                            try:
                                chunk = json.loads(json_data)
                                if 'choices' in chunk and len(chunk['choices']) > 0:
                                    content = chunk['choices'][0].get('delta', {}).get('content', '')
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                continue
    except requests.exceptions.RequestException as e:
        yield f"\nAPI request failed: {e}"
# ==============================================

# ==============================================
# Chat Loop
# ==============================================

def chat_loop(api_key: str, use_rich: bool = True):

    global prompt # Keep prompt global if needed elsewhere, though maybe reconsider later
    system_timestamp = cognition_handler._generate_timestamp() 
    system_message_timestamp  = f"{system_timestamp}"
    system_message_content = f"""You are a helpful assistant with retrieval from a vector database, which contains documents and chat history between yourself and users. Use the additional context where appropriate to privide concise and accurate answers."""
    system_message = f"{system_message_timestamp} {system_message_content}"

    # --- Initialize the history list with the system message ---
    conversation_history: List[Dict[str, str]] = [
        {"role": "system", "content": system_message}
    ]
    while True:
        print(f"\n{AppName} Type [exit] or [quit] to end chat")
        # Keep the original prompt for storage/display if needed
        original_prompt = input(f"\n{user_name}: ")

        if original_prompt.lower() in ('exit', 'quit'):
            print("Ending chat session...")
            break

        if not original_prompt.strip():
            print("Please enter a valid prompt.")          

        # Enhance the prompt with DB search results        
        enhanced_prompt = enhance_prompt(original_prompt)
        # --- Add user message to Messages conversation history---
        conversation_history.append({"role": "user", "content": enhanced_prompt}) # <-- Add user prompt to history

        # --- Messages Truncation ---
        # Uses token limit to determine maximum messages length and adjust accordingly
        MAX_HISTORY_TOKENS = 5000
        conversation_history, current_token_count = truncate_history_by_tokens(
            history=conversation_history,
            max_tokens=MAX_HISTORY_TOKENS
        )
        print(f"[Debug] Token count after truncation: {current_token_count}")
        # --- End Truncation  ---
        # --- Update System Message with Current Timestamp ---
        current_system_message_timestamp = cognition_handler._generate_timestamp() # Line 1: Get timestamp
        conversation_history[0]['content'] =  f"{current_system_message_timestamp} {system_message_content}"

       # --- End Update ---
        # --- Print response (streaming) ---
        print(f"\n{assistant_name}: ", end='', flush=True)
        full_response = []
        # Pass messages history to the API function
        for chunk in stream_deepseek_api(conversation_history, api_key): 
            print(chunk, end='', flush=True)
            full_response.append(chunk)
        response_text = ''.join(full_response)
        # --- END Print response (streaming) ---
        # --- Add assistant response to Messages conversation history ---
        if response_text and not response_text.startswith("\nAPI request failed:"): # Avoid adding error messages as assistant responses
             conversation_history.append({"role": "assistant", "content": response_text})
        print("\n--- Full Conversation History ---")
        for message_dict in conversation_history:
            content = message_dict.get("content", "") # Get the content, default to empty string if missing
            print(f"\033[32m{content}\033[0m") # Print content in green
        print("---------------------------------\n")

        # --- Store the prompt and response in ChromaDB---
        """
        First, Remove enhanced prompt with search results and replace with original user prompt
        to ensure an uncluttered chat-history and plenty of space for new results
        Then, Add most recent messages user and assistant to DB
        """
        conversation_history[-2]['content'] = original_prompt
        latest_response_message = conversation_history[-1]['content']
        latest_user_message = conversation_history[-2]['content']
        cognition_handler.store_response(user_name, assistant_name, latest_user_message, latest_response_message)
        # ---END Store the prompt and response in ChromaDB---

        if use_rich and any('```' in line for line in full_response): # Check if response contains code blocks
            extracted_code = extract_code_blocks(response_text) # Pass full response text
            if extracted_code:
                print("\n[Code Output]")
                display_code_blocks(extracted_code)




def extract_code_blocks(text: str) -> list[dict]:
    """Robust code block extraction that handles:
    - Properly formatted code blocks only
    - Nested backticks within code
    - Language specifiers
    - Won't match plain text between blocks
    """
    import re
    # This pattern strictly matches proper code blocks only
    pattern = r'```([a-zA-Z0-9\+]*)\n([\s\S]*?)\n```'
    matches = re.findall(pattern, text)
    
    blocks = []
    for lang, content in matches:
        content = content.strip()
        if content:  # Only add non-empty blocks
            blocks.append({
                'language': lang or 'text',
                'content': content
            })
    return blocks

# ==============================================
# Main Execution
# ==============================================
if __name__ == "__main__":
    # Load or create config
    config = ensure_config()
    # Verify API key exists (should always exist after ensure_config)
    if not config.get('deepseek_api_key'):
        print("❌ No API key configured - please check config.json")
        exit(1)
    """
    user and assistant name are defined for future metadata usage in a VectorDB 
    which will allow individual user based ontext
    """
    AppName = "DeeperChat"
    api_key = config['deepseek_api_key']
    user_name = config['user_name']
    assistant_name = "Assistant"
    prompt = None
    cognition_handler = ResponseHandler()
    # Start chat loop with Rich disabled if not available
    chat_loop(config['deepseek_api_key'], use_rich=RICH_AVAILABLE)