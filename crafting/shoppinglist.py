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

    @staticmethod
    def move_single_int_to_quantity(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Iterate over the dictionary and move a single integer value to a 'quantity' property.
        Ensures each dictionary has only one integer value.
        
        Args:
            data (Dict[str, Any]): The dictionary to process.
        
        Returns:
            Dict[str, Any]: The updated dictionary with the integer value moved to 'quantity'.
        """
        updated_data = {}
        
        for key, value in data.items():
            if isinstance(value, dict):
                # Process nested dictionaries
                updated_data[key] = ShoppingList.move_single_int_to_quantity(value)
            elif isinstance(value, int):
                # If the value is an integer, move it to 'quantity'
                updated_data[key] = {'quantity': value}
            else:
                # Keep other values as they are
                updated_data[key] = value
        
        # Ensure that each dictionary has only one integer value
        if len(updated_data) == 1 and isinstance(list(updated_data.values())[0], dict) and 'quantity' in list(updated_data.values())[0]:
            # If there is only one item and it's a dict with a 'quantity' key, return as is
            return updated_data
        
        return updated_data

    def update_quantity(self, item: str, amount: int) -> None:
        """Update the quantity of an item in the shopping list."""
        # recipe = self.inventory.get(item, None)
        # if recipe:
        #     recipe['quantity'] = recipe.get('quantity', 1) * amount
        # else:
        #     recipe = {}
        #     recipe[item] = {'quantity': amount}

        if item in self.items:
            current = self.items[item]
            if isinstance(current, dict):
                current['quantity'] = current.get('quantity', 1) + amount
            else:
                logging.warning(f"Item {item} is not a dictionary.")
        else:
            # Handle cases where the item is not in self.items
            recipe = self.inventory.get(item, None)
            if recipe:
                recipe['quantity'] = recipe.get('quantity', 1) * amount
            else:
                recipe = {'name': item, 'quantity': amount}
            self.items.update({item: recipe})

    def add_items(self, items: Dict[str, Dict[str, Any]], amount: int) -> None:
        """Add items to the shopping list."""
        for item in items:
            logging.debug("Adding %s to shopping list.", item)
            self.update_quantity(item, amount)
            #self.items.update({item: items[item]})

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
        self.intermediate_steps.update({item: self.intermediate_steps.get(item, 0) + amount})

    def simplify(self) -> None:
        """Recursively replace intermediate crafted items with their components."""
        logging.info("Simplifying shopping list.")

        rerun_simplify = False

        replacements = {}
        for item in self.items:
            recipe = self.inventory.get(item, None)
            if recipe:
                if 'items' in recipe:
                    replacements.update({item: recipe})

        if replacements:
            items_to_delete = []
            for key, value in replacements.items():
                self.replace_items(key, value)
                items_to_delete.append(key) # Mark item for deletion

            # Remove items after the loop to avoid resizing dictionary during iteration
            for item in items_to_delete:
                del self.items[item]
                del replacements[item]
            
            rerun_simplify = True

        if rerun_simplify:
            self.simplify()
        else:
            logging.info("Nothing to simplify.")

    def replace_items(self, item_name: str, item: Dict[str, Any]) -> None:
        """Replace items in the shopping list with smaller components."""
        amount_item = int(item.get('quantity', 1))
        child_items = item.get('items', None)
        if isinstance(child_items, dict):
            for child_item_name, value in child_items.items(): 
                quantity = int(value.get('quantity', 1))
                amount_replaced_item = quantity * amount_item
                logging.info("Replacing %s of %s.", amount_replaced_item, item)
                self.add_items({child_item_name: value}, amount_replaced_item)        
        else:
            logging.warning("Unexpected type for replacement_items: %s", type(item))
        
        # Record the step of replacement (if applicable)
        self.add_step(item_name, amount_item)

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
        target_items = self.target_items.keys()
        target_items_formatted = '\n'.join([f"- {item}: {self.target_amount}" for item in target_items])

        # Define the desired order of keys
        key_order = ["quantity", "rarity", "source", 'wiki']

        # Construct the output with each item on a new line
        items_dump = "\n".join(
            f"{item}: " + ", ".join(
                f"{k}: {details[k]}" 
                for k in key_order 
                if k in details
            ) + ", " + ", ".join(
                f"{k}: {details[k]}" 
                for k in details 
                if k not in key_order and k != "name"
            )
            for item, details in self.items.items()
        ).rstrip(", ")

        # Construct the message
        items_message = (
            target_items_formatted
            if items_dump == '{}' or not items_dump
            else items_dump
        )
        
        intermediate_steps_dump = safe_dump(self.intermediate_steps, default_flow_style=False, sort_keys=True).rstrip("\n")
        intermediate_steps_message = (
            "No intermediate steps."
            if intermediate_steps_dump == '{}' or not intermediate_steps_dump
            else intermediate_steps_dump
        )

        # Base message parts.
        message_parts = [
            f"You selected\n{target_items_formatted}",
            "",
            f"You need these items to craft:",
            items_message,
            "",
            "The following intermediate items need to be crafted:",
            intermediate_steps_message,
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
