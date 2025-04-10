# token_counter.py
import tiktoken
from typing import List, Dict, Tuple

# --- Constants ---
# Default model - assuming DeepSeek uses encoding similar to GPT-3.5/4
# Use "cl100k_base" if specific model name causes issues
DEFAULT_MODEL_FOR_TOKENIZER = "gpt-4"

# --- Helper Function to Count Tokens ---
def count_message_tokens(messages: List[Dict[str, str]], model: str = DEFAULT_MODEL_FOR_TOKENIZER) -> int:
    """
    Returns the approximate number of tokens used by a list of messages
    based on OpenAI's cookbook examples. Adjust logic if Deepseek differs.
    """
    try:
        # Attempt to get encoding for the specified model
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # Fallback to cl100k_base if the model name isn't recognized
        # cl100k_base is used by GPT-3.5-turbo and GPT-4 models
        print(f"Warning: Model '{model}' not found by tiktoken. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")

    # --- Token counting logic based on OpenAI's recommended approach ---
    # Note: This might need minor adjustments if Deepseek's exact tokenization differs.
    #       Refer to Deepseek documentation if available for specifics.
    num_tokens = 0
    for message in messages:
        # Each message incurs overhead tokens (role, separators, etc.)
        # OpenAI examples use ~3-4 tokens overhead per message. Let's use 4 for a safe estimate.
        num_tokens += 4
        for key, value in message.items():
            if value: # Ensure value exists before encoding
                try:
                    num_tokens += len(encoding.encode(str(value))) # Encode content/role value
                except Exception as e:
                    print(f"Warning: Could not encode value for key '{key}'. Error: {e}")
                    # Decide how to handle encoding errors, e.g., skip or estimate
            # If message includes 'name', add ~1 token overhead (less common)
            # if key == "name":
            #     num_tokens += 1
    # Add a few final tokens for the assistant's reply priming, e.g., <|im_start|>assistant
    num_tokens += 3
    return num_tokens

# --- Main Truncation Function ---
def truncate_history_by_tokens(
    history: List[Dict[str, str]],
    max_tokens: int,
    model_name: str = DEFAULT_MODEL_FOR_TOKENIZER
) -> Tuple[List[Dict[str, str]], int]:
    """
    Truncates conversation history if it exceeds max_tokens.

    Removes the oldest pair of messages (assumed user/assistant)
    until the total token count is within the limit.

    Args:
        history: The list of message dictionaries.
        max_tokens: The maximum allowed tokens for the history.
        model_name: The model name for tiktoken encoding.

    Returns:
        A tuple containing:
        - The potentially truncated history list.
        - The final token count of the returned history.
    """
    current_tokens = count_message_tokens(history, model_name)

    # Check if history needs truncation
    while current_tokens > max_tokens:
        if len(history) >= 2:
            # Remove the oldest message (index 0) and the next oldest (new index 0)
            # This assumes the oldest messages are a user/assistant pair.
            removed_msg1 = history.pop(0)
            removed_msg2 = history.pop(0)
            print(f"[History Truncation] Token limit ({max_tokens}) exceeded ({current_tokens}). Removing oldest pair:")
            print(f"  - Removed: {removed_msg1['role']}: {removed_msg1['content'][:50]}...")
            print(f"  - Removed: {removed_msg2['role']}: {removed_msg2['content'][:50]}...")

            # Recalculate token count after removal
            current_tokens = count_message_tokens(history, model_name)
            print(f"[History Truncation] New token count: {current_tokens}. History length: {len(history)}")
        else:
            # Cannot remove a pair if fewer than 2 messages are left.
            print(f"[History Truncation] Warning: Cannot truncate further (less than 2 messages left) even though token limit ({max_tokens}) is exceeded ({current_tokens}).")
            break # Exit the loop

    # Return the modified history and its final token count
    return history, current_tokens