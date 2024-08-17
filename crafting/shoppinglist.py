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

    def __init__(self, inventory: List[Dict[str, Any]], item: str, amount: int):
        self.items: Dict[str, int] = {}
        self.crafting_cost: Dict[str, float] = {}
        self.sell_to_vendor: float = 0.0
        self.buy_from_vendor: float = 0.0
        self.target_items: Dict[str, int] = {}
        self.target_amount: int = amount
        self.intermediate_steps: Dict[str, int] = {}
        self.inventory = inventory

    @classmethod
    def create_empty(cls):
        inventory = []  # Empty inventory
        item = ""  # Empty item
        amount = 0  # Default amount
        return cls(inventory, item, amount)

    def add_items(self, items: Dict[str, int], amount: int) -> None:
        """Add items to the shopping list."""
        for item in items:
            logging.debug("Adding %s to shopping list.", item)
            self.items.update({item: items[item] * amount})

    def calculate_crafting_costs(self) -> None:
        """Calculate all costs."""
        for item in self.target_items:
            recipe_cost = get_crafting_cost(item, self.inventory)
            if recipe_cost is not None:
                self.crafting_cost.update(
                    {item: self.target_items[item] * recipe_cost * self.target_amount}
                )

        for item in self.items:
            recipe_cost = get_crafting_cost(item, self.inventory)
            if recipe_cost is not None:
                self.crafting_cost.update(
                    {item: self.items[item] * recipe_cost * self.target_amount}
                )

        for item in self.intermediate_steps:
            recipe_cost = get_crafting_cost(item, self.inventory)
            if recipe_cost is not None:
                self.crafting_cost.update(
                    {
                        item: self.intermediate_steps[item]
                        * recipe_cost
                        * self.target_amount
                    }
                )
        logging.debug(
            "Summing item crafting_cost for %s item/s in shopping list.", item
        )

    def calculate_buy_from_vendor(self) -> None:
        """Calculate the total cost to buy items from vendors."""
        self.buy_from_vendor = 0.0  # Initialize as a float

        # Process target items
        for item in self.target_items:
            buy_cost = get_buy_from_vendor(item, self.inventory)
            if buy_cost is not None:
                self.buy_from_vendor += (
                    self.target_items[item] * buy_cost * self.target_amount
                )

        # Process items
        for item in self.items:
            buy_cost = get_buy_from_vendor(item, self.inventory)
            if buy_cost is not None:
                self.buy_from_vendor += self.items[item] * buy_cost * self.target_amount

        # Process intermediate steps
        for item in self.intermediate_steps:
            buy_cost = get_buy_from_vendor(item, self.inventory)
            if buy_cost is not None:
                self.buy_from_vendor += (
                    self.intermediate_steps[item] * buy_cost * self.target_amount
                )

        logging.debug("Total buy_from_vendor cost: %s", self.buy_from_vendor)

    def calculate_sell_to_vendor(self) -> None:
        """Calculate the total revenue from selling items to vendors."""
        self.sell_to_vendor_cost = 0.0  # Initialize as a float

        # Process target items
        for item in self.target_items:
            sell_cost = get_sell_to_vendor(item, self.inventory)
            if sell_cost is not None:
                self.sell_to_vendor_cost += (
                    self.target_items[item] * sell_cost * self.target_amount
                )

        # Process items
        for item in self.items:
            sell_cost = get_sell_to_vendor(item, self.inventory)
            if sell_cost is not None:
                self.sell_to_vendor_cost += (
                    self.items[item] * sell_cost * self.target_amount
                )

        # Process intermediate steps
        for item in self.intermediate_steps:
            sell_cost = get_sell_to_vendor(item, self.inventory)
            if sell_cost is not None:
                self.sell_to_vendor_cost += (
                    self.intermediate_steps[item] * sell_cost * self.target_amount
                )

        logging.debug("Total sell_to_vendor revenue: %s", self.sell_to_vendor_cost)

    def add_step(self, item: str, amount: int) -> None:
        """Add intermediate items to the crafting tree."""
        logging.debug("Adding %s of %s to crafting tree.", amount, item)
        self.intermediate_steps.update(
            {item: self.intermediate_steps.get(item, 0) + amount}
        )

    def simplify(self) -> None:
        """Recursively replace intermediate crafted items with their components."""
        logging.info("Simplifying shopping list.")

        replacements = {}
        for item in self.items:
            recipe = find_recipe(item, self.inventory)
            if recipe:
                replacements.update({item: recipe})

        for item in replacements:
            self.replace_items(item, replacements[item])

        if replacements:
            self.simplify()
        else:
            logging.info("Nothing to simplify.")

    def replace_items(self, item: str, replacement_items: Dict[str, int]) -> None:
        """Replace items in the shopping list with smaller components."""
        amount_replaced_item = self.items.pop(item)
        logging.info("Replacing %s of %s.", amount_replaced_item, item)
        for replacement in replacement_items:
            amount_replacement = (
                self.items.get(replacement, 0)
                + replacement_items[replacement] * amount_replaced_item
            )
            self.items.update({replacement: amount_replacement})
        self.add_step(item, amount_replaced_item)

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

    def format_for_display(self) -> str:
        """Format the ShoppingList for printing to stdout."""
        total_crafting_cost = sum(self.crafting_cost.values())
        total_crafting_cost_formatted = f"{total_crafting_cost:,}"

        # Base message parts.
        message_parts = [
            "",
            f"You need these items to craft {self.target_amount} of {self.target_items}:",
            safe_dump(self.items, default_flow_style=False, sort_keys=True),
            "The following intermediate items need to be crafted:",
            safe_dump(
                self.intermediate_steps, default_flow_style=False, sort_keys=True
            ).rstrip("\n"),
        ]

        # Conditionally add the total crafting cost section.
        if total_crafting_cost > 0:
            message_parts.extend(
                [
                    "",
                    f"It will cost a total of {total_crafting_cost_formatted} to craft the intermediate items:",
                    safe_dump(
                        self.crafting_cost, default_flow_style=False, sort_keys=True
                    ),
                ]
            )

        # Conditionally add the sell to vendor section.
        if self.sell_to_vendor > 0:
            sell_to_vendor_formatted = f"{self.sell_to_vendor:,}"
            message_parts.extend(
                [
                    "",
                    f"{self.target_items} sells to a vendor for: {sell_to_vendor_formatted}",
                ]
            )

        # Conditionally add the buy from vendor section.
        if self.buy_from_vendor > 0:
            buy_from_vendor_formatted = f"{self.buy_from_vendor:,}"
            message_parts.extend(
                [
                    "",
                    f"{self.target_items} can be bought from a vendor for: {self.buy_from_vendor}",
                ]
            )

        # Join all parts into the final message.
        message = "\n".join(message_parts)

        return message
