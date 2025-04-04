import os
import platform
def increase_terminal_buffer():
    """Increase terminal buffer size based on OS"""
    system = platform.system()
    
    try:
        if system == "Windows":
            # Windows - using mode command
            os.system('mode con: lines=10000')
        elif system == "Linux" or system == "Darwin":  # Darwin = macOS
            # Unix-like systems - using stty and resize
            os.system('stty rows 10000')
            # Try resize if available (for terminal emulators)
            #os.system('resize -s 10000> /dev/null 2>&1')
        else:
            print(f"Unsupported OS: {system}. Terminal buffer not adjusted.")
    except Exception as e:
        print(f"Failed to adjust terminal buffer: {str(e)}")
