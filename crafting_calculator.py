#!/usr/bin/env python3
"""Calculate required base resources for crafting in games."""

import logging
import argparse

from pathlib import Path
from typing import Any, Dict, List, Tuple

# 3rd party
from yaml import safe_load

# internal
from crafting.shoppinglist import ShoppingList
from crafting.common import find_recipe
from crafting.common import get_crafting_cost

EXITCODE_NO_RECIPES = 1


def parse_arguments() -> argparse.Namespace:
    """Parse given command line arguments."""
    parser = argparse.ArgumentParser(
        allow_abbrev=False, formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    calculation = parser.add_argument_group("crafting options")
    verbosity = parser.add_argument_group("verbosity options")
    export = parser.add_argument_group("export options")

    verbosity.add_argument(
        "--debug",
        "-d",
        default=False,
        action="store_true",
        help="enable debug logging with timestamps",
    )
    verbosity.add_argument(
        "--verbose",
        "-v",
        default=False,
        action="store_true",
        help="enable verbose output",
    )

    export.add_argument(
        "--as-json",
        action="store_true",
        default=False,
        help="return a JSON string instead of a user-friendly message",
    )

    calculation.add_argument("item", type=str, help="the item you want to craft")

    calculation.add_argument(
        "--amount",
        type=int,
        default=1,
        help="craft this amount of the item",
        required=False,
    )
    calculation.add_argument(
        "--game",
        help="load recipes for this game from the recipes folder (e.g. yonder)",
        required=True,
    )

    options = parser.parse_args()
    return options


def setup_logging(debug: bool, verbose: bool) -> None:
    """Create a logging configuration according to given flags."""
    if debug:
        logging.basicConfig(
            format="%(asctime)s %(levelname)s: %(message)s", level=logging.DEBUG
        )
        logging.debug("Debug logging enabled.")
    elif verbose:
        logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)
    else:
        logging.basicConfig(format="%(levelname)s: %(message)s")


def load_recipes(game: str) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    """Helper to load content from files for a specific game."""
    path = Path(f"recipes/{game}")
    content_list = []
    for entry in path.rglob("*.yml"):
        raw_content = entry.read_text()
        content = safe_load(raw_content)
        if content:
            content_list.extend(content)

    inventory, meta = load_recipes_from_content(content_list)
    return (inventory, meta)


