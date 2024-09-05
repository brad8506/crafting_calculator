import socketserver
import webbrowser
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from typing import Dict, Any, Tuple
import json
from yaml import safe_load

# internal
from crafting_calculator import *
from crafting.common import *


class MyRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        # Handle the root path
        if self.path == "/":
            self.path = "/web/index.html"
            return super().do_GET()

        # Handle the game discovery
        elif self.path.startswith("/discover_games"):
            games = self.discover_games()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(games).encode())

        # Handle game selection
        elif self.path.startswith("/select_game"):
            query_components = parse_qs(urlparse(self.path).query)
            selected_game = query_components.get("game", [None])[0]
            if selected_game:
                self.update_data_json(selected_game)
            self.send_response(200)
            self.end_headers()

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

    def update_data_json(self, game):
        # Load the game's recipes
        inventory, meta = self._load_recipes(game)
        listCraftable, listGatherable = process_inventory(inventory)
        listCraftableItems = sorted(list(listCraftable.keys()))

        # Update the data.json file
        data = listCraftable
        # update_amounts_recursively(data, 1)
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
        # inventory = process_inventory(inventory)
        # inventory = update_amounts_recursively(inventory, 1)
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
