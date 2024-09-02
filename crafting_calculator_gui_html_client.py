#!/usr/bin/env python3
"""GUI to calculate required base resources for crafting in games."""

from pathlib import Path
from string import Template
from typing import Any, Dict, Tuple
import logging
import webbrowser
import os
import subprocess

# 3rd party
from yaml import safe_load

# internal
from crafting_calculator import *
from crafting.shoppinglist import *
from crafting.common import *

def discover_games() -> Tuple[Dict[str, Any]]:
    games = []
    path = Path("recipes")
    for entry in path.rglob("**/meta.yml"):
        raw_content = entry.read_text()
        content = safe_load(raw_content)
        if content:
            if content.get("title"):
                games.append(entry.parent.name)

    return games

def _load_recipes(game):
    inventory, meta = load_recipes(game)
    return (inventory, meta)

def windowPySimpleGui():
    games = discover_games()
    listCraftable = {}
    listGatherable = {}
    if games[0]:
        inventory, meta = _load_recipes(games[0])
        listCraftable, listGatherable = process_inventory(inventory)
        listCraftableItems = sorted(list(listCraftable.keys()))
        gatherable_list = get_gatherable_list(listGatherable)
        gatherable_list_formatted = gatherable_list.format_recipes_for_text_display()

    layout = [
        [
            sg.Text("Game:", size=(6, 1)),
            sg.Combo(
                games,
                default_value=games[0],
                key="game",
                size=(40, 1),
                enable_events=True,
            ),
            sg.Button("Reload recipes", key="reload_recipes"),
        ],
        [
            sg.Text("", size=(6, 1)),
            sg.Text("Craftable Search:", size=(15, 1)),
            sg.Text("", size=(20, 1)),
            sg.Text("Gatherable Search:", size=(15, 1)),
        ],
        [
            sg.Text("", size=(6, 1)),
            sg.InputText(key="craftable_search", size=(40, 1), enable_events=True),
            sg.Text("", size=(0, 1)),
            sg.InputText(key="gatherable_search", size=(40, 1), enable_events=True),
        ],
        [
            sg.Text("", size=(6, 1)),
            sg.Text("Craftable Items:", size=(15, 1)),
            sg.Text("", size=(20, 1)),
            sg.Text("Gatherable Items:", size=(15, 1)),
        ],
        [
            sg.Text("", size=(6, 1)),
            sg.Listbox(
                listCraftableItems,
                key="craftable_item",
                select_mode="extended",
                size=(40, 20),
                enable_events=False,
            ),
            sg.Multiline(
                size=(40, 21),
                key="gatherable_output",
                enable_events=True,
                default_text=gatherable_list_formatted,
            ),
        ],
        [
            sg.Text("Amount:", size=(6, 1)),
            sg.InputText(key="amount", default_text="1", size=(40, 1)),
        ],
        [
            sg.Text("", size=(5, 1)),
            sg.Column([[sg.Button("Calculate", key="calculate", size=(15, 1))]]),
            sg.Column([[sg.Button("Clear selected items", key="clear_items")]]),
        ],
        [
            sg.Text(
                "Tip: Use Ctrl+MouseClick to select or deselect multiple items.",
                size=(49, 1),
            )
        ],
        [
            sg.Text("Output:", size=(6, 1)),
            sg.Multiline(size=(84, 20), key="craftable_output", enable_events=True),
        ],
    ]
    return sg.Window("Crafting Calculator", layout, location=(500, 200), finalize=True)


def process_inventory(inventory):
    """
    Process the inventory to classify items into craftable and gatherable lists,
    and return the combined and sorted lists.

    Args:
        inventory (dict): The inventory dictionary.

    Returns:
        tuple: A tuple containing:
            - combined_list (dict): Combined list of craftable and gatherable items with headers.
            - labels (list): List of item labels.
    """
    
    recursive_inventory = {}
    for item_name, details in inventory.items():
        if item_name in ('Vital Nano Bracer'):
            debug = True
        if item_name in ('Vital Nano Bracer', 'Bio-compatible Material', 'Xiphoid Process', 'Steroid Implant'):
            debug = True
        add_recipe_details_recursive(item_name, details, inventory, recursive_inventory)
        debug = True
    recursive_inventory = {key: recursive_inventory[key] for key in sorted(recursive_inventory)}


    # Initialize dictionaries for item classification
    listCraftable = {}
    listGatherable = {}

    # Classify items into craftable and gatherable
    for item_name, details in recursive_inventory.items():
        hasChildItems = details.get("items", {})
        if hasChildItems:
            listCraftable[item_name] = details
        else:
            listGatherable[item_name] = details

    # Sort items within each category
    listCraftable = {key: listCraftable[key] for key in sorted(listCraftable)}
    listGatherable = {key: listGatherable[key] for key in sorted(listGatherable)}

    return listCraftable, listGatherable

def get_gatherable_list(listGatherable) -> ShoppingList:
    gatherable_list = ShoppingList.create_empty()
    gatherable_list.inventory = listGatherable
    for item_name, details in listGatherable.items():
        details["quantity"] = details.get("quantity", 1)
    gatherable_list.items = listGatherable
    return gatherable_list


