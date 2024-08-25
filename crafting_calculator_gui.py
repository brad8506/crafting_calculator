#!/usr/bin/env python3
"""GUI to calculate required base resources for crafting in games."""

from pathlib import Path
from string import Template
from typing import Any, Dict, Tuple
import logging
import os
import subprocess
import PySimpleGUI as sg

# 3rd party
from yaml import safe_load

# internal
from crafting_calculator import load_recipes
from crafting.shoppinglist import ShoppingList
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

def get_inventory_values(inventory, key):
    return_array = []
    for item in inventory:
        return_array.append(item.get(key))
    return return_array


def windowPySimpleGui():
    games = discover_games()
    listCraftable = {}
    listGatherable = {}
    if games[0]:
        inventory, meta = _load_recipes(games[0])
        listCraftable, listGatherable  = process_inventory(inventory)
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
            sg.Button("Reload recipes", key="reload_recipes")
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
            sg.Multiline(size=(40, 21), key="gatherable_output", enable_events=True, default_text=gatherable_list_formatted),
        ],
        [
            sg.Text("Amount:", size=(6, 1)),
            sg.InputText(key="amount", default_text="1", size=(40, 1)),
        ],
        [
            sg.Text("", size=(5, 1)),
            sg.Column([
                [sg.Button("Calculate", key="calculate", size=(15, 1))]
            ]),
            sg.Column([
                [sg.Button("Clear selected items", key="clear_items")]
            ]),
        ],
        [
            sg.Text(
                "Tip: Use Ctrl+MouseClick to select or deselect multiple items.",
                size=(49, 1),
            )
        ],
        [
            sg.Text("Output:", size=(6, 1)),
            sg.Multiline(size=(84, 20), key="craftable_output", enable_events=True)
        ]
    ]
    return sg.Window("Crafting Calculator", layout, finalize=True)

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
    # Initialize dictionaries for item classification
    listCraftable = {}
    listGatherable = {}

    # Classify items into craftable and gatherable
    for item_name, details in inventory.items():
        hasChildItems = details.get('items', None)
        if hasChildItems:
            listCraftable[item_name] = item_name
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
        gatherable_list.add_items({item_name: details}, 1)
    return gatherable_list

def main():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    logging.debug(dir_path)

    window = windowPySimpleGui()

    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()

        craftable_output = window["craftable_output"]

        # if user closes window or clicks cancel
        if event in (sg.WIN_CLOSED, "Cancel"):
            break

        if event in ('game', 'reload_recipes'):
            output(craftable_output, "")
            inventory, meta = _load_recipes(values["game"])
            listCraftable, listGatherable  = process_inventory(inventory)
            
            window["craftable_item"].update(listCraftable)
            
            gatherable_list = get_gatherable_list(listGatherable)
            output(window["gatherable_output"], gatherable_list.format_recipes_for_text_display())

        if event in ("craftable_search"):
            craftable_search_string = values.get("craftable_search", "").lower()
            inventory, meta = _load_recipes(values["game"])
            listCraftable, listGatherable  = process_inventory(inventory)
            filtered_items = [item for item in listCraftable if craftable_search_string in item.lower()]
            window["craftable_item"].update(filtered_items)

        if event in ("gatherable_search"):
            gatherable_search_string = values.get("gatherable_search", "").lower()
            inventory, meta = _load_recipes(values["game"])
            listCraftable, listGatherable  = process_inventory(inventory)
            gatherable_list = get_gatherable_list(listGatherable)

            items_to_delete = {}
            for item_name, details in gatherable_list.items.items():
                if not gatherable_search_string in item_name.lower():
                    items_to_delete[item_name] = item_name

            for item_to_delete in items_to_delete:
                del gatherable_list.items[item_to_delete]
            
            output(window["gatherable_output"], gatherable_list.format_recipes_for_text_display())

        if event == "calculate":
            items = values["craftable_item"]
            if not items:
                output(craftable_output, "Please select an item")
            else:
                game = values["game"]
                amount = int(values["amount"] or 1)
                shopping_list = ShoppingList.create_empty()
                inventory, meta = _load_recipes(values["game"])

                # Sort inventory dictionary alphabetically
                inventory = {key: inventory[key] for key in sorted(inventory)}

                temp_items = {}
                for item in items:
                    temp_items[item] = inventory.get(item)
                items = temp_items

                shopping_list.inventory = inventory
                shopping_list.target_amount = amount
                for item in items:
                    target_item = inventory.get(item)
                    target_item['quantity'] = amount
                    shopping_list.target_items.update({item: target_item})
                    shopping_list.add_items({item: target_item}, 1)

                shopping_list.simplify()
                shopping_list.calculate_crafting_costs()
                shopping_list.calculate_buy_from_vendor()
                shopping_list.calculate_sell_to_vendor()
                output(craftable_output, shopping_list.format_for_text_display())

        if event == "clear_items":
            window["craftable_item"].set_value([])

    window.close()


def output(element, string, append=False):
    element.Update(disabled=False)
    element.Update(string, append=append)
    element.Update(disabled=True)


if __name__ == "__main__":
    main()
