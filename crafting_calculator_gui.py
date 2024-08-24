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
    if games[0]:
        inventory, meta = _load_recipes(games[0])
        # items = sorted(get_inventory_values(inventory, "name"))
        items = sorted(list(inventory.keys()))

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
        ],
        [
            sg.Text("Search:", size=(6, 1)),
            sg.InputText(key="search", size=(40, 1), enable_events=True),
        ],
        [
            sg.Text("Item:", size=(6, 1)),
            sg.Listbox(
                items,
                key="item",
                select_mode="extended",
                size=(40, 10),
                enable_events=False,
            ),
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
        [sg.Text("Output:", size=(6, 1))],
        [sg.Multiline(size=(100, 20), key="output", enable_events=True)],
    ]
    return sg.Window("Crafting Calculator", layout, resizable=True)


def main():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    logging.debug(dir_path)

    window = windowPySimpleGui()

    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()

        output_element = window["output"]

        # if user closes window or clicks cancel
        if event in (sg.WIN_CLOSED, "Cancel"):
            break

        if event == "game":
            output(output_element, "")
            inventory, meta = _load_recipes(values["game"])
            items = sorted(inventory.keys())
            window["item"].update(items)

        if event in ("search", "search_button"):
            search_query = values.get("search", "").lower()
            inventory, meta = _load_recipes(values["game"])
            items = sorted(inventory.keys())
            filtered_items = [item for item in items if search_query in item.lower()]
            window["item"].update(filtered_items)

        if event == "calculate":
            items = values["item"]
            if not items:
                output(output_element, "Please select an item")
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
                    #shopping_list.add_items({item: target_item}, amount)
                    required_items = target_item.get('items', None)
                    if required_items:
                        shopping_list.add_items(required_items, amount)

                shopping_list.simplify()
                shopping_list.calculate_crafting_costs()
                shopping_list.calculate_buy_from_vendor()
                shopping_list.calculate_sell_to_vendor()
                output(output_element, shopping_list.format_for_display())

        if event == "clear_items":
            window["item"].set_value([])

    window.close()


def output(element, string, append=False):
    element.Update(disabled=False)
    element.Update(string, append=append)
    element.Update(disabled=True)


if __name__ == "__main__":
    main()
