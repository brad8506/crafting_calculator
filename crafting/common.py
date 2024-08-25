"""Common functionality not related to a class."""

import logging
from typing import List, Dict, Any, Union


def find_recipe(item: str, inventory: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
    """Find the first matching recipe from the inventory."""

    recipe_items = inventory.get(item, {})

    # logging.debug("Searching recipe for %s.", item)
    # for recipe in inventory:
    #     if recipe.get("name") == item:
    #         recipe_items = recipe.get("items", {})
    #         logging.debug("Found recipe for %s.", item)
    #         logging.debug(recipe_items)
    #         break

    # if not recipe_items:
    #     logging.debug("No recipes for %s.", item)

    return recipe_items


def get_crafting_cost(
    item: str, inventory: Dict[str, Dict[str, Any]], item_key: str = "crafting_cost"
) -> Union[float, None]:
    """Get the first matching recipe value from the inventory based on the provided item key."""
    recipe_value = None

    recipe = inventory.get(item, None)
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
