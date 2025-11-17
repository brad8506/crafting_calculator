# crafting_calculator_gui_html_server.py

A HTML server for crafting recipes with expand/collapse and simple text export.

Run build\exe.win-amd64-3.11\crafting_calculator_gui_html_server.exe
Visit http://localhost:8000/

GUI
<img src="./images/gui.png">

Expand/Collapse
<img src="./images/expand-collapse.png">

Simple text output
<img src="./images/simple-text-output.png">

## build executable
Update CHANGELOG.md
Increment setup.py APP_VERSION
pip install cx_Freeze
python setup.py build

Outputs to ./build directory

# History
The original crafting_calculator.py was done by Stephen Voss https://github.com/GhostLyrics/crafting_calculator
