import os
import random
import sys

import pygame
import pygame_gui
import pytmx

from constants import *


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

    def __init__(self, field, hero, enemy):
        self.lab = field
        self.hero = hero
        self.enemy = enemy
        self.enemy_start = False

    def render(self, screen, koeff):
        self.lab.render(screen, koeff)
        # self.hero.render(screen, koeff)
        self.enemy.render(screen, koeff)

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

        if self.hero.x == self.enemy.must_start_x and \
                self.hero.y == self.enemy.must_start_y:
            self.enemy_start = not self.enemy_start
        if self.hero.x == self.enemy.must_stop_x and \
                self.hero.y == self.enemy.must_stop_y:
            self.enemy_start = not self.enemy_start

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


def show_message(screen, message, cords=None):
    font = pygame.font.Font(None, 50)
    text = font.render(message, True, (50, 70, 0))
    if cords is None:
        text_x = WINDOW_WIDTH // 2 - text.get_width() // 2
        text_y = WINDOW_HEIGHT // 2 - text.get_height() // 2
    else:
        text_x, text_y = cords[0], cords[1]
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


class Particle(pygame.sprite.Sprite):
    # сгенерируем частицы разного размера
    fire = [load_image("grafic/star.png")]
    for scale in (5, 10, 20):
        fire.append(pygame.transform.scale(fire[0], (scale, scale)))

    def __init__(self, pos, dx, dy):
        super().__init__(effects_sprites)
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
    particle_count = 10
    # возможные скорости
    numbers = range(-5, 6)
    for _ in range(particle_count):
        Particle(position, random.choice(numbers), random.choice(numbers))


