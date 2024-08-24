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

    def __init__(self, inventory: Dict[str, Dict[str, Any]], item: str, amount: int):
        self.items: Dict[str, Dict[str, Any]] = {}
        self.crafting_cost: Dict[str, float] = {}
        self.buy_from_vendor: Dict[str, float] = {}
        self.sell_to_vendor: float = 0.0
        self.target_items: Dict[str, Dict[str, Any]] = {}
        self.target_amount: int = amount
        self.intermediate_steps: Dict[str, Dict[str, Any]] = {}
        self.inventory = inventory

    @classmethod
    def create_empty(cls):
        inventory = []  # Empty inventory
        item = ""  # Empty item
        amount = 0  # Default amount
        return cls(inventory, item, amount)

    def add_items(self, items: Dict[str, Dict[str, Any]], amount: int) -> None:
        """Add items to the shopping list."""
        
        for key, value in items.items():
            child_items = value.get('items', None)
            a = True
        
        if isinstance(items.get('items'), dict):
            sub_items['quantity'] = sub_items['quantity'] * amount
            self.items.update({sub_items['name']: sub_items})
        elif isinstance(items, list):
            # If `items` is a list of dictionaries
            for sub_items in items:
                if isinstance(sub_items, dict):
                    sub_items['quantity'] = sub_items['quantity'] * amount

                    self.items.update({sub_items['name']: sub_items})
                else:
                    logging.warning("Unexpected list item type: %s", type(sub_items))
        else:
            logging.warning("Unexpected type for items: %s", type(items))

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

    def calculate_buy_from_vendor(self) -> Dict[str, float]:
        """Calculate the cost to buy each item from vendors and return a dictionary."""
        buy_from_vendor = {}  # Initialize as an empty dictionary

        # Process target items
        for item in self.target_items:
            buy_cost = get_buy_from_vendor(item, self.inventory)
            if buy_cost is not None:
                total_cost = buy_cost * self.target_amount
                buy_from_vendor[item] = total_cost

        # Process items
        for item in self.items:
            buy_cost = get_buy_from_vendor(item, self.inventory)
            if buy_cost is not None:
                buy_from_vendor[item] = buy_cost

        # Process intermediate steps
        for item in self.intermediate_steps:
            buy_cost = get_buy_from_vendor(item, self.inventory)
            if buy_cost is not None:
                total_cost = (
                    self.intermediate_steps[item] * buy_cost * self.target_amount
                )
                buy_from_vendor[item] = total_cost

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

        if replacements:
            for item in replacements:
                self.replace_items(item, replacements[item])
            self.items.pop(item, None)

        if replacements:
            self.simplify()
        else:
            logging.info("Nothing to simplify.")

    # def replace_items(self, item: str, replacement_items: Dict[str, int]) -> None:
    #     """Replace items in the shopping list with smaller components."""
    #     amount_replaced_item = self.items.pop(item)
    #     logging.info("Replacing %s of %s.", amount_replaced_item, item)
    #     for replacement in replacement_items:
    #         amount_replacement = (
    #             self.items.get(replacement, 0)
    #             + replacement_items[replacement] * amount_replaced_item
    #         )
    #         self.items.update({replacement: amount_replacement})
    #     self.add_step(item, amount_replaced_item)

    def replace_items(self, item: str, replacement_items: Union[Dict[str, int], List[Dict[str, int]]]) -> None:
        """Replace items in the shopping list with smaller components."""
        
        # Check if `replacement_items` is a dictionary or list of dictionaries
        if isinstance(replacement_items, dict):
            # Handle dictionary case
            amount_replaced_item = self.items.pop(item, 0)
            logging.info("Replacing %s of %s.", amount_replaced_item, item)
            self.add_items(replacement_items, amount_replaced_item)
            
        elif isinstance(replacement_items, list):
            # Handle list of dictionaries case
            amount_replaced_item = self.items.pop(item, 0)
            logging.info("Replacing %s of %s.", amount_replaced_item, item)
            for sub_items in replacement_items:
                if isinstance(sub_items, dict):
                    # Ensure the quantity key exists and is a number
                    if 'quantity' in sub_items and isinstance(sub_items['quantity'], (int, float)):
                        # Scale the quantities by `amount_replaced_item`
                        updated_items = {k: v * amount_replaced_item for k, v in sub_items.items() if k != 'quantity'}
                        # Add items to shopping list
                        self.add_items(updated_items, 1)  # Use amount 1 as `amount_replaced_item` is handled
                    else:
                        logging.warning("Missing or invalid 'quantity' key in sub-items: %s", sub_items)
                else:
                    logging.warning("Unexpected list item type: %s", type(sub_items))
                    
        else:
            logging.warning("Unexpected type for replacement_items: %s", type(replacement_items))
        
        # Record the step of replacement (if applicable)
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

        # Conditionally add the buy from vendor section.
        if self.buy_from_vendor:
            message_parts.append("")
            message_parts.append("The following items can be bought from a vendor:")
            for item, cost in self.buy_from_vendor.items():
                if cost > 0:  # Only include items with a cost greater than 0
                    cost_formatted = f"{cost:,.2f}"  # Format cost with thousands separator and 2 decimal places
                    message_parts.append(f"{item}: {cost_formatted}")

        # Conditionally add the sell to vendor section.
        if self.sell_to_vendor > 0:
            sell_to_vendor_formatted = f"{self.sell_to_vendor:,}"
            message_parts.extend(
                [
                    "",
                    f"{self.target_items} sells to a vendor for: {sell_to_vendor_formatted}",
                ]
            )

        # Join all parts into the final message.
        message = "\n".join(message_parts)

        return message
