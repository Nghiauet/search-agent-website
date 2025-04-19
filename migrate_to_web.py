#!/usr/bin/env python3
"""
Helper script to migrate from terminal to web-based MCP Agent.
"""
import os
import sys
import shutil
from colorama import init, Fore, Style

# Initialize colorama for colored terminal output
init()

def print_header():
    """Print script header."""
    print(f"\n{Fore.BLUE}=" * 60)
    print(f"{Fore.GREEN}MCP Agent: Terminal to Web Migration Assistant{Style.RESET_ALL}")
    print(f"{Fore.BLUE}=" * 60)

def check_dependencies():
    """Check if all required dependencies are installed."""
    try:
        import aiohttp
        print(f"{Fore.GREEN}✓ aiohttp is installed{Style.RESET_ALL}")
    except ImportError:
        print(f"{Fore.RED}✗ aiohttp is not installed{Style.RESET_ALL}")
        print(f"  {Fore.YELLOW}Please install it with: pip install aiohttp{Style.RESET_ALL}")
        return False
    
    try:
        import colorama
        print(f"{Fore.GREEN}✓ colorama is installed{Style.RESET_ALL}")
    except ImportError:
        print(f"{Fore.RED}✗ colorama is not installed{Style.RESET_ALL}")
        print(f"  {Fore.YELLOW}Please install it with: pip install colorama{Style.RESET_ALL}")
        return False
    
    return True

def check_and_setup_files():
    """Check if all required files exist and set them up if needed."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check for web_app.py
    web_app_path = os.path.join(base_dir, 'web_app.py')
    if not os.path.exists(web_app_path):
        print(f"{Fore.RED}✗ web_app.py is missing{Style.RESET_ALL}")
        return False
    else:
        print(f"{Fore.GREEN}✓ web_app.py exists{Style.RESET_ALL}")
    
    # Check for static directory
    static_dir = os.path.join(base_dir, 'static')
    if not os.path.exists(static_dir):
        print(f"{Fore.YELLOW}! Creating static directory{Style.RESET_ALL}")
        os.makedirs(static_dir)
    else:
        print(f"{Fore.GREEN}✓ static directory exists{Style.RESET_ALL}")
    
    # Check for run scripts
    run_sh_path = os.path.join(base_dir, 'run_web.sh')
    run_bat_path = os.path.join(base_dir, 'run_web.bat')
    
    if not os.path.exists(run_sh_path):
        print(f"{Fore.RED}✗ run_web.sh is missing{Style.RESET_ALL}")
        return False
    else:
        print(f"{Fore.GREEN}✓ run_web.sh exists{Style.RESET_ALL}")
        # Make it executable
        os.chmod(run_sh_path, 0o755)
        print(f"{Fore.YELLOW}  Made run_web.sh executable{Style.RESET_ALL}")
    
    if not os.path.exists(run_bat_path):
        print(f"{Fore.RED}✗ run_web.bat is missing{Style.RESET_ALL}")
        return False
    else:
        print(f"{Fore.GREEN}✓ run_web.bat exists{Style.RESET_ALL}")
    
    return True

def print_instructions():
    """Print instructions for running the web app."""
    print(f"\n{Fore.BLUE}-" * 60)
    print(f"{Fore.GREEN}Ready to run the web application!{Style.RESET_ALL}")
    print(f"{Fore.BLUE}-" * 60)
    
    print(f"\n{Fore.YELLOW}To start the web application:{Style.RESET_ALL}")
    
    if sys.platform.startswith('win'):
        print(f"  {Fore.CYAN}> run_web.bat{Style.RESET_ALL}")
    else:
        print(f"  {Fore.CYAN}> ./run_web.sh{Style.RESET_ALL}")
    
    print(f"\n{Fore.YELLOW}Then open your web browser and navigate to:{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}http://localhost:8001{Style.RESET_ALL}")
    
    print(f"\n{Fore.YELLOW}For more information, see:{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}WEB_README.md{Style.RESET_ALL}")

def main():
    """Main function."""
    print_header()
    
    # Check dependencies
    print(f"\n{Fore.BLUE}Checking dependencies...{Style.RESET_ALL}")
    if not check_dependencies():
        print(f"\n{Fore.RED}Please install the missing dependencies and run this script again.{Style.RESET_ALL}")
        return
    
    # Check files
    print(f"\n{Fore.BLUE}Checking files...{Style.RESET_ALL}")
    if not check_and_setup_files():
        print(f"\n{Fore.RED}Please fix the missing files and run this script again.{Style.RESET_ALL}")
        return
    
    # Print instructions
    print_instructions()

if __name__ == "__main__":
    main()
