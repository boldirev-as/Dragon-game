import os
import random
import sys

import pygame
from constants import *
import pytmx

pygame.init()
current_level = "level1"
infoObject = pygame.display.Info()
WINDOW_SIZE = WINDOW_WIDTH, WINDOW_HEIGHT = infoObject.current_w, infoObject.current_h - 60
game_rules = open(f"{MAPS_DIR}/{current_level}/game_rules.txt",
                  mode="r", encoding="utf8")
game_rules_list = dict()
for line in game_rules.readlines():
    line = line.split(";")
    game_rules_list[line[0]] = list(map(int, line[1].strip("\n").split(",")))


class GameField:

    def __init__(self, filename, free_tile, finish_tile):
        self.map = pytmx.load_pygame(f"{MAPS_DIR}/{current_level}/{filename}")
        self.height = self.map.height
        self.width = self.map.width
        self.tile_size = self.map.tilewidth
        self.free_tiles = free_tile
        self.finish_tile = finish_tile

    def render(self, screen, koeff):
        for y in range(self.height):
            for x in range(self.width):
                for i in range(3):
                    image = self.map.get_tile_image(x, y, i)
                    if image is not None:
                        screen.blit(image, (x * self.tile_size + koeff[0],
                                            y * self.tile_size + koeff[1]))

    def get_tile_id(self, position):
        if self.map.get_tile_gid(*position, 1) in self.map.tiledgidmap.keys():
            return self.map.tiledgidmap[self.map.get_tile_gid(*position, 1)]
        return 0

    def is_free(self, position):
        return self.get_tile_id(position) in self.free_tiles

    def find_path_step(self, start, target):
        x, y = start
        inf = 1000
        distance = [[inf] * self.width for _ in range(self.height)]
        distance[y][x] = 0
        prev = [[None] * self.width for _ in range(self.height)]
        queue = [(x, y)]
        while queue:
            x, y = queue.pop(0)
            for dx, dy in (1, 0), (0, 1), (-1, 0), (0, -1):
                next_x, next_y = x + dx, y + dy
                if 0 <= next_x < self.width and 0 <= next_y < self.height and \
                        self.is_free((next_x, next_y)) and \
                        distance[next_y][next_x] == inf:
                    distance[next_y][next_x] = distance[y][x] + 1
                    prev[next_y][next_x] = (x, y)
                    queue.append((next_x, next_y))

        x, y = target
        if distance[y][x] == inf or start == target:
            return start
        while prev[y][x] != start:
            x, y = prev[y][x]
        return x, y


class Configurator:

    def __init__(self, filename):
        self.map = pytmx.load_pygame(f"{MAPS_DIR}/{current_level}/{filename}")
        self.height = self.map.height
        self.width = self.map.width
        self.tile_size = self.map.tilewidth
        self.x, self.y = 0, 0

    def render(self, screen, koeff):
        for y in range(self.height):
            for x in range(self.width):
                image = self.map.get_tile_image(x, y, 0)
                screen.blit(image, (self.x + x * TILE_SIZE + koeff[0],
                                    self.y + y * TILE_SIZE + koeff[1]))

    def set_position(self, position):
        self.x, self.y = position


class Enemy:

    def __init__(self, position, must_start, must_stop):
        self.x, self.y = position
        self.delay = 100
        self.must_start_y = must_start[1]
        self.must_start_x = must_start[0]
        self.must_stop_y = must_stop[1]
        self.must_stop_x = must_stop[0]
        pygame.time.set_timer(ENEMY_EVENT_TYPE, self.delay)

    def get_position(self):
        return self.x, self.y

    def set_position(self, position):
        self.x, self.y = position

    def render(self, screen, koeff):
        center = self.x * TILE_SIZE + TILE_SIZE // 2 + koeff[0], \
                 self.y * TILE_SIZE + TILE_SIZE // 2 + koeff[1]
        pygame.draw.circle(screen, (0, 0, 0), center, radius=TILE_SIZE // 2)


class Hero:

    def __init__(self, position):
        self.x, self.y = position

    def get_position(self):
        return self.x, self.y

    def set_position(self, position):
        self.x, self.y = position

    def render(self, screen, koeff):
        center = self.x * TILE_SIZE + TILE_SIZE // 2 + koeff[0], \
                 self.y * TILE_SIZE + TILE_SIZE // 2 + koeff[1]
        pygame.draw.circle(screen, (255, 255, 255), center, radius=TILE_SIZE // 2)


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, sheet, columns, rows, x, y):
        super().__init__(all_sprites)
        self.frames = []
        self.cut_sheet(sheet, columns, rows)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.rect.move(x, y)

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size)))

    def update(self):
        self.cur_frame = (self.cur_frame + 1) % len(self.frames)
        self.image = self.frames[self.cur_frame]

    def move(self, koeffs, hero):
        self.rect.update(hero.x * TILE_SIZE + koeffs[0], hero.y * TILE_SIZE + koeffs[1], 30, 30)


