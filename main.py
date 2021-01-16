import pygame
from constants import *
import pytmx


class GameField:

    def __init__(self, filename, free_tile, finish_tile):
        self.map = pytmx.load_pygame(f"{MAPS_DIR}/{filename}")
        self.height = self.map.height
        self.width = self.map.width
        self.tile_size = self.map.tilewidth
        self.free_tiles = free_tile
        self.finish_tile = finish_tile

    def render(self, screen):
        for y in range(self.height):
            for x in range(self.width):
                for i in range(3):
                    image = self.map.get_tile_image(x, y, i)
                    if image is not None:
                        screen.blit(image, (x * self.tile_size, y * self.tile_size))

    def get_tile_id(self, position):
        if self.map.get_tile_gid(*position, 1) in self.map.tiledgidmap.keys():
            return self.map.tiledgidmap[self.map.get_tile_gid(*position, 1)]
        return 0

    def is_free(self, position):
        return self.get_tile_id(position) in self.free_tiles


class Hero:

    def __init__(self, position):
        self.x, self.y = position

    def get_position(self):
        return self.x, self.y

    def set_position(self, position):
        self.x, self.y = position

    def render(self, screen):
        center = self.x * TILE_SIZE + TILE_SIZE // 2, self.y * TILE_SIZE + TILE_SIZE // 2
        pygame.draw.circle(screen, (255, 255, 255), center, radius=TILE_SIZE // 2)


class Game:

    def __init__(self, field, hero):
        self.lab = field
        self.hero = hero

    def render(self, screen):
        self.lab.render(screen)
        self.hero.render(screen)

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
        print(self.lab.get_tile_id((next_x, next_y)))
        if self.lab.is_free((next_x, next_y)):
            self.hero.set_position((next_x, next_y))


def main():
    pygame.init()
    pygame.display.set_caption('Coronavirus')
    infoObject = pygame.display.Info()
    screen = pygame.display.set_mode((infoObject.current_w, infoObject.current_h - 60))

    field = GameField("map.tmx", [78, 79, 80, 48, 49, 50, 108, 109, 110], 0)
    hero = Hero((3, 13))
    game = Game(field, hero)

    running = True
    clock = pygame.time.Clock()
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        screen.fill((255, 228, 225))

        game.update_hero()
        game.render(screen)

        clock.tick(FPS)
        pygame.display.flip()
    pygame.quit()


if __name__ == '__main__':
    main()