def load_recipes_from_content(
    content_list: List[Dict[str, Any]]
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    # Loop through the content and add each item to the inventory, keyed by the "name" key
    inventory = {}
    meta = {}

    for item in content_list:
        if isinstance(item, dict) and "name" in item:
            recipe_name = item["name"]
            inventory[recipe_name] = item
        elif isinstance(item, list) and "name" in item:
            recipe_name = item["name"]
            inventory[recipe_name] = dict(item)
        else:
            # Optionally handle cases where item is not a dictionary or doesn't have a "name" key
            print(f"Skipping item: {item}, missing 'name' key")

    # Loop through inventory and fix child items that are using list type
    for item_name, details in inventory.items():
        if item_name == "Plasma Launcher":
            debug = True
        details["quantity"] = details.get("quantity", 1)
        child_items = details.get("items", None)
        if child_items:
            if isinstance(child_items, list):
                new_child_items = {}
                for values in child_items:
                    child_name = values.get("name")
                    new_child_items[child_name] = values
                child_items = new_child_items
            for child_item_name, child_details in child_items.items():
                if isinstance(child_details, int):
                    # child_items[child_item_name] = {'name': child_item_name, 'quantity': child_details}
                    dict_child_details = {
                        "name": child_item_name,
                        "quantity": child_details * details["quantity"],
                    }
                    child_items[child_item_name] = dict_child_details
                if isinstance(child_items, dict):
                    debug = True

    sum_recipes = len(inventory)
    if sum_recipes:
        logging.info(
            "Loaded a total of %s recipes for %s.", sum_recipes, meta.get("title")
        )
    else:
        logging.info("No recipes detected for %s.", meta.get("title"))

    if not inventory:
        logging.error("No recipes were detected for %s.", meta.get("title"))
        raise RuntimeWarning("No recipes detected.")

    return (inventory, meta)


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
        if item_name in ("Armor Plate"):
            debug = True
        if item_name in ("Plasma Launcher"):
            debug = True
        if item_name in ("Steroid Implant"):
            debug = True
        if item_name in ("Vital Nano Bracer"):
            debug = True
        if item_name in (
            "Vital Nano Bracer",
            "Bio-compatible Material",
            "Xiphoid Process",
            "Steroid Implant",
        ):
            debug = True
        add_recipe_details_recursive(item_name, details, inventory, recursive_inventory)
        debug = True
    recursive_inventory = {
        key: recursive_inventory[key] for key in sorted(recursive_inventory)
    }

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


def convert_item(item_name: str, item, inventory: dict):
    if isinstance(item, int):
        # If item is an integer, convert it to a dictionary.
        item = {"name": item_name}
    if isinstance(item, list):
        # If item is an integer, convert it to a dictionary.
        item = dict(item)

    if "items" in item and isinstance(item["items"], list):
        new_child_details = {}
        for child_details in item["items"]:
            name = child_details["name"]
            child_defaults = {"name": item_name, "quantity": item.get("quantity", 1)}
            recipe = inventory.get(name, {})
            new_child_details[name] = {**child_defaults, **recipe, **child_details}
        item["items"] = new_child_details

    recipe = inventory.get(item_name, {})
    defaults = {"name": item_name, "quantity": item.get("quantity", 1)}
    item = {**defaults, **recipe, **item}
    return item  # Return the item as is if it's not an integer


def add_recipe_details_recursive(
    item_name: str, item_details: dict, inventory: dict, final_inventory
):
    """
    Recursively adds item details into the parent_dict.

    Args:
        item (dict): The current item details.
        parent_dict (dict): The dictionary to accumulate the details.
    """

    if item_name == "Armor Plate":
        debug = True

    item_details = convert_item(item_name, item_details, inventory)
    item_quantity = item_details.get("quantity")
    # Recurse if there are child items
    child_name = ""
    child_details = {}
    for child_name, child_details in item_details.get("items", {}).items():
        child_details = convert_item(child_name, child_details, inventory)
        # child_details['quantity'] = child_details['quantity'] * item_quantity
        child_details_new = add_recipe_details_recursive(
            child_name, child_details, inventory, item_details["items"]
        )
        item_details["items"] = child_details_new

    final_inventory[item_name] = item_details

    return final_inventory


def craft_item(item: str, inventory: List[Dict[str, Any]], amount: int) -> ShoppingList:
    """Calculate the items required to craft a recipe."""
    shopping_list = ShoppingList(inventory, item, amount)
    required_items = find_recipe(item, inventory)
    shopping_list.add_items(required_items, amount)
    shopping_list.simplify()

    # shopping_list.add_item_costs(shopping_list.intermediate_steps)
    shopping_list.crafting_cost.update(
        {item: get_crafting_cost(item, inventory) * amount}
    )

    for recipe in inventory:
        if recipe.get("name") == item:
            if "sell_to_vendor" in recipe.keys():
                shopping_list.sell_to_vendor = recipe.get("sell_to_vendor")

            else:
                logging.warning("No sell_to_vendor property for %s.", item)

    return shopping_list


def main() -> None:
    """Break a recipe down into its base components and create a shopping list."""
    options = parse_arguments()
    setup_logging(options.debug, options.verbose)

    try:
        inventory, meta = load_recipes(options.game)
    except RuntimeWarning as error:
        if str(error.args) == "No recipes detected.":
            raise SystemExit(EXITCODE_NO_RECIPES)

    shopping_list = craft_item(options.item, inventory, options.amount)

    if options.as_json:
        print(shopping_list.to_json())
    else:
        print(shopping_list.format_for_text_display())


if __name__ == "__main__":
    main()
