import sys
import pygame.display

import get_MIC
from get_MIC import *
from sprite_loader import *
from UI import *

pygame.init()
pygame.display.set_caption("Scream Frog")

FPS = 60
PLAYER_VEL = 5
scroll = 0
clock = pygame.time.Clock()
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

loudness_threshold = 200
current_scene = "START_SCENE"
death_trigger = False
death_time = None
finish_time = None
objects = []


class Player(pygame.sprite.Sprite):
    '''
    inheritance sprites easier to do pixel perfect collision
    '''
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("Sprites", "Frog", 32, 32, True)
    ANIMATION_DELAY = 3
    global current_scene

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0
        self.isHurting = False

    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        # self.x_vel = PLAYER_VEL * 10
        # count to avoid infinite jumping
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def make_hit(self):
        self.hit = True

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
            self.isHurting = True
        if self.hit_count > fps:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    # adding the hit_head will make games too hard so comment it temporary
    def hit_head(self):
        # self.y_vel = -1
        self.count = 1

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))


def draw(window, bg_images, bg_width, player, objects, firework_obj, offset_x):
    """
    Draws the game scene, including background, player, and objects.
    """
    global finished

    # parallel background, each layer move in different vel, makes 2d looks like 3d
    for x in range(5):
        bg_speed = 0.1
        for i in bg_images:
            window.blit(i, ((x * bg_width) - scroll * bg_speed, 0))
            bg_speed += 0.2

    for obj in objects:
        obj.draw(window, offset_x)

    player.draw(window, offset_x)

    # when finished set on fireworks
    if finished:
        for obj in firework_obj:
            obj.on()
            obj.loop()
            obj.draw(window, offset_x)

    # pygame.display.update()


def handle_vertical_collision(player, objects, dy):
    """
    Handles vertical collisions for the player and updates position/state.
    """
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()

            collided_objects.append(obj)

    return collided_objects


def collide(player, objects, dx):
    """
    Checks for horizontal collisions between the player and objects.
    """
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break

    player.move(-dx, 0)
    player.update()
    return collided_object



def handle_move(player, objects):
    '''
    Handles the movement of the player
    Remains keyboard input to convenient show
    '''
    global current_scene
    global death_trigger
    global death_time
    objects = [obj for obj in objects if
               not isinstance(obj, StartingPoint) and not isinstance(obj, FinishPoint) and not isinstance(obj,
                                                                                                          Firework)]
    global scroll
    keys = pygame.key.get_pressed()

    # check left and right if will collide
    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)

    # move and handles the parallel background scroll
    if keys[pygame.K_LEFT] and not collide_left:
        player.move_left(PLAYER_VEL)
        if scroll > 0:
            scroll -= 5
    if keys[pygame.K_RIGHT] and not collide_right:
        player.move_right(PLAYER_VEL)
        if scroll < 6000:
            scroll += 5

    if get_MIC.loudness > loudness_threshold and player.jump_count < 2:
        player.jump()
    if get_MIC.loudness > 5 and not collide_right:
        player.move_right(PLAYER_VEL)
        if scroll < 3000:
            scroll += 5

    # fall off the game scene then die
    if player.rect.y > WINDOW_HEIGHT + 10 and not finished:
        player.make_hit()
        death_trigger = True
        death_time = pygame.time.get_ticks()

    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    to_check = [collide_left, collide_right, *vertical_collide]

    # collision interaction
    for obj in to_check:
        if obj and obj.name == "Spike":
            player.make_hit()
            death_trigger = True
            death_time = pygame.time.get_ticks()
        elif obj and obj.name == "stick":
            obj.shaking = True


def check_finish(player, finish_point):
    """
    Checks if the player has touched the FinishPoint.
    """
    return pygame.sprite.collide_rect(player, finish_point)


