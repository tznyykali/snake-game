import socket
import threading
import pickle
import random

class Server:
    def __init__(self, host, port):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Set socket option
        self.server_socket.bind((host, port))
        self.server_socket.listen()
        print(f"Server listening on {host}:{port}")

        self.clients = {}
        self.player_count = 0  # Track total number of players
        self.game_state = {
            "players": {},
            "scores": {},
            "food": self.generate_food(),
        }

    def generate_food(self):
        return [random.randint(1, 59) * 10, random.randint(1, 39) * 10]

    def handle_client(self, client_socket, client_address):
        print(f"New connection from {client_address}")

        try:
            self.player_count += 1
            snake_id = self.player_count  # Assign player ID based on total players
            self.clients[client_socket] = snake_id
            self.game_state["players"][snake_id] = [[100, 50], [90, 50], [80, 50]]
            self.game_state["scores"][snake_id] = 0

            while True:
                data = client_socket.recv(4096)
                if not data:
                    break
                snake_data = pickle.loads(data)
                self.game_state["players"][snake_id] = snake_data["snake_body"]

                # Check if the snake is dead (for example, hits the wall, bites itself, or bites other players)
                if self.snake_is_dead(snake_data["snake_body"], snake_id):
                    self.game_state["players"][snake_id] = [[100, 50], [90, 50], [80, 50]]  # Reset snake position
                    self.game_state["scores"][snake_id] = 0  # Reset score

                self.update_scores()
                self.broadcast_game_state()
        except Exception as e:
            print(f"Connection lost: {e}")
        finally:
            print(f"Connection from {client_address} closed")
            del self.game_state["players"][snake_id]
            del self.game_state["scores"][snake_id]
            del self.clients[client_socket]
            client_socket.close()
            self.broadcast_game_state()

    def update_scores(self):
        # Reset food if eaten by any player
        for snake_id, snake_body in self.game_state["players"].items():
            head = snake_body[0]
            if head == self.game_state["food"]:
                self.game_state["scores"][snake_id] += 1
                self.game_state["food"] = self.generate_food()

    def snake_is_dead(self, snake_body, current_snake_id):
        # Implement logic to check if snake is dead (e.g., hits wall, bites itself, or bites other players)
        head = snake_body[0]
        # Check if snake hits the wall
        if head[0] < 0 or head[0] >= 600 or head[1] < 0 or head[1] >= 400:
            return True
        # Check if snake bites itself
        if head in snake_body[1:]:
            return True
        # Check if snake bites other players
        for snake_id, player_body in self.game_state["players"].items():
            if snake_id != current_snake_id and head in player_body:
                return True
        return False

    def broadcast_game_state(self):
        game_state_data = {"players": self.game_state["players"], "scores": self.game_state["scores"], "food": self.game_state["food"]}
        serialized_data = pickle.dumps(game_state_data)
        for client_socket in list(self.clients.keys()):
            try:
                client_socket.sendall(serialized_data)
            except Exception as e:
                print(f"Error sending data: {e}")
                del self.clients[client_socket]
                client_socket.close()

    def start(self):
        while True:
            client_socket, client_address = self.server_socket.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
            client_thread.start()

if __name__ == "__main__":
    server = Server('0.0.0.0', 5555)
    server.start()
