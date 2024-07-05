import pygame
import socket
import threading
import pickle
import random

class Client:
    def __init__(self, host, port):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((host, port))
        self.game_state = {"players": {}, "scores": {}, "food": [0, 0]}
        self.player_id = None  # Initialize player ID
        threading.Thread(target=self.receive_data).start()

    def receive_data(self):
        while True:
            try:
                received_data = self.client_socket.recv(4096)
                if not received_data:
                    break
                game_state_data = pickle.loads(received_data)
                self.game_state = game_state_data
            except Exception as e:
                print(f"Connection lost: {e}")
                self.client_socket.close()
                break

    def send_data(self, snake_body):
        try:
            data_to_send = {"player_id": self.player_id, "snake_body": snake_body}
            serialized_data = pickle.dumps(data_to_send)
            self.client_socket.sendall(serialized_data)
        except Exception as e:
            print(f"Error sending data: {e}")

class SnakeGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((600, 400))
        pygame.display.set_caption('Multiplayer Snake Game')
        self.clock = pygame.time.Clock()
        self.client = Client('172.19.10.44', 5555)
        self.snake_pos = [100, 50]
        self.snake_body = [[100, 50], [90, 50], [80, 50]]
        self.direction = 'RIGHT'
        self.change_to = self.direction
        self.food_pos = [0, 0]

    def snake_is_dead(self):
        head = self.snake_body[0]
        return head[0] < 0 or head[0] >= 600 or head[1] < 0 or head[1] >= 400 or head in self.snake_body[1:]

    def handle_death(self):
        self.snake_pos = [100, 50]  # Reset snake position
        self.snake_body = [[100, 50], [90, 50], [80, 50]]  # Reset snake body
        self.direction = 'RIGHT'
        self.change_to = self.direction
        self.client.send_data(self.snake_body)

    def game_loop(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.change_to = 'UP'
                    if event.key == pygame.K_DOWN:
                        self.change_to = 'DOWN'
                    if event.key == pygame.K_LEFT:
                        self.change_to = 'LEFT'
                    if event.key == pygame.K_RIGHT:
                        self.change_to = 'RIGHT'

            if self.change_to == 'UP' and not self.direction == 'DOWN':
                self.direction = 'UP'
            if self.change_to == 'DOWN' and not self.direction == 'UP':
                self.direction = 'DOWN'
            if self.change_to == 'LEFT' and not self.direction == 'RIGHT':
                self.direction = 'LEFT'
            if self.change_to == 'RIGHT' and not self.direction == 'LEFT':
                self.direction = 'RIGHT'

            if self.direction == 'UP':
                self.snake_pos[1] -= 10
            if self.direction == 'DOWN':
                self.snake_pos[1] += 10
            if self.direction == 'LEFT':
                self.snake_pos[0] -= 10
            if self.direction == 'RIGHT':
                self.snake_pos[0] += 10

            self.snake_body.insert(0, list(self.snake_pos))
            if self.snake_pos == self.food_pos:
                self.food_pos = [random.randint(1, 59) * 10, random.randint(1, 39) * 10]
            else:
                self.snake_body.pop()

            if self.snake_is_dead():
                self.handle_death()

            self.client.send_data(self.snake_body)

            self.screen.fill((0, 0, 0))
            for player_id, player_snake in self.client.game_state["players"].items():
                for pos in player_snake:
                    pygame.draw.rect(self.screen, (0, 255, 0), pygame.Rect(pos[0], pos[1], 10, 10))
            self.food_pos = self.client.game_state["food"]
            pygame.draw.rect(self.screen, (255, 0, 0), pygame.Rect(self.food_pos[0], self.food_pos[1], 10, 10))

            for idx, (player_id, score) in enumerate(self.client.game_state["scores"].items()):
                font = pygame.font.Font(None, 36)
                text = font.render(f"Player {idx + 1}: {score}", True, (255, 255, 255))
                self.screen.blit(text, (10, 10 + idx * 30))

            pygame.display.flip()
            self.clock.tick(15)

if __name__ == "__main__":
    game = SnakeGame()
    game.game_loop()
