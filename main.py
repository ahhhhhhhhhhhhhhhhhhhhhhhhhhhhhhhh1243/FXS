import re
import pygame
import threading
import random  # Added to spawn enemies at random locations

# Initialize Pygame
pygame.init()

# Lexer - Tokenize the input string
TOKEN_SPEC = [
    ('COMMAND', r'game.add|draw'),
    ('OBJECT', r'window|sprite|square|enemy|movement|start menu|collision|gun'),
    ('NUMBER', r'\d+'),
    ('PAREN', r'[(),]'),
    ('SKIP', r'[ \t]+'),  # Skip spaces and tabs
]

def tokenize(code):
    tokens = []
    for pattern, regex in TOKEN_SPEC:
        matches = re.finditer(regex, code)
        for match in matches:
            tokens.append((pattern, match.group(0)))
    return tokens

# Parser - Parse the tokens into an Abstract Syntax Tree (AST)
class Parser:
    def parse(self, tokens):
        command = tokens[0][1]  # e.g., 'game.add' or 'draw'
        obj = tokens[1][1]      # e.g., 'window', 'sprite', 'enemy', 'square', 'movement', 'collision', 'gun'
        numbers = [int(token[1]) for token in tokens if token[0] == 'NUMBER']
        
        return {
            'command': command,
            'object': obj,
            'numbers': numbers
        }

# Interpreter - Execute the AST
class Interpreter:
    def __init__(self):
        self.sprites = []
        self.enemies = []
        self.bullets = []
        self.player = None
        self.player_speed = 5
        self.show_start_menu = False
        self.collision_enabled = False
        self.player_has_gun = False
        self.gun_damage = 10
        self.dead = False

    def draw_start_menu(self, screen):
        font = pygame.font.SysFont(None, 55)
        title_text = font.render("Start Menu", True, (255, 255, 255))
        instruction_text = font.render("Press ENTER to Start", True, (255, 255, 255))

        screen.fill((0, 0, 0))  # Black background
        screen.blit(title_text, (300, 200))  # Draw the title
        screen.blit(instruction_text, (220, 300))  # Draw the instruction

    def execute(self, ast, screen):
        if ast['command'] == 'game.add':
            if ast['object'] == 'window':
                width, height = ast['numbers']
                pygame.display.set_mode((width, height))
                pygame.display.set_caption('My Game Window')
            elif ast['object'] == 'sprite':
                x, y = ast['numbers']
                sprite = pygame.Rect(x, y, 50, 50)  # Create a sprite
                self.player = sprite
                self.sprites.append(sprite)
            elif ast['object'] == 'enemy':
                self.spawn_enemy()  # Call spawn_enemy when 'enemy' is added
            elif ast['object'] == 'movement':
                speed = ast['numbers'][0]
                self.player_speed = speed
            elif ast['object'] == 'start menu':
                self.show_start_menu = True
            elif ast['object'] == 'collision':
                self.collision_enabled = True
            elif ast['object'] == 'gun':
                self.player_has_gun = True
                if len(ast['numbers']) > 0:
                    self.gun_damage = ast['numbers'][0]

    def spawn_enemy(self):
        x = random.randint(50, 850)  # Random x coordinate
        y = random.randint(50, 750)  # Random y coordinate
        enemy = {'rect': pygame.Rect(x, y, 50, 50), 'health': 100}  # Create enemy at random location
        self.enemies.append(enemy)

    def draw_sprites(self, screen):
        for sprite in self.sprites:
            pygame.draw.rect(screen, (0, 255, 0), sprite)

    def draw_enemies(self, screen):
        for enemy in self.enemies:
            pygame.draw.rect(screen, (255, 0, 0), enemy['rect'])
            self.move_enemy_towards_player(enemy['rect'])

    def draw_bullets(self, screen):
        for bullet in self.bullets:
            pygame.draw.rect(screen, (255, 255, 0), bullet)

    def move_enemy_towards_player(self, enemy_rect):
        if self.player and not self.dead:
            if enemy_rect.x < self.player.x:
                enemy_rect.x += 1
            elif enemy_rect.x > self.player.x:
                enemy_rect.x -= 1
            if enemy_rect.y < self.player.y:
                enemy_rect.y += 1
            elif enemy_rect.y > self.player.y:
                enemy_rect.y -= 1

    def move_player(self, keys_pressed):
        if self.player and not self.dead:
            if keys_pressed[pygame.K_LEFT]:
                self.player.x -= self.player_speed
            if keys_pressed[pygame.K_RIGHT]:
                self.player.x += self.player_speed
            if keys_pressed[pygame.K_UP]:
                self.player.y -= self.player_speed
            if keys_pressed[pygame.K_DOWN]:
                self.player.y += self.player_speed

    def shoot_bullet(self):
        if self.player and self.player_has_gun and not self.dead:
            bullet = pygame.Rect(self.player.x + 25, self.player.y + 25, 10, 10)
            self.bullets.append(bullet)

    def move_bullets(self):
        for bullet in self.bullets:
            bullet.x += 10
            for enemy in self.enemies:
                if bullet.colliderect(enemy['rect']):
                    enemy['health'] -= self.gun_damage
                    if enemy['health'] <= 0:
                        self.enemies.remove(enemy)
                        self.spawn_enemy()  # Spawn a new enemy when one dies
                    self.bullets.remove(bullet)
                    break

    def check_collision(self):
        if self.collision_enabled and not self.dead:
            for enemy in self.enemies:
                if self.player.colliderect(enemy['rect']):
                    self.dead = True

    def draw_death_screen(self, screen):
        font = pygame.font.SysFont(None, 55)
        death_text = font.render("You Died!", True, (255, 0, 0))
        instruction_text = font.render("Press R to Restart", True, (255, 255, 255))
        screen.fill((0, 0, 0))
        screen.blit(death_text, (320, 250))
        screen.blit(instruction_text, (220, 350))

# Game thread to run the game loop
def game_thread(code, interpreter, screen):
    tokens = tokenize(code)
    parser = Parser()
    ast = parser.parse(tokens)
    interpreter.execute(ast, screen)

# Thread to read user input
def input_thread(interpreter, screen):
    while True:
        code = input("Enter code (e.g., 'game.add window (900, 800)', 'game.add start menu', 'game.add gun (20)'): ")
        game_thread(code, interpreter, screen)

# Main game loop
def main_game_loop(interpreter):
    screen = pygame.display.set_mode((900, 800))
    running = True
    game_started = False
    
    while running:
        keys_pressed = pygame.key.get_pressed()
        screen.fill((0, 0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_r and interpreter.dead:
                    interpreter.dead = False
                if interpreter.show_start_menu and event.key == pygame.K_RETURN:
                    interpreter.show_start_menu = False
                    game_started = True
                if event.key == pygame.K_SPACE and interpreter.player_has_gun:
                    interpreter.shoot_bullet()

        if interpreter.dead:
            interpreter.draw_death_screen(screen)
        elif interpreter.show_start_menu and not game_started:
            interpreter.draw_start_menu(screen)
        else:
            interpreter.move_player(keys_pressed)
            interpreter.move_bullets()
            interpreter.draw_sprites(screen)
            interpreter.draw_bullets(screen)
            interpreter.draw_enemies(screen)
            interpreter.check_collision()

        pygame.display.flip()
        pygame.time.delay(30)

    pygame.quit()

# Main thread
if __name__ == "__main__":
    interpreter = Interpreter()
    threading.Thread(target=input_thread, args=(interpreter, pygame.display.set_mode((900, 800)))).start()
    main_game_loop(interpreter)
