# utilities/setup_config.py
import json
import os
from typing import Dict, Optional

DEFAULT_CONFIG = {
    "deepseek_api_key": "",
    "user_name": ""
}

def validate_api_key(api_key: str) -> bool:
    """Validate the format of a DeepSeek API key"""
    return api_key.startswith("sk-") and len(api_key) > 30

def validate_username(username: str) -> bool:
    """Validate the username meets basic requirements"""
    return 2 <= len(username.strip()) <= 30

def prompt_for_username(current_name: Optional[str] = None) -> str:
    """Interactive prompt to get a valid username"""
    print("\n👤 User Identification")
    print("---------------------")
    
    if current_name:
        print(f"Current username: {current_name}")
        print("(Leave blank to keep current)")
    
    while True:
        username = input("Enter your name/identifier (2-30 chars): ").strip()
        
        if current_name and not username:
            return current_name
            
        if validate_username(username):
            return username
            
        print("⚠️ Username must be between 2-30 characters")

def prompt_for_api_key(current_key: Optional[str] = None) -> str:
    """Interactive prompt to get a valid API key"""
    print("\n🔑 DeepSeek API Key Setup:")
    print("1. Get your API key from https://platform.deepseek.com")
    print("2. Paste it below (it will be saved locally)")
    
    if current_key:
        print(f"(Leave blank to keep current key)")
    
    while True:
        api_key = input("Enter your DeepSeek API key (starts with 'sk-'): ").strip()
        
        if current_key and not api_key:
            return current_key
            
        if validate_api_key(api_key):
            return api_key
            
        print("⚠️ Invalid API key format. Should start with 'sk-' and be >30 characters")

def prompt_for_config(current_config: Optional[Dict] = None) -> Dict:
    """Interactive prompt to gather complete configuration"""
    config = current_config.copy() if current_config else DEFAULT_CONFIG.copy()
    
    config['user_name'] = prompt_for_username(config.get('user_name'))
    config['deepseek_api_key'] = prompt_for_api_key(config.get('deepseek_api_key'))
    
    return config

def save_config(config: Dict, config_path: str = 'config.json') -> bool:
    """Save configuration to file"""
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Could not save config: {e}")
        return False

def load_config(config_path: str = 'config.json') -> Dict:
    """Load configuration from file or return empty dict if invalid"""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            # Validate basic structure
            if isinstance(config, dict):
                return config
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return {}

def ensure_config(config_path: str = 'config.json') -> Dict:
    """
    Public interface - ensures valid config exists
    Returns validated configuration dictionary
    """
    # Load existing config if available
    config = load_config(config_path)
    
    # Check if we need to prompt for any missing/invalid values
    needs_update = False
    
    if not validate_username(config.get('user_name', '')):
        config = prompt_for_config(config)
        needs_update = True
    elif not validate_api_key(config.get('deepseek_api_key', '')):
        print("\n⚠️ API key validation failed")
        config = prompt_for_config(config)
        needs_update = True
    
    # Save if we made changes
    if needs_update:
        if save_config(config, config_path):
            print("✅ Configuration updated successfully")
        else:
            print("⚠️ Could not save configuration changes")
    
    return config