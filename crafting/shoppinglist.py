"""Shopping List class to hold all required items."""

import logging
from json import dumps
from typing import List, Dict, Any

# 3rd party
from yaml import safe_dump

# internal
import crafting.common
from crafting.common import *


# Singleton class
class ShoppingList:
    """A shopping list holds all items required to craft the given item."""

    def __init__(
        self, inventory: Dict[str, Dict[str, Any]], items: Dict[str, Any], amount: int
    ):
        self.items: Dict[str, Any] = {}
        self.crafting_cost: float = 0.0
        self.target_items: Dict[str, Any] = {}
        self.target_amount: int = amount
        self.intermediate_steps: Dict[str, Any] = {}
        self.inventory = inventory

    @classmethod
    def create_empty(cls):
        inventory = {}
        items = {}
        amount = 0  # Default amount
        return cls(inventory, items, amount)

    def calculate_crafting_costs(self) -> None:
        """Calculate all costs."""
        for item_name, details in self.items.items():
            recipe_cost = get_crafting_cost(item_name, self.inventory)
            if recipe_cost is not None:
                self.crafting_cost = self.crafting_cost + (
                    recipe_cost * details.get("quantity")
                )

        for item_name, details in self.intermediate_steps.items():
            recipe_cost = get_crafting_cost(item_name, self.inventory)
            if recipe_cost is not None:
                self.crafting_cost = self.crafting_cost + (
                    recipe_cost * details.get("quantity")
                )
            logging.debug(
                "Summing item crafting_cost for %s item/s in shopping list.", item_name
            )

    def calculate_buy_from_vendor(self) -> Dict[str, float]:
        """Calculate the cost to buy each item from vendors and return a dictionary."""
        buy_from_vendor = 0.0

        # Process items
        for item, details in self.items.items():
            buy_cost = get_buy_from_vendor(item, self.inventory)
            if buy_cost is not None:
                buy_from_vendor += buy_cost * details.get("quantity")

        # Process intermediate steps
        for item, details in self.intermediate_steps.items():
            buy_cost = get_buy_from_vendor(item, self.inventory)
            if buy_cost is not None:
                amount = details.get("quantity", 1)
                buy_from_vendor += buy_cost * details.get("quantity")

        logging.debug("Buy from vendor costs: %s", buy_from_vendor)

        self.buy_from_vendor = buy_from_vendor
        return buy_from_vendor

    def calculate_sell_to_vendor(self) -> None:
        """Calculate the total revenue from selling items to vendors."""
        self.sell_to_vendor = 0.0  # Initialize as a float

        # Process target items
        for item in self.target_items:
            sell_cost = get_sell_to_vendor(item, self.inventory)
            if sell_cost is not None:
                self.sell_to_vendor += sell_cost * self.target_amount

        logging.debug("Total sell_to_vendor revenue: %s", self.sell_to_vendor)

    def simplify(self) -> None:
        """Recursively replace intermediate crafted items with their components."""
        logging.info("Simplifying shopping list.")

        items_to_add = {}
        items_to_remove = []

        # Collect items to be added or removed
        for item_name, details in self.items.items():
            recipe = self.inventory.get(item_name, None)
            if recipe:
                if isinstance(details, dict):
                    details = recipe | details

                child_items = details.get("items", {})
                if child_items:
                    # if item_name not in self.target_items:
                    self.intermediate_steps.update({item_name: details})
                    items_to_remove.append(item_name)  # Mark item for removal

                    for child_name, child_details in child_items.items():
                        new_child_details = {}
                        if isinstance(child_details, int):
                            new_child_details = {
                                "name": child_name,
                                "quantity": child_details,
                            }
                            child_recipe = self.inventory.get(child_name, None)
                            if child_recipe:
                                new_child_details = child_recipe | new_child_details
                        else:
                            new_child_details = child_details
                        items_to_add[
                            child_name
                        ] = new_child_details  # Mark item for addition

        # Apply the changes
        for item_name in items_to_remove:
            del self.items[item_name]

        self.items.update(items_to_add)

        # Recursively simplify if there were changes
        if items_to_add or items_to_remove:
            self.simplify()
        else:
            logging.info("Nothing to simplify.")

    def to_yaml(self) -> str:
        """Return ShoppingList contents as YAML formatted string."""
        prepared_string: str = safe_dump(
            self.items, default_flow_style=False, sort_keys=True
        )
        prepared_string = prepared_string.rstrip("\n")
        return prepared_string

    def to_json(self) -> str:
        """Return ShoppingList contents as JSON formatted string."""

        output = {
            "shopping_list": self.items,
            "intermediates": self.intermediate_steps,
            "target_items": self.target_items,
            "target_amount": self.target_amount,
        }
        return dumps(output, sort_keys=True, indent=2)

    def format_for_text_display(self) -> str:
        """Format the ShoppingList for printing to stdout."""

        # Define the desired order of keys
        key_order = ["quantity", "rarity", "source", "wiki"]
        ignore_keys = ["name", "items"]

        # target_items_formatted = "\n".join(
        #     f"{item}: " + ", ".join(
        #         f"{k}: {details[k]}"
        #         for k in key_order + [k for k in details if k not in key_order and k not in ignore_keys]
        #         if k in details
        #     )
        #     for item, details in sorted(self.target_items.items())
        # )
        target_items_formatted = "\n".join(self.target_items.keys())

        items_formatted = "\n".join(
            f"{item}: "
            + ", ".join(
                f"{k}: {details[k]}"
                for k in key_order
                + [k for k in details if k not in key_order and k not in ignore_keys]
                if k in details
            )
            for item, details in sorted(self.items.items())
        )

        intermediate_items_formatted = "\n".join(
            f"{item}: "
            + ", ".join(
                f"{k}: {details[k]}"
                for k in key_order
                + [k for k in details if k not in key_order and k not in ignore_keys]
                if k in details
            )
            for item, details in sorted(self.intermediate_steps.items())
        )

        message_parts = [
            f"You selected:",
            target_items_formatted,
            "",
            f"Gather these items:",
            items_formatted,
            "",
            "Craft these intermediate items:",
            intermediate_items_formatted,
        ]

        # Join all parts into the final message.
        message = "\n".join(message_parts)

        return message

    def format_recipes_for_text_display(self) -> str:
        """Format the ShoppingList for printing to stdout."""

        # Define the desired order of keys
        key_order = ["rarity", "source", "wiki"]

        # Construct the output with each item on a new line
        items_dump = "\n".join(
            f"{item}: "
            + ", ".join(f"{k}: {details[k]}" for k in key_order if k in details)
            + ", "
            + ", ".join(
                f"{k}: {details[k]}"
                for k in details
                if k not in key_order and k != "name" and k != "quantity"
            )
            for item, details in sorted(self.items.items())
        ).rstrip(", ")

        # Construct the message
        items_message = "" if items_dump == "{}" or not items_dump else items_dump

        # Base message parts.
        message_parts = [
            items_message,
        ]

        # Join all parts into the final message.
        message = "\n".join(message_parts)

        return message
