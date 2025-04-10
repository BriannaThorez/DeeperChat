#prompt_handler.py
#prompt_handler.py
import ast
import subprocess
import difflib
import os
import re
from typing import Optional, Tuple, List, Dict
from cognition_handler import ResponseHandler

class PromptEnhancer:
    def __init__(self):
        self.cognition_handler = ResponseHandler()
        
    def detect_and_read_python_files(self, prompt: str) -> Tuple[str, bool]:
        """
        Detects .py files mentioned in prompt and reads their content.
        Returns: (updated_prompt, found_files)
        """
        # Find all .py files mentioned in prompt
        py_files = re.findall(r'(\w+\.py)', prompt)
        if not py_files:
            return prompt, False

        # Create expansive directory if it doesn't exist
        os.makedirs('expansive', exist_ok=True)    
        
       # Read found files from expansive directory only
        file_contents = []
        for file in py_files:
            file_path = os.path.join('expansive', file)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        file_contents.append(f"Content of {file}:\n```python\n{content}\n```")
                except Exception as e:
                    file_contents.append(f"Error reading {file}: {str(e)}")
            else:
                file_contents.append(f"File {file} not found in expansive directory")
        
        # Combine original prompt with file contents
        updated_prompt = f"{prompt}\n\n[The following Python files were detected in 'expansive' directory:]\n" + "\n".join(file_contents)
        return updated_prompt, bool(file_contents)


    def _format_memory_results(self, results: List[Dict]) -> str:
        """
        Format memory search results into a readable context string,
        handling different content types (prompt/response).
        """
        if not results:
            return ""

        context_lines = ["\n[CONTEXT]\n[Relevant history & memory results as [User][Timestamp][ChatHistory]:"]
        for i, result in enumerate(results, 1):
            # Safely get required fields with defaults
            metadata = result.get('metadata', {})
            # Content is already formatted as 'speaker[timestamp]: text'
            formatted_content = result.get('content', '[Content Missing]')
            score = result.get('score', 0.0)
            content_type = metadata.get('content_type', 'unknown') # Check if it's prompt or response

            # Add the header for the result
            context_lines.append(f"\n=== Similarity: {score:.2f} ===")

            # Add the recalled content (already includes speaker and timestamp)
            context_lines.append(formatted_content)

            # --- Safely handle original_prompt ---
            # Only add original_prompt context if it was a response chunk and the key exists
            if content_type == 'response':
                original_prompt = metadata.get('original_prompt') # Use .get() for safe access
                if original_prompt:
                    # Add as additional context, not replacing the main content line
                    context_lines.append(f"  (Context: In response to prompt starting with '{original_prompt}')")
            # --- End safe handling ---

        # Join the lines into a single string
        context_str = "\n".join(context_lines)
        return context_str

    def enhance_prompt(self, prompt: str) -> str:
        """
        Enhanced version that:
        1. Checks for Python files
        2. Searches for relevant past conversations
        3. Combines everything into final prompt
        """
        # First check for Python files
        enhanced_prompt, files_found = self.detect_and_read_python_files(prompt)
        
        if files_found:
            print("\n[System] Detected and included Python file(s) from expansive directory")
        
        # Search for relevant past conversations
        memory_results = self.cognition_handler.recall_memory(prompt, max_results=3)
        memory_context = self._format_memory_results(memory_results)

        if memory_results:
            print(f"\n[System] Found {len(memory_results)} relevant past conversations")
            
        # Combine everything
        final_prompt = f"If applicable, use the following to assist in answering the user instruction:{memory_context} \n[INSTRUCTION]:\n {enhanced_prompt}"
        #print(f"\033[32m{final_prompt}\033[0m")
        return final_prompt

# For backward compatibility
def enhance_prompt(prompt: str) -> str:
    return PromptEnhancer().enhance_prompt(prompt)