def menu(status, screen):

    def hide(wdgts, hide):
        for wdg in wdgts:
            wdg.hide() if hide else wdg.show()

    pause_btns = [btn_resume, btn_close, btn_menu]
    win_btns = [btn_menu_for_win]
    lose_btns = [btn_menu_for_lost]
    menu_btns = [*levels_btns, btn_close_game]
    hide(win_btns + lose_btns + menu_btns + [btn_pause] + pause_btns, hide=True)
    if status == GAME:
        media_player.play(0)
        hide([btn_pause], hide=False)
    elif status == WIN:
        media_player.play(3)
        show_message(screen, "YOU WIN!")
        hide(win_btns, hide=False)
        create_particles((WINDOW_WIDTH // 2, 0))
    elif status == LOSE:
        media_player.play(2)
        show_message(screen, "YOU LOST!")
        hide(lose_btns, hide=False)
    elif status == MENU:
        show_message(screen, "LEVELS", cords=(WINDOW_WIDTH // 2, 30))
        hide(menu_btns, hide=False)
        media_player.play(1)
    elif status == PAUSE:
        image = load_image("grafic/background.png", -1)
        screen.blit(image, (WINDOW_WIDTH // 2 - image.get_width() // 2,
                            WINDOW_HEIGHT // 2 - image.get_height() // 2))
        hide(pause_btns, hide=False)


class Player:

    def __init__(self, musics):
        self.musics = musics
        self.play_music = [False] * len(self.musics)

    def play(self, i):
        if self.play_music[i] is False:
            self.play_music = [False] * len(self.musics)
            self.all_stop()
            self.play_music[i] = True
            self.musics[i].play(-1)

    def all_stop(self):
        for music in self.musics:
            music.stop()


def main():
    pygame.display.set_caption('Coronavirus')
    screen = pygame.display.set_mode(WINDOW_SIZE)

    field = GameField("map.tmx", [78, 79, 80, 48, 49, 50, 108, 109, 110, 101], 101)
    hero = Hero(game_rules_list["start_character_pos"])
    enemy = Enemy(game_rules_list["enemy_pos1"], game_rules_list["enemy1_start"],
                  game_rules_list["enemy1_stop"])
    dragon = AnimatedSprite(load_image("grafic\hero.png", -1), 8, 2, 3 * TILE_SIZE, 13 * TILE_SIZE)
    game = Game(field, hero, enemy)
    camera = Camera()

    running = True
    status = MENU
    clock = pygame.time.Clock()
    while running:
        time_delta = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == ENEMY_EVENT_TYPE and status == GAME:
                game.move_enemy()
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == btn_pause:
                        status = PAUSE
                    if event.ui_element == btn_resume:
                        status = GAME
                    if event.ui_element in (btn_close, btn_close_game):
                        running = False
                    if event.ui_element in (btn_menu, btn_menu_for_win,
                                            btn_menu_for_lost):
                        status = MENU
                    if event.ui_element in levels_btns:
                        global current_level
                        current_level = LEVELS_DIR[levels_btns.index(event.ui_element)]
                        load_rules()

                        field = GameField("map.tmx", [78, 79, 80, 48, 49, 50, 108, 109, 110, 101], 101)
                        hero = Hero(game_rules_list["start_character_pos"])
                        enemy = Enemy(game_rules_list["enemy_pos1"], game_rules_list["enemy1_start"],
                                      game_rules_list["enemy1_stop"])
                        game = Game(field, hero, enemy)
                        status = GAME

            manager.process_events(event)
        manager.update(time_delta)

        screen.fill((229, 213, 164))

        if status == GAME:
            game.update_hero()
            camera.update(hero)
            dragon.move((camera.dx, camera.dy), hero)

        if status in (GAME, PAUSE):
            game.render(screen, (camera.dx, camera.dy))
            all_sprites.draw(screen)
            all_sprites.update()

        effects_sprites.update()
        effects_sprites.draw(screen)

        menu(status, screen)
        manager.draw_ui(screen)

        if game.check_win() and status == GAME:
            status = WIN
        if game.check_lose() and status == GAME:
            status = LOSE

        clock.tick(FPS)
        pygame.display.flip()
    pygame.quit()


def load_rules():
    game_rules = open(f"{MAPS_DIR}/{current_level}/game_rules.txt",
                      mode="r", encoding="utf8")
    game_rules_list = dict()
    for line in game_rules.readlines():
        line = line.split(";")
        game_rules_list[line[0]] = list(map(int, line[1].strip("\n").split(",")))
    return game_rules_list


if __name__ == '__main__':
    pygame.mixer.init()
    game_sound = pygame.mixer.Sound('sounds/soundtrack1.mp3')
    menu_sound = pygame.mixer.Sound('sounds/menu.mp3')
    lost_sound = pygame.mixer.Sound('sounds/lost.mp3')
    win_sound = pygame.mixer.Sound('sounds/win.mp3')
    media_player = Player([game_sound, menu_sound, lost_sound, win_sound])
    pygame.init()

    current_level = "level1"
    infoObject = pygame.display.Info()
    WINDOW_SIZE = WINDOW_WIDTH, WINDOW_HEIGHT = infoObject.current_w, infoObject.current_h
    screen_rect = (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    game_rules_list = load_rules()

    all_sprites = pygame.sprite.Group()
    effects_sprites = pygame.sprite.Group()

    manager = pygame_gui.UIManager(WINDOW_SIZE)

    btn_pause = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((WINDOW_WIDTH - 70, 0), (70, 70)),
        text="Pause",
        manager=manager
    )

    btn_resume = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2 + 100), (200, 70)),
        text="Resume play",
        manager=manager
    )

    btn_close = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2 - 100), (200, 70)),
        text="Close game",
        manager=manager
    )

    btn_menu = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2), (200, 70)),
        text="Menu",
        manager=manager
    )

    btn_menu_for_win = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2 + 100), (200, 70)),
        text="Menu",
        manager=manager
    )

    btn_menu_for_lost = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2 + 100), (200, 70)),
        text="Menu",
        manager=manager
    )

    btn_close_game = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT - 200), (200, 70)),
        text="Exit game",
        manager=manager
    )

    levels_btns = list()
    for i in range(len(LEVELS_DIR)):
        btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WINDOW_WIDTH // 2 - 300 + 100 * (i % 3),
                                       WINDOW_HEIGHT // 2 - 300 + 100 * (i // 3)), (70, 70)),
            text=f"{i + 1}",
            manager=manager
        )
        levels_btns.append(btn)

    main()
