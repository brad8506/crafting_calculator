import socketserver
import webbrowser
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, unquote
from pathlib import Path
from typing import Dict, Any, Tuple
import json
from yaml import safe_load

# internal
from crafting_calculator import *
from crafting.common import *


class MyRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = self.path
        parsed_url = urlparse(path)

        # Handle the game discovery
        if self.path.startswith("/discover_games"):
            games = self.discover_games()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(games).encode())

        elif self.path.startswith("/discover_specialisations"):
            query_components = parse_qs(urlparse(self.path).query)
            selected_game = query_components.get("game", [None])[0]
            if selected_game:
                specialisations = self.discover_specialisations(selected_game)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(specialisations).encode())

        elif self.path.startswith("/filter_recipes"):
            # Extract the parts after "/filter_recipes"
            parts = self.path.split("/")
            if len(parts) >= 3:
                game = parts[2]  # The game will be at index 2
                specialisation = parts[3]  # The specialisation will be at index 3
                decoded_specialisation = unquote(specialisation)
                if (
                    decoded_specialisation == "null"
                    or decoded_specialisation == "- None -"
                ):
                    specialisation = False
                if game and specialisation:
                    [recipes, meta] = self.filter_recipes(game, specialisation)
                    self.update_data_json_with_recipes(recipes)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(recipes).encode())
                elif game:
                    data = self.update_data_json_for_game(game)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(data).encode())

        # Handle game selection
        elif self.path.startswith("/select_game"):
            query_components = parse_qs(urlparse(self.path).query)
            selected_game = query_components.get("game", [None])[0]
            if selected_game:
                self.update_data_json_for_game(selected_game)
            self.send_response(200)
            self.end_headers()

        # Handle the root path
        elif parsed_url.path == "/":
            self.path = "/web/index.html"
            return super().do_GET()

        else:
            return super().do_GET()

    def discover_games(self) -> Tuple[Dict[str, Any]]:
        games = []
        path = Path("recipes")
        for entry in path.rglob("**/meta.yml"):
            raw_content = entry.read_text()
            content = safe_load(raw_content)
            if content and content.get("title"):
                games.append(entry.parent.name)
        return games

    def discover_specialisations(self, game):
        path = Path(f"recipes/{game}")
        fullPath = path.resolve()  # Get the absolute path

        # Debugging: Check if the directory exists
        if not fullPath.exists():
            print(f"Error: The path {fullPath} does not exist.")
            return []

        print(f"Resolved full path: {fullPath}")  # Debug log

        # Debugging: List the files and directories inside fullPath
        try:
            contents = list(fullPath.rglob("*.yml"))  # Find all .yml files recursively
            print(f"Contents of {fullPath}: {contents}")  # Debug log
        except Exception as e:
            print(f"Error reading directory: {e}")
            return []

        # Get specialisations (file names without extension)
        specialisations = ["- None -"]
        for entry in contents:
            print(f"Checking entry: {entry} (Type: {type(entry)})")  # Debug log
            if entry.is_file() and entry.suffix == '.yml' and entry.stem != 'meta':
                specialisations.append(entry.stem)  # Add file name without extension to specialisations

        return specialisations

    def filter_recipes(self, game: str, specialization: str) -> Dict[str, Any]:
        path = Path(f"recipes/{game}")
        content_list = {}
        filtered_inventory = {}
        filtered_meta = {}

        inventory = {}
        inventory, meta = self._load_recipes(game)
        listCraftable, listGatherable = process_inventory(inventory)

        # Ensure the path exists
        if not path.exists() or not path.is_dir():
            return content_list

        # Look for the specific specialization file
        # recipe_file = path / f"{specialization}.yml"
        recipe_file = self.find_specialization_file(game, specialization)
        if recipe_file:
            raw_content = recipe_file.read_text(encoding="utf-8")
            content = safe_load(raw_content)

            # Validate content and collect recipes
            if content:
                content_list = content
                filtered_inventory, filtered_meta = load_recipes_from_content(content_list)
                filtered_dict = {key: inventory[key] for key in filtered_inventory if key in inventory}
                inventory = filtered_dict
        return (inventory, meta)

    def find_specialization_file(self, game, specialization):
        specialization = unquote(specialization)
        path = Path(f"recipes/{game}")
        fullPath = path.resolve()  # Get the absolute path

        # Debugging: Check if the directory exists
        if not fullPath.exists():
            print(f"Error: The path {fullPath} does not exist.")
            return None

        print(f"Resolved full path: {fullPath}")  # Debug log

        # Recursively search for the specialization file
        specialization_file = None
        for entry in fullPath.rglob(f"**/{specialization}.yml"):
            if entry.is_file():
                specialization_file = entry
                break  # Stop at the first match

        if specialization_file:
            print(f"Found specialization file: {specialization_file}")
        else:
            print(f"Specialization file {specialization}.yml not found.")

        return specialization_file

    def update_data_json_for_game(self, game):
        # Load the game's recipes
        inventory, meta = self._load_recipes(game)
        self.update_data_json_with_recipes
        listCraftable, listGatherable = process_inventory(inventory)
        listCraftableItems = sorted(list(listCraftable.keys()))

        # Update the data.json file
        data = listCraftable
        file_path = "data.json"
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)  # Indent for readability
                print(data)
            print(f"Data successfully written to {file_path}")
        except (IOError, TypeError) as e:
            print(f"Error writing file: {e}")

        return data

    def update_data_json_with_recipes(self, recipes):
        # Process the inventory for craftable and gatherable items
        listCraftable, listGatherable = process_inventory(recipes)
        listCraftableItems = sorted(list(listCraftable.keys()))

        # Update the data.json file with filtered data
        data = listCraftable
        file_path = "data.json"
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)  # Indent for readability
                print(data)
            print(f"Data successfully written to {file_path}")
        except (IOError, TypeError) as e:
            print(f"Error writing file: {e}")

    def end_headers(self):
        # Add CORS headers, we only allow localhost.
        self.send_header("Access-Control-Allow-Origin", "http://localhost")
        super().end_headers()

    # Placeholder methods for loading recipes and processing inventory
    def _load_recipes(self, game):
        inventory, meta = load_recipes(game)
        return (inventory, meta)


# Define the server address and port
PORT = 8000
server_address = ("localhost", PORT)


def start_server():
    httpd = socketserver.TCPServer(server_address, MyRequestHandler)
    print(f"Serving on http://{server_address[0]}:{PORT}")
    httpd.serve_forever()


def open_browser():
    # Open the default web browser to the server URL
    webbrowser.open(f"http://{server_address[0]}:{PORT}")


if __name__ == "__main__":
    # Start the server in a new thread
    server_thread = threading.Thread(target=start_server)
    server_thread.start()

    # Open the browser
    open_browser()
