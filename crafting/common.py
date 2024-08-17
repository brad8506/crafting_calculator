"""Common functionality not related to a class."""

import logging
from typing import List, Dict, Any, Union


def find_recipe(item: str, inventory: List[Dict[str, Any]]) -> Dict[str, int]:
    """Find the first matching recipe from the inventory."""

    recipe_items: Dict[str, int] = {}

    logging.debug("Searching recipe for %s.", item)
    for recipe in inventory:
        if recipe.get("name") == item:
            recipe_items = recipe.get("items", {})
            logging.debug("Found recipe for %s.", item)
            logging.debug(recipe_items)
            break

    if not recipe_items:
        logging.debug("No recipes for %s.", item)

    return recipe_items


def get_crafting_cost(item: str, inventory: List[Dict[str, Any]]) -> Union[float, None]:
    """Get the first matching recipe crafting_cost from the inventory."""

    recipe_cost = None

    logging.debug("Getting recipe crafting_cost for %s.", item)
    for recipe in inventory:
        if recipe.get("name") == item:
            if "crafting_cost" in recipe.keys():
                recipe_cost = recipe.get("crafting_cost")
                logging.debug("Found recipe key crafting_cost for %s.", item)
            else:
                recipe_cost = 0
                logging.warning("No recipe key crafting_cost for %s.", item)
            break

    return recipe_cost

def get_crafting_cost(
    item: str, inventory: List[Dict[str, Any]], item_key: str = "crafting_cost"
) -> Union[float, None]:
    """Get the first matching recipe value from the inventory based on the provided item key."""

    recipe_value = None

    logging.debug("Getting recipe %s for %s.", item_key, item)
    for recipe in inventory:
        if recipe.get("name") == item:
            if item_key in recipe.keys():
                recipe_value = recipe.get(item_key)
                logging.debug("Found recipe key %s for %s.", item_key, item)
            else:
                recipe_value = 0
                logging.warning("No recipe key %s for %s.", item_key, item)
            break

    return recipe_value


def get_sell_to_vendor(
    item: str, inventory: List[Dict[str, Any]]
) -> Union[float, None]:
    """Get the first matching recipe sell_to_vendor from the inventory."""

    sell_to_vendor = None

    logging.debug("Getting recipe sell_to_vendor for %s.", item)
    for recipe in inventory:
        if recipe.get("name") == item:
            if "sell_to_vendor" in recipe.keys():
                sell_to_vendor = recipe.get("sell_to_vendor")
                logging.debug("Found recipe key sell_to_vendor for %s.", item)
            else:
                sell_to_vendor = 0
                logging.warning("No recipe key sell_to_vendor for %s.", item)
            break

    return sell_to_vendor

def get_buy_from_vendor(
    item: str, inventory: List[Dict[str, Any]]
) -> Union[float, None]:
    """Get the first matching recipe buy_from_vendor from the inventory."""

    buy_from_vendor = None

    logging.debug("Getting recipe buy_from_vendor for %s.", item)
    for recipe in inventory:
        if recipe.get("name") == item:
            if "buy_from_vendor" in recipe.keys():
                buy_from_vendor = recipe.get("buy_from_vendor")
                logging.debug("Found recipe key buy_from_vendor for %s.", item)
            else:
                buy_from_vendor = 0
                logging.warning("No recipe key buy_from_vendor for %s.", item)
            break

    return buy_from_vendor