class Game:

    def __init__(self, field, hero, config, enemy):
        self.lab = field
        self.hero = hero
        self.config = config
        self.enemy = enemy
        self.enemy_start = False

    def render(self, screen, koeff):
        if self.hero.x == self.enemy.must_start_x and \
                self.hero.y == self.enemy.must_start_y:
            self.enemy_start = not self.enemy_start
        if self.hero.x == self.enemy.must_stop_x and \
                self.hero.y == self.enemy.must_stop_y:
            self.enemy_start = not self.enemy_start

        self.lab.render(screen, koeff)
        # self.hero.render(screen, koeff)
        self.enemy.render(screen, koeff)
        self.config.render(screen, koeff)

    def update_hero(self):
        next_x, next_y = self.hero.get_position()
        if pygame.key.get_pressed()[pygame.K_LEFT]:
            next_x -= 1
        if pygame.key.get_pressed()[pygame.K_RIGHT]:
            next_x += 1
        if pygame.key.get_pressed()[pygame.K_UP]:
            next_y -= 1
        if pygame.key.get_pressed()[pygame.K_DOWN]:
            next_y += 1

        if self.lab.is_free((next_x, next_y)):
            self.hero.set_position((next_x, next_y))

    def update_conf(self):
        direction_x = (self.hero.x * TILE_SIZE) - self.config.x
        if abs(direction_x) > 100:
            self.config.x += 100 // FPS * (1 if direction_x > 0 else -1)
        elif abs(direction_x) < 90:
            self.config.x -= 100 // FPS * (1 if direction_x > 0 else -1)

        direction_y = (self.hero.y * TILE_SIZE) - self.config.y
        if abs(direction_y) > 300:
            self.config.y += 100 // FPS * (1 if direction_y > 0 else -1)
        elif abs(direction_y) < 250:
            self.config.y -= 100 // FPS * (1 if direction_y > 0 else -1)

    def move_enemy(self):
        if self.enemy_start:
            next_position = self.lab.find_path_step(self.enemy.get_position(),
                                                    self.hero.get_position())
            self.enemy.set_position(next_position)

    def check_win(self):
        return self.lab.get_tile_id(self.hero.get_position()) == \
               self.lab.finish_tile

    def check_lose(self):
        return self.hero.get_position() == self.enemy.get_position()


class Camera:
    # зададим начальный сдвиг камеры
    def __init__(self):
        self.dx = 0
        self.dy = 0

    # позиционировать камеру на объекте target
    def update(self, target):
        self.dx += -(target.x * TILE_SIZE + self.dx + TILE_SIZE - WINDOW_WIDTH // 2)
        self.dy += -(target.y * TILE_SIZE + self.dy + TILE_SIZE - WINDOW_HEIGHT // 2)


def show_message(screen, message):
    font = pygame.font.Font(None, 50)
    text = font.render(message, True, (50, 70, 0))
    text_x = WINDOW_WIDTH // 2 - text.get_width() // 2
    text_y = WINDOW_HEIGHT // 2 - text.get_height() // 2
    text_w = text.get_width()
    text_h = text.get_height()
    pygame.draw.rect(screen, (200, 150, 50), (text_x - 10, text_y - 10,
                                              text_w + 20, text_h + 20))
    screen.blit(text, (text_x, text_y))


def load_image(name, colorkey=None):
    fullname = name
    # если файл не существует, то выходим
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    return image


screen_rect = (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)


class Particle(pygame.sprite.Sprite):
    # сгенерируем частицы разного размера
    fire = [load_image("grafic/star.png")]
    for scale in (5, 10, 20):
        fire.append(pygame.transform.scale(fire[0], (scale, scale)))

    def __init__(self, pos, dx, dy):
        super().__init__(all_sprites)
        self.image = random.choice(self.fire)
        self.rect = self.image.get_rect()

        # у каждой частицы своя скорость — это вектор
        self.velocity = [dx, dy]
        # и свои координаты
        self.rect.x, self.rect.y = pos

        # гравитация будет одинаковой (значение константы)
        self.gravity = GRAVITY

    def update(self):
        # применяем гравитационный эффект:
        # движение с ускорением под действием гравитации
        self.velocity[1] += self.gravity
        # перемещаем частицу
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]
        # убиваем, если частица ушла за экран
        if not self.rect.colliderect(screen_rect):
            self.kill()


def create_particles(position):
    # количество создаваемых частиц
    particle_count = 20
    # возможные скорости
    numbers = range(-5, 6)
    for _ in range(particle_count):
        Particle(position, random.choice(numbers), random.choice(numbers))


def main():
    pygame.display.set_caption('Coronavirus')
    screen = pygame.display.set_mode(WINDOW_SIZE)

    field = GameField("map.tmx", [78, 79, 80, 48, 49, 50, 108, 109, 110, 101], 101)
    hero = Hero((3, 13))
    config = Configurator("config.tmx")
    enemy = Enemy(game_rules_list["enemy_pos1"], game_rules_list["enemy1_start"],
                  game_rules_list["enemy1_stop"])
    dragon = AnimatedSprite(load_image("grafic\hero.png", -1), 8, 2, 3 * TILE_SIZE, 13 * TILE_SIZE)
    game = Game(field, hero, config, enemy)
    camera = Camera()

    running = True
    game_over = False
    clock = pygame.time.Clock()
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == ENEMY_EVENT_TYPE and not game_over:
                game.move_enemy()
        screen.fill((229, 213, 164))
        if not game_over:
            game.update_hero()
        game.render(screen, (camera.dx, camera.dy))
        game.update_conf()
        camera.update(hero)
        dragon.move((camera.dx, camera.dy), hero)
        all_sprites.update()
        all_sprites.draw(screen)
        if game.check_win():
            game_over = True
            show_message(screen, "You won!")
            create_particles((WINDOW_WIDTH // 2, 0))
        if game.check_lose():
            game_over = True
            show_message(screen, "You lost!")
        clock.tick(FPS)
        pygame.display.flip()
    pygame.quit()


if __name__ == '__main__':
    pygame.mixer.init()
    pygame.mixer.music.load('sounds/soundtrack1.mp3')
    pygame.mixer.music.play(-1)
    all_sprites = pygame.sprite.Group()
    main()
