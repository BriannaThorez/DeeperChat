import ast
import subprocess
import difflib
import os
import re
from typing import Optional, Tuple, List, Dict

def detect_and_read_python_files(prompt: str) -> Tuple[str, bool]:
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

def enhance_prompt(prompt: str) -> str:
    """
    Main function to enhance prompts with additional context
    Only looks for files in the 'expansive' directory
    Handles module edit requests.
    """
    # Check for edit command pattern
    edit_pattern = r"\[EDIT_MODULE (\w+\.py)\](.*?)(?=\n\[|\Z)"
    edit_matches = re.findall(edit_pattern, prompt, re.DOTALL)
    
    if edit_matches:
        for module_name, edit_instructions in edit_matches:
            edit_result = edit_module(module_name, edit_instructions, prompt)
            if edit_result['status'] == 'success':
                prompt += f"\n\n[System] Module {module_name} was successfully edited."
            else:
                prompt += f"\n\n[System] Edit failed: {edit_result['message']}"
    
    # Original file detection functionality
    enhanced_prompt, files_found = detect_and_read_python_files(prompt)
    
    if files_found:
        print("\n[System] Detected and included Python file(s) from expansive directory")
    
    return enhanced_prompt