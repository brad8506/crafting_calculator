from cx_Freeze import setup, Executable

# Dependencies for your application
build_exe_options = {
    "packages": ["os"],
    # "excludes": ["tkinter"],
}

# Base "Console" or "Win32GUI" for GUI applications
base = "Win32GUI"

setup(
    name="CraftingCalculatorGui",
    version="1.0",
    description="Cross-game compatible. Break down crafting recipes into raw and intermediate components",
    options={"build_exe": build_exe_options},
    executables=[Executable("crafting_calculator_gui.py", base=base)],
)
