"""Common functionality not related to a class."""

import logging
from typing import List, Dict, Any, Union


def find_recipe(item_name: str, inventory: Dict[str, Dict]) -> Dict[str, Dict]:
    """Find the first matching recipe from the inventory."""
    recipe = inventory.get(item_name, {})
    if not recipe:
        logging.debug("No recipe for %s.", item_name)
    return recipe

def update_amounts_recursively(details: Dict, quantity: int) -> Dict:
    if isinstance(details, Dict):
        for item_name, item_details in details.items():
            item_details['quantity'] = item_details['quantity'] * quantity
            child_items = item_details.get('items', {})
            if child_items:
                item_details['items'] = update_amounts_recursively(child_items, quantity)

    return details

def get_crafting_cost(item_name: str, inventory: Dict[str, Dict[str, Any]], item_key: str = "crafting_cost") -> Union[float, None]:
    """Get the first matching recipe value from the inventory based on the provided item key."""
    recipe_value = None

    recipe = inventory.get(item_name, None)
    if recipe:
        cost = recipe.get(item_key, None)
        if cost:
            recipe_value = cost
        else:
            # logging.warning("No recipe key %s for %s.", item_key, item)
            do_nothing = True

    return recipe_value


def get_sell_to_vendor(
    item: str, inventory: List[Dict[str, Any]]
) -> Union[float, None]:
    """Get the first matching recipe sell_to_vendor from the inventory."""
    return get_crafting_cost(item, inventory, "sell_to_vendor")


def get_buy_from_vendor(
    item: str, inventory: List[Dict[str, Any]]
) -> Union[float, None]:
    """Get the first matching recipe buy_from_vendor from the inventory."""
    return get_crafting_cost(item, inventory, "buy_from_vendor")

def process_child_items(details) -> dict:
    """
    Process the input data by adding a 'quantity' key if the value is an int,
    or converting a list into a dictionary.

    :param input_data: The dictionary or list to process.
    :param amount: The amount to set or adjust the 'quantity' key by.
    :return: The processed dictionary.
    """
    child_items = details.get('items', {})
    if child_items:
        if isinstance(child_items, list):
            # Convert list of dicts to a dict with 'name' as the key
            converted_items = {}
            for item in child_items:
                name = item.pop('name')
                converted_items[name] = item
            child_items = converted_items

        if isinstance(child_items, dict):
            # If the dict contains an int, add a 'quantity' key
            for key, value in child_items.items():
                if isinstance(value, int):
                    child_items[key] = {"quantity": value}
                elif isinstance(value, list):
                    child_items[key] = dict(value)
                #child_items[key]['quantity'] = child_items[key]['quantity'] * details['quantity']
        
        details.update({'items': child_items})

    return details