import pygame
import sys
import time
import os
import random

# it must be done otherwise it does not know
pygame.font.init()

# SET THE WINDOW OF THE GAME
WIDTH, HEIGHT = 750, 750
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invaders 0.1")

# load ships images
RED_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_red_small.png"))
BLUE_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_blue_small.png"))
GREEN_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_green_small.png"))
# player ship
YELLOW_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_yellow (copy).jpeg"))

# load guns and background
BACKGROUND = pygame.image.load("assets/background-black.png")
BG = pygame.transform.scale(BACKGROUND, (WIDTH, HEIGHT))
LASER_BLUE = pygame.image.load(os.path.join("assets", "pixel_laser_blue.png"))
LASER_GREEN = pygame.image.load(os.path.join("assets", "pixel_laser_green.png"))
LASER_RED = pygame.image.load(os.path.join("assets", "pixel_laser_red.png"))
LASER_YELLOW = pygame.image.load(os.path.join("assets", "pixel_laser_yellow.png"))


class Laser:
    def __init__(self, x, y, img):
        self.x = x
        self.y = y
        self.img = img
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))

    def move(self, velocity):
        self.y += velocity

    def off_screen(self, height):
        return not(height >= self.y >= 0)

    def collision(self, obj):
        return collide(self, obj)


# abstract class
class Ship:
    # cooldown at 1/6 sec
    COOLDOWN = 10

    def __init__(self, x, y, health=100):
        self.x = x
        self.y = y
        self.health = health
        self.ship_img = None
        self.laser_img = None
        self.lasers = []
        self.cool_down_counter = 0

    def draw(self, window):
        window.blit(self.ship_img, (self.x, self.y))
        for laser in self.lasers:
            laser.draw(window)

    def move_lasers(self, vel, obj):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            elif laser.collision(obj):
                obj.health -= 10
                self.lasers.remove(laser)

    def get_width(self):
        return self.ship_img.get_width()

    def get_height(self):
        return self.ship_img.get_height()

    def cooldown(self):
        if self.cool_down_counter >= self.COOLDOWN:
            self.cool_down_counter = 0
        elif self.cool_down_counter > 0:
            self.cool_down_counter += 1

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x , self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1


class Player(Ship):
    def __init__(self, x, y, health=100):
        super().__init__(x, y, health)
        self.ship_img = YELLOW_SPACE_SHIP
        self.laser_img = LASER_YELLOW
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.max_health = health

    def draw(self, window):
        super().draw(window)
        self.health_bar(window)

    def move_lasers(self, vel, objs):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            else:
                for obj in objs:
                    if laser.collision(obj):
                        objs.remove(obj)
                        self.lasers.remove(laser)

    def health_bar(self, window):
        pygame.draw.rect(window, (255, 0, 0),
                         (self.x, self.y + self.ship_img.get_height() + 10, self.ship_img.get_width(), 10))
        pygame.draw.rect(window, (0, 255, 0),
                         (self.x, self.y + self.ship_img.get_height() + 10,
                         health_percentage(self.health, self.max_health, self.ship_img.get_width()),
                          10))


class Enemy(Ship):
    COLOR_MAP = {
        "red": (RED_SPACE_SHIP, LASER_RED),
        "blue": (BLUE_SPACE_SHIP, LASER_BLUE),
        "green": (GREEN_SPACE_SHIP, LASER_GREEN)
    }

    def __init__(self, x, y, color, health=100):
        super().__init__(x, y, health)
        self.ship_img, self.laser_img = self.COLOR_MAP[color]
        self.mask = pygame.mask.from_surface(self.ship_img)

    def move(self, velocity):
        self.y += velocity

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x - 10, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1


# check if 2 objects collide with pygame's overlap on the mask
def collide(obj1, obj2):
    offset_x = int(obj2.x - obj1.x)
    offset_y = int(obj2.y - obj1.y)
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) is not None


def health_percentage(health, max_health, width):
    return width * health / max_health if (width * health / max_health) > 0 else 0


def play():
    FPS = 30
    clock = pygame.time.Clock()

    run = True
    lost = False
    level = 0
    lives = 1
    player_velocity = 5
    laser_velocity = 6

    main_font = pygame.font.SysFont("comicsans", 50)
    lost_font = pygame.font.SysFont("comicsans", 100)

    # Create player at down middle of the screen
    player = Player(WIDTH/2, HEIGHT - 130)
    enemies = []
    wave_length = 5
    enemy_velocity = 1

    def redraw_window():
        WINDOW.blit(BG, (0, 0))
        # draw text Lives and Levels
        lives_label = main_font.render(f" Lives: {lives}", 1, (255, 255, 255))
        level_label = main_font.render(f" Level: {level}", 1, (255, 255, 255))
        WINDOW.blit(lives_label, (10, 10))
        WINDOW.blit(level_label, (WIDTH - level_label.get_width() - 10, 10))
        #  draw player
        player.draw(WINDOW)
        #  draw enemies
        for enemy in enemies:
            enemy.draw(WINDOW)

        if lost:
            # show you loser screen on top of screen
            lost_label = lost_font.render("You lost!!!", 1, (255, 255, 255))
            WINDOW.blit(lost_label, (WIDTH / 2 - lost_label.get_width() / 2, 300))
            # TODO: stop the game/ go to start a new game

        pygame.display.update()

    # Main loop
    while run:
        clock.tick(FPS)
        if lives <= 0 or player.health <= 0:
            lost = True

        if len(enemies) == 0:
            level += 1
            wave_length += 5
            for i in range(wave_length):
                enemy = Enemy(random.randrange(50, WIDTH - 50), random.randrange(-1000, -100),
                              random.choice(["red", "blue", "green"]))
                enemies.append(enemy)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                # pygame.quit()

        # get keys pressed
        keys = pygame.key.get_pressed()
        # Actions on key pressed
        if keys[pygame.K_a] and player.x - player_velocity > 0:  # left
            player.x -= player_velocity
        if keys[pygame.K_d] and player.x + player_velocity + player.get_width() < WIDTH:  # right
            player.x += player_velocity
        if keys[pygame.K_w] and player.y - player_velocity > 0:  # up
            player.y -= player_velocity
        if keys[pygame.K_s] and player.y + player_velocity + player.get_height() < HEIGHT:  # down
            player.y += player_velocity
        if keys[pygame.K_SPACE]:  # shoot laser
            player.shoot()
        #  a pause action

        for enemy in enemies[:]:
            enemy.move(enemy_velocity)
            enemy.move_lasers(laser_velocity, player)

            # random enemy shooting
            if random.randrange(0, 3 * 60) == 1:
                enemy.shoot()

            if collide(enemy, player):
                player.health -= 10
                enemies.remove(enemy)
            elif enemy.y + enemy.get_height() > HEIGHT:
                enemies.remove(enemy)
                lives -= 1

        player.move_lasers(-laser_velocity, enemies)

        redraw_window()


def main_menu():
    run = True

    title_font = pygame.font.SysFont("comicssans", 70)

    while run:
        #  draw a start game screen
        WINDOW.blit(BG, (0, 0))
        title_label = title_font.render("Press the mouse to start...", 1, (255, 255, 255))
        WINDOW.blit(title_label, (WIDTH/2 - title_label.get_width()/2, 350))
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                play()

    pygame.quit()


if __name__ == "__main__":
    # main execution
    main_menu()


