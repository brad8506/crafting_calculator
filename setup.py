from cx_Freeze import setup, Executable
import os

# Directory containing your assets
web_dir = os.path.join(os.path.dirname(__file__), 'web')
recipes_dir = os.path.join(os.path.dirname(__file__), 'recipes')

# Options for cx_Freeze
build_exe_options = {
    'packages': [],  # Include any additional packages you might need
    'excludes': [],
    'include_files': [
        (web_dir, 'web'),   # Include the 'web' folder
        (recipes_dir, 'recipes')  # Include the 'recipes' folder
    ],
    'optimize': 2
}

# Base 'Win32GUI' is used for Windows applications without a console
# Change to None for console applications
base = None

setup(
    name="Crafting Calculator GUI Server",
    version="1.0",
    description="A GUI server for the crafting calculator",
    options={"build_exe": build_exe_options},
    executables=[Executable("crafting_calculator_gui_html_server.py", base=base)],
)