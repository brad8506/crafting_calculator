from cx_Freeze import setup, Executable
import os
import platform
import sys


# Version of the application
APP_VERSION = "1.1"

# PYTHON_VERSION = sys.version_info
PYTHON_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

# Get architecture (either 32-bit or 64-bit)
ARCHITECTURE = platform.architecture()[0]

# Directory containing your assets
web_dir = os.path.join(os.path.dirname(__file__), "web")
crafting_dir = os.path.join(os.path.dirname(__file__), "crafting")
recipes_dir = os.path.join(os.path.dirname(__file__), "recipes")
js_dir = os.path.join(os.path.dirname(__file__), "js")

# Options for cx_Freeze
build_exe_options = {
    "packages": [],  # Include any additional packages you might need
    "excludes": [],
    "include_files": [
        (web_dir, "web"),  # Include the 'web' folder
        (crafting_dir, "crafting"),  # Include the 'web' folder
        (recipes_dir, "recipes"),  # Include the 'recipes' folder
        (js_dir, "js"),  # Include the 'recipes' folder
    ],
    "optimize": 2,
    "build_exe": f"build/exe.win-amd{ARCHITECTURE}-{PYTHON_VERSION}/{APP_VERSION}",  # Dynamic output path
}

# Base 'Win32GUI' is used for Windows applications without a console
# Change to None for console applications
base = None

setup(
    name="Crafting Calculator GUI Server",
    version=APP_VERSION,
    description="A GUI server for the crafting calculator",
    options={"build_exe": build_exe_options},
    executables=[Executable("crafting_calculator_gui_html_server.py", base=base)],
)