def GAME_SCENE(window):
    global current_scene
    global finished
    global objects
    global death_trigger
    global death_time
    global finish_time

    mic_icon = Icon(80, 80, "./assets/UI/mic_idle.png", "./assets/UI/mic_loud.png", scale_factor=1.1, shake_amplitude=8)

    clock = pygame.time.Clock()
    bg_images, bg_width = get_background()

    player = Player(50, 200, 32, 32)
    # player = Player(50, 200, radius=16)
    tmx_map = "./Level/Level1_map.tmx"
    objects, firework_obj = load_objects_from_tmx(tmx_map)

    offset_x = 0
    scroll_area_width = 200

    mic_thread_instance = threading.Thread(target=mic_thread, daemon=True)
    mic_thread_instance.start()

    run = True
    while run:
        if current_scene != "GAME_SCENE":
            return "RESTART_SCENE"
        clock.tick(FPS)

        loudness_tmp = get_MIC.loudness
        if loudness_tmp > loudness_threshold:
            mic_icon.set_state("loud2")
        elif loudness_tmp > 5:
            mic_icon.set_state("loud")
        else:
            mic_icon.set_state("idle")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()

        player.loop(FPS)

        for obj in objects:
            if isinstance(obj, BreakingStick) and obj.shaking:
                # objects.remove(obj)
                objects = obj.update(player, objects)
            elif isinstance(obj, StartingPoint):
                obj.loop()
            elif isinstance(obj, FinishPoint):
                obj.loop()
                if not finished and check_finish(player, obj):
                    finished = True
                    finish_time = pygame.time.get_ticks()

        draw(window, bg_images, bg_width, player, objects, firework_obj, offset_x)
        mic_icon.draw(window)
        pygame.display.update()

        if not death_trigger:
            handle_move(player, objects)
        elif death_trigger and pygame.time.get_ticks() - death_time > 1500:
            current_scene = "RESTART_SCENE"
        if finished and pygame.time.get_ticks() - finish_time > 1500:
            current_scene = "RESTART_SCENE"

        # camera scroll effect
        if ((player.rect.right - offset_x >= WINDOW_WIDTH - scroll_area_width) and player.x_vel > 0) or (
                (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel

    pygame.quit()
    quit()


def START_SCENE():
    play_button = Button(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50, "Play", button_sprite)
    settings_button = Button(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50, "Mic Set", button_sprite)
    background_image = pygame.image.load("./assets/Background/Whole_Background.png").convert()
    background_image = pygame.transform.scale2x(background_image)

    while True:
        window.blit(background_image, (0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if play_button.is_clicked(event):
                return "GAME_SCENE"
            elif settings_button.is_clicked(event):
                return "SETTING_SCENE"

        play_button.check_hover()
        settings_button.check_hover()

        play_button.draw(window)
        settings_button.draw(window)

        pygame.display.update()
        clock.tick(FPS)


def RESTART_SCENE():
    restart_button = Button(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50, "Again", button_sprite)
    settings_button = Button(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50, "Mic Set", button_sprite)
    global death_time
    global death_trigger
    global finished
    global finish_time
    text_context = 'YOU LOSE!' if death_trigger else 'YOU WON!'
    text_surface = FONT.render(text_context, True, (255, 255, 255))
    text_rect = text_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 150))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if death_time != None:
                death_time, death_trigger = None, False
            elif finish_time != None:
                finish_time, finished = None, False
            if restart_button.is_clicked(event):
                # death_time, finish_time= None
                # death_trigger, finished = False
                return "GAME_SCENE"
            elif settings_button.is_clicked(event):

                return "SETTING_SCENE"

        restart_button.check_hover()
        settings_button.check_hover()

        window.blit(text_surface, text_rect)
        restart_button.draw(window)
        settings_button.draw(window)

        pygame.display.update()
        clock.tick(FPS)


def SETTING_SCENE():
    global loudness_threshold
    slider = Slider(WINDOW_WIDTH // 2 - 150, WINDOW_HEIGHT // 2, 300, 10, min_val=100, max_val=300,
                    initial_val=loudness_threshold)
    back_button = Button(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 100, "Back", button_sprite)

    background_image = pygame.image.load("./assets/Background/Whole_Background.png").convert()
    background_image = pygame.transform.scale2x(background_image)

    label_surface = FONT.render("Intensity", True, (255, 255, 255))

    label_position = (slider.x + slider.width // 2 - label_surface.get_width() // 2,
                      slider.y - label_surface.get_height() - 50)

    while True:
        window.blit(background_image, (0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            loudness_threshold = slider.handle_event(event, loudness_threshold)
            if back_button.is_clicked(event):
                return "START_SCENE"

        back_button.check_hover()

        slider.draw(window)
        back_button.draw(window)
        window.blit(label_surface, label_position)

        pygame.display.update()
        clock.tick(FPS)




def main():
    global current_scene
    current_scene = "START_SCENE"

    while True:
        # print(loudness_threshold)
        if current_scene == "START_SCENE":
            current_scene = START_SCENE()
        elif current_scene == "GAME_SCENE":
            current_scene = GAME_SCENE(window)
        elif current_scene == "RESTART_SCENE":
            current_scene = RESTART_SCENE()
        elif current_scene == "SETTING_SCENE":
            current_scene = SETTING_SCENE()


if __name__ == "__main__":
    main()
