import pygame
import math
pygame.init()
pygame.font.init()

FONT_SIZE = 36
FONT = pygame.font.SysFont("Algerian", FONT_SIZE)
button_sprite = pygame.image.load("./assets/UI/button.png")
BUTTON_SCALE = 2  # Default scale
HOVER_SCALE = 2.2  # Scale when hovered

WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
BLUE = (50, 150, 255)

WINDOW_WIDTH, WINDOW_HEIGHT = 500, 816


def get_background():
    """
    Load and scale multiple background layers to fit the window height
    while preserving the aspect ratio.
    """
    bg_images = []
    for i in range(1, 6):
        bg_image = pygame.image.load(f"./assets/Background/plx-{i}.png").convert_alpha()
        # scaling the image by WINDOW size
        scale_factor = WINDOW_HEIGHT / bg_image.get_height()
        new_width = int(bg_image.get_width() * scale_factor)
        new_height = WINDOW_HEIGHT
        scaled_bg_image = pygame.transform.scale(bg_image, (new_width, new_height))

        bg_images.append(scaled_bg_image)

    bg_width = bg_images[0].get_width()

    return bg_images, bg_width


class Button:
    def __init__(self, x, y, text, image, scale=BUTTON_SCALE):
        self.x = x
        self.y = y
        self.text = text
        self.image = image
        self.default_scale = scale
        self.hover_scale = HOVER_SCALE
        self.rect = self.image.get_rect(center=(x, y))
        self.is_hovered = False

    def draw(self, surface):
        """
        Draws the button and its text on the given surface.
        """
        # Enlarge the button if hovered
        scale = self.hover_scale if self.is_hovered else self.default_scale
        scaled_image = pygame.transform.scale(
            self.image, (int(self.image.get_width() * scale), int(self.image.get_height() * scale))
        )
        scaled_rect = scaled_image.get_rect(center=(self.x, self.y))
        surface.blit(scaled_image, scaled_rect)

        text_font_size = int(FONT_SIZE * scale / BUTTON_SCALE)  # Scale the font size
        # scaled_font = pygame.font.Font(None, text_font_size)  # Create a scaled font
        scaled_font = pygame.font.SysFont("Algerian", text_font_size)
        text_surface = scaled_font.render(self.text, True, (255, 255, 255))  # White text
        text_rect = text_surface.get_rect(center=(self.x, self.y))
        surface.blit(text_surface, text_rect)

        # Update the rect for hover detection
        self.rect = scaled_rect

    def check_hover(self):
        """
        Checks if the mouse is hovering over the button.
        """
        pos = pygame.mouse.get_pos()
        self.is_hovered = self.rect.collidepoint(pos)

    def is_clicked(self, event):
        """
        Detects if the button is clicked on a MOUSEBUTTONDOWN event.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and self.is_hovered:
            return True
        return False


class Slider:
    def __init__(self, x, y, width, height, min_val=100, max_val=300, initial_val=150):
        """
        Initializes the slider with the given range and initial value.
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.dragging = False

        self.slider_rect = pygame.Rect(self.x, self.y, width, height)
        self.handle_rect = pygame.Rect(
            self.x + ((initial_val - min_val) / (max_val - min_val)) * width - 10,
            self.y - 10,
            20,
            self.height + 20
        )

    def draw(self, surface):
        """
        Draws the slider bar, handle, and current value.
        """
        pygame.draw.rect(surface, GRAY, self.slider_rect)
        pygame.draw.rect(surface, BLUE, self.handle_rect)

        text_surface = FONT.render(f"{int(self.value)}", True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=(self.handle_rect.centerx, self.handle_rect.top - 20))
        surface.blit(text_surface, text_rect)

    def handle_event(self, event, loudness_threshold):
        """
        Handles mouse events to drag the slider handle and update the value.
        Updates the global loudness_threshold variable.
        """
        # global loudness_threshold

        # is or not dragging
        if event.type == pygame.MOUSEBUTTONDOWN and self.handle_rect.collidepoint(event.pos):
            self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        # update the position by mouse
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            # make sure the block with in the range
            new_x = max(self.x, min(event.pos[0], self.x + self.width))
            self.handle_rect.centerx = new_x
            self.value = ((new_x - self.x) / self.width) * (self.max_val - self.min_val) + self.min_val

            loudness_threshold = int(self.value)

        return loudness_threshold

class Icon:
    """
    Icon (mainly used for microphone)
    """

    def __init__(self, x, y, idle_sprite_path, state_sprite_path, scale_factor=1.0, shake_amplitude=0):
        self.x = x
        self.y = y
        self.scale_factor = scale_factor
        self.shake_amplitude = shake_amplitude
        self.state = "idle"
        self.shake_time = None

        # load sprite
        self.idle_sprite = pygame.image.load(idle_sprite_path).convert_alpha()
        self.state_sprite = pygame.image.load(state_sprite_path).convert_alpha()

        self.idle_sprite = pygame.transform.scale(
            self.idle_sprite,
            (int(self.idle_sprite.get_width()), int(self.idle_sprite.get_height()))
        )
        self.state_sprite = pygame.transform.scale(
            self.state_sprite,
            (int(self.state_sprite.get_width() * scale_factor), int(self.state_sprite.get_height() * scale_factor))
        )

        self.current_sprite = self.idle_sprite

    def set_state(self, state):
        self.state = state
        if state == "idle":
            self.current_sprite = self.idle_sprite
        elif state in ["loud", "loud2"]:
            self.current_sprite = self.state_sprite

    def get_shaking_position(self):
        if self.state == "loud2":
            self.shake_time = pygame.time.get_ticks()
            frequency = 40
            offset_x = int(math.sin(self.shake_time * frequency / 1000) * self.shake_amplitude)
            offset_y = int(math.cos(self.shake_time * frequency / 1000) * self.shake_amplitude)
            return self.x + offset_x, self.y + offset_y
        return self.x, self.y

    def draw(self, surface):
        position = self.get_shaking_position() if self.state == "loud2" else (self.x, self.y)
        surface.blit(self.current_sprite, position)

