import pygame
import time
import math
from os import listdir
from os.path import isfile, join
import random
from pytmx import load_pygame

finished = False

def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]

def load_objects_from_tmx(tmx_file):
    tmx_data = load_pygame(tmx_file)
    block_size = tmx_data.tilewidth

    objects = []
    firework_objects = []

    for layer in tmx_data.visible_layers:
        if hasattr(layer, "tiles"):
            for x, y, surface in layer.tiles():
                # Access tile properties
                props = tmx_data.get_tile_properties_by_gid(layer.data[y][x])
                tile_type = props.get("type", None) if props else None

                if tile_type == "grassBlock":
                    block = GrassBlock(x * block_size, y * block_size, block_size)
                    objects.append(block)
                elif tile_type == "stick":
                    block = BreakingStick(x * block_size, y * block_size, block_size, block_size)
                    objects.append(block)
                elif tile_type == "Spike":
                    block = Spike(x * block_size, y * block_size, block_size)
                    objects.append(block)
                elif tile_type == "startingPoint":
                    block = StartingPoint(x * block_size, 500, 64, 64)
                    objects.append(block)
                elif tile_type == "FinishPoint":
                    block = FinishPoint(x * block_size, 364, 64, 64)
                    objects.append(block)
                elif tile_type == "dirtBlock":
                    block = DirtBlock(x * block_size, y * block_size, block_size)
                    objects.append(block)
                elif tile_type == "fire":
                    fire = Fire(x * block_size, y * block_size - block_size, block_size, block_size)
                    objects.append(fire)
                elif tile_type == "firework":
                    block = Firework(x * block_size, 500, 256, 256)
                    firework_objects.append(block)

    return objects, firework_objects

def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        # convert alpha support transparency
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites


def get_block(size, x, y):
    path = join("Level", "Tilemap", "Level1_map.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(x, y, size, size)
    surface.blit(image, (0, 0), rect)
    # return pygame.transform.scale2x(surface)
    return surface

class Object(pygame.sprite.Sprite):

    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x=0):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))


class GrassBlock(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size, 96, 0)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


class DirtBlock(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size, 0, 192)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Sprites", "Fire", width, height)
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0


class BreakingStick(Object):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "stick")

        stick_sprite = get_block(width, 288, 0)
        self.image = stick_sprite
        self.mask = pygame.mask.from_surface(self.image)

        self.shaking = False
        self.broken = False
        self.animation_count = 0
        self.start_time = None
        self.shake_f = 50
        # store the pos to avoid stick moving away
        self.original_x = x
        self.original_y = y

    def update(self, player, obj):
        """Handles accurate shaking and breaking behavior."""
        if self.shaking:
            if self.start_time is None: self.start_time = time.time()
            elapsed_time = time.time() - self.start_time
            if elapsed_time < 0.5:
                shake_magnitude = 3
                offset_x = int(shake_magnitude * math.sin(elapsed_time * self.shake_f))
                offset_y = int(shake_magnitude * math.cos(elapsed_time * self.shake_f))

                self.rect.x = self.original_x + offset_x
                self.rect.y = self.original_y + offset_y
            else:
                if self in obj:
                    obj.remove(self)
                self.break_stick()
        else:
            # Ensure stick returns to original position
            self.rect.x = self.original_x
            self.rect.y = self.original_y
        return obj

    def break_stick(self):
        """Sets the stick to the broken state and removes it."""
        del self



class Spike(Object):
    '''
    Spike object that hurts
    '''
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size, "Spike")
        block = get_block(size, 384, 0)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


class StartingPoint(Object):
    '''
    The initial decoration with an arrow
    '''
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "startPoint")
        self.point = load_sprite_sheets("Sprites", "Start", width, height)
        self.image = self.point["move"][0]
        # self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "move"

    def loop(self):
        sprites = self.point[self.animation_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0


class FinishPoint(Object):
    '''
    The end check point
    '''
    ANIMATION_DELAY = 8

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "EndPoint")
        self.point = load_sprite_sheets("Sprites", "End", width, height)
        self.image = self.point["move"][0]
        self.animation_count = 0
        self.animation_name = "move"


    def loop(self):
        sprites = self.point[self.animation_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0


class Firework(Object):
    ANIMATION_DELAY = 7
    type_num = 1

    global finished

    def __init__(self, x, y, width, height, type_num=1):
        super().__init__(x, y, width, height, "Firework")
        self.point = load_sprite_sheets("Sprites", "Firework", width, height)
        self.image = self.point[f"firework{type_num}"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = None

    def on(self):
        self.animation_name = f"firework{self.type_num}"

    def loop(self):
        if self.rect.y > 0:
            self.rect.y -= 15
        else:
            self.rect.y = 500
            self.type_num = random.randint(1, 3)

        sprites = self.point[self.animation_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0