def main():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    logging.debug(dir_path)

    window = windowPySimpleGui()

    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, window_values = window.read()

        # craftable_output = window["craftable_output"]

        # if user closes window or clicks cancel
        if event in (sg.WIN_CLOSED, "Cancel"):
            break

        if event in ("game", "reload_recipes"):
            # output(craftable_output, "")
            inventory, meta = _load_recipes(window_values["game"])
            listCraftable, listGatherable = process_inventory(inventory)

            window["craftable_item"].update(listCraftable)

            gatherable_list = get_gatherable_list(listGatherable)
            # output(
            #     window["gatherable_output"],
            #     gatherable_list.format_recipes_for_text_display(),
            # )

        if event in ("craftable_search"):
            craftable_search_string = window_values.get("craftable_search", "").lower()
            inventory, meta = _load_recipes(window_values["game"])
            listCraftable, listGatherable = process_inventory(inventory)
            filtered_items = [
                item
                for item in listCraftable
                if craftable_search_string in item.lower()
            ]
            window["craftable_item"].update(filtered_items)

        if event in ("gatherable_search"):
            gatherable_search_string = window_values.get(
                "gatherable_search", ""
            ).lower()
            inventory, meta = _load_recipes(window_values["game"])
            listCraftable, listGatherable = process_inventory(inventory)
            gatherable_list = get_gatherable_list(listGatherable)

            items_to_delete = {}
            for item_name, details in gatherable_list.items.items():
                if not gatherable_search_string in item_name.lower():
                    items_to_delete[item_name] = item_name

            for item_to_delete in items_to_delete:
                del gatherable_list.items[item_to_delete]

            # output(
            #     window["gatherable_output"],
            #     gatherable_list.format_recipes_for_text_display(),
            # )

        if event == "calculate":
            items = window_values["craftable_item"]
            if not items:
                # output(craftable_output, "Please select an item")
                debug = True
            else:
                game = window_values["game"]
                amount = int(window_values["amount"] or 1)
                shopping_list = ShoppingList.create_empty()
                inventory, meta = _load_recipes(window_values["game"])
                listCraftable, listGatherable = process_inventory(inventory)

                target_items = {}
                for item_name in items:
                    target_items[item_name] = inventory.get(item_name)
                    target_items[item_name]["quantity"] = (
                        target_items[item_name].get("quantity", 1) * amount
                    )
                del items
                del item_name

                # Sort inventory dictionary alphabetically
                shopping_list.inventory = {
                    key: inventory[key] for key in sorted(inventory)
                }
                del inventory

                shopping_list.target_amount = amount
                del amount

                shopping_list.target_items.update(target_items)
                shopping_list.items.update(target_items)
                del target_items
                # shopping_list.simplify()
                shopping_list.simplifyV2()
                shopping_list.format_for_html_display()

        if event == "clear_items":
            window["craftable_item"].set_value([])

    window.close()

def generate_html_content(data):
    """
    Generate a simple HTML page as a string with embedded JavaScript for AJAX updates.
    :param data: The initial data to be included in the HTML.
    :return: A string containing the HTML content with AJAX functionality.
    """
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Data Output</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #dddddd; text-align: left; padding: 8px; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
        </style>
        <script>
            function updateContent() {{
                // Example AJAX call to get new data
                fetch('data.json')
                    .then(response => response.json())
                    .then(data => {{
                        // Find the table body element
                        const tableBody = document.getElementById('data-table-body');

                        // Clear existing content
                        tableBody.innerHTML = '';

                        // Populate table with new data
                        for (const [key, value] of Object.entries(data)) {{
                            const row = `<tr><td>{{key}}</td><td>{{value}}</td></tr>`;
                            tableBody.insertAdjacentHTML('beforeend', row);
                        }}
                    }})
                    .catch(error => console.error('Error fetching data:', error));
            }}

            // Update content every 5 seconds
            setInterval(updateContent, 5000);
        </script>
    </head>
    <body>
        <h1>Data Output</h1>
        <button onclick="updateContent()">Update Now</button>
        <table>
            <thead>
                <tr>
                    <th>Key</th>
                    <th>Value</th>
                </tr>
            </thead>
            <tbody id="data-table-body">
    """

    # Populate initial data into the table
    for key, value in data.items():
        html_content += f"""
                <tr>
                    <td>{key}</td>
                    <td>{value}</td>
                </tr>
        """

    html_content += """
            </tbody>
        </table>
    </body>
    </html>
    """

    return html_content

def save_html_to_file(html_content, filename="output.html"):
    """
    Save the HTML content to a file.
    :param html_content: The HTML content to be saved.
    :param filename: The filename for the HTML file.
    """
    with open(filename, "w") as file:
        file.write(html_content)

def display_html_in_browser(filename="output.html"):
    """
    Open the HTML file in the default web browser.
    :param filename: The filename of the HTML file to be displayed.
    """
    # Make sure the file path is absolute
    filepath = os.path.abspath(filename)
    webbrowser.open(f"file://{filepath}")

if __name__ == "__main__":
    # Example data
    data = {
        "Item 1": "Value 1",
        "Item 2": "Value 2",
        "Item 3": "Value 3",
    }
    
    # Generate the HTML content
    html_content = generate_html_content(data)
    
    # Save the content to an HTML file
    save_html_to_file(html_content)
    
    # Display the file in the default web browser
    display_html_in_browser()
