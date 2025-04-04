import os
import importlib
import sys
import traceback
from typing import Optional, Tuple

def dynamic_import(module_name: str) -> Tuple[Optional[object], Optional[str]]:
    """
    Attempts to import from expansive directory first,
    falls back to main directory if needed.
    Returns
     - The module object if successful
    - Error message if failed
    - Source directory ('expansive' or 'main') if successful
    """
    expansive_path = os.path.join('expansive', f"{module_name}.py")
    main_path = f"{module_name}.py"
    
    # Try expansive version first
    if os.path.exists(expansive_path):
        try:
            spec = importlib.util.spec_from_file_location(
                f"expansive.{module_name}", 
                expansive_path
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"expansive.{module_name}"] = module
            spec.loader.exec_module(module)
            return module, None, 'expansive'
        except Exception as e:
            error = f"Expansive version failed:\n{traceback.format_exc()}"
    
    # Fall back to main version
    if os.path.exists(main_path):
        try:
            module = importlib.import_module(module_name)
            return module, None, 'main'
        except Exception as e:
            error = (error + "\n\n" if 'error' in locals() else "") + f"Main version failed:\n{traceback.format_exc()}"
    
    return None, error or f"No {module_name}.py found in either directory", None