#!/usr/bin/env python3
"""
Pearl the Jaguar - Tamagotchi (PyGame GUI Prototype)
Screen Dimensions: 800 x 480 pixels (Standard 7" Display / 5:3 Landscape Ratio)
"""

import sys
import os
import pygame
from PIL import Image
from pearl_state import Pearl, PearlState

def load_gif_frames(filepath, target_size=(230, 230)):
    """
    Extracts all frames from a .gif file into Pygame surfaces.
    """
    gif = Image.open(filepath)
    frames = []
    try:
        while True:
            frame_rgba = gif.convert("RGBA")
            data = frame_rgba.tobytes()
            size = frame_rgba.size
            surf = pygame.image.fromstring(data, size, "RGBA")
            scaled_surf = pygame.transform.scale(surf, target_size)
            frames.append(scaled_surf)
            gif.seek(gif.tell() + 1)
    except EOFError:
        pass
    return frames

def load_video_frames(filepath, target_size=(230, 230), max_frames=150):
    """
    Extracts frames from a video file (.mp4, .mov, .avi) into Pygame surfaces.
    """
    try:
        import cv2
        cap = cv2.VideoCapture(filepath)
        frames = []
        count = 0
        while cap.isOpened() and count < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_surf = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
            scaled_surf = pygame.transform.scale(frame_surf, target_size)
            frames.append(scaled_surf)
            count += 1
        cap.release()
        return frames
    except Exception as e:
        print(f"Note: Install 'opencv-python' to parse video files ({filepath}): {e}")
        return []

def make_rounded_rect_surface(surface, target_size, border_radius=12):
    """
    Scales and clips a surface into a sleek rounded rectangle fitting the main viewport area.
    """
    width, height = target_size
    scaled = pygame.transform.smoothscale(surface, (width, height))
    if pygame.display.get_surface() is not None:
        scaled = scaled.convert_alpha()
    
    mask = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, width, height), border_radius=border_radius)
    
    rounded_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    rounded_surf.blit(scaled, (0, 0))
    rounded_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return rounded_surf

def load_asset_frames(basenames, target_size=(466, 280), border_radius=12):
    """
    Tries loading frames for the first matching basename in `basenames`.
    Checks extensions: .mp4, .mov, .gif, .png, .jpg, .jpeg, .webp (case-insensitive).
    Scales images to rectangular space with rounded corners.
    """
    if isinstance(basenames, str):
        basenames = [basenames]

    extensions = [".mp4", ".mov", ".gif", ".png", ".jpg", ".jpeg", ".webp"]

    for bname in basenames:
        for ext in extensions:
            for test_ext in [ext, ext.upper()]:
                filepath = os.path.join("assets", f"{bname}{test_ext}")
                if os.path.exists(filepath):
                    frames = []
                    ext_lower = test_ext.lower()
                    if ext_lower in [".mp4", ".mov"]:
                        frames = load_video_frames(filepath, target_size)
                    elif ext_lower == ".gif":
                        try:
                            frames = load_gif_frames(filepath, target_size)
                        except Exception as e:
                            print(f"Warning: Could not parse GIF {filepath}: {e}")
                    else:
                        try:
                            img = pygame.image.load(filepath)
                            if pygame.display.get_surface() is not None:
                                img = img.convert_alpha()
                            rounded_img = make_rounded_rect_surface(img, target_size, border_radius=border_radius)
                            frames = [rounded_img]
                        except Exception as e:
                            print(f"Warning: Could not load image {filepath}: {e}")
                    
                    if frames:
                        return frames
    return None

def create_fallback_surface(target_size=(466, 280)):
    surf = pygame.Surface(target_size, pygame.SRCALPHA)
    pygame.draw.rect(surf, (60, 65, 80), (0, 0, target_size[0], target_size[1]), border_radius=12)
    return surf

def load_image_assets():
    """
    Loads static images (.png/.jpg/.jpeg), GIFs (.gif), or Videos (.mp4/.mov) for Pearl's states and contexts.
    Returns a dict mapping state keys to lists of PyGame Surfaces.
    """
    assets = {}
    
    mapping = {
        PearlState.IDLE: ["pearl_idle"],
        PearlState.FEEDING: ["pearl_eat"],
        PearlState.PLAYING: ["pearl_play"],
        PearlState.STUDYING: ["pearl_study"],
        PearlState.DISTRESSED: ["pearl_distressed"],
        "night": ["pearl_night"],
        "weekend": ["pearl_weekend"],
        "eat_full": ["pearl_eat_full"],
    }
    
    target_size = (466, 280)

    for key, basenames in mapping.items():
        frames = load_asset_frames(basenames, target_size=target_size, border_radius=12)
        if frames:
            assets[key] = frames

    # Ensure at least IDLE fallback exists
    if PearlState.IDLE not in assets:
        assets[PearlState.IDLE] = [create_fallback_surface(target_size)]

    return assets

def get_current_pearl_frames(pearl, image_assets):
    """
    Dynamically returns the appropriate sprite frames based on Pearl's current state and real-time schedule/context.
    """
    sched = pearl.get_schedule_status()
    
    if pearl.state == PearlState.IDLE:
        if sched["is_night"] and "night" in image_assets:
            return image_assets["night"]
        elif sched["is_weekend"] and "weekend" in image_assets:
            return image_assets["weekend"]
        elif PearlState.IDLE in image_assets:
            return image_assets[PearlState.IDLE]

    elif pearl.state == PearlState.FEEDING:
        if pearl.hunger > 100 and "eat_full" in image_assets:
            return image_assets["eat_full"]
        elif PearlState.FEEDING in image_assets:
            return image_assets[PearlState.FEEDING]

    elif pearl.state == PearlState.PLAYING:
        if PearlState.PLAYING in image_assets:
            return image_assets[PearlState.PLAYING]

    elif pearl.state == PearlState.STUDYING:
        if PearlState.STUDYING in image_assets:
            return image_assets[PearlState.STUDYING]

    elif pearl.state == PearlState.DISTRESSED:
        if PearlState.DISTRESSED in image_assets:
            return image_assets[PearlState.DISTRESSED]

    return image_assets.get(PearlState.IDLE, [create_fallback_surface()])


def draw_status_bars(screen, font, pearl):
    """
    Draws 3 horizontal status bars across the top header with custom graphical icons,
    percentage numbers centered INSIDE the status bar, and critical red fill when < 30%.
    """
    # 3 Stat Configs (Stat Name, Value, Max Value, Normal Color, Icon Type, Icon X, Bar X)
    stats = [
        ("hunger", pearl.hunger, 100, (255, 140, 0), "hunger", 40, 72),
        ("happiness", pearl.happiness, 100, (230, 80, 180), "happiness", 290, 322),
        ("grades", pearl.grades, 100, (80, 180, 250), "grades", 540, 572),
    ]

    bar_width = 175
    bar_height = 26
    bar_top_y = 33

    for stat_name, raw_val, max_val, normal_color, icon_type, icon_x, start_x in stats:
        # Visually cap percentage display at 100% max
        display_val = min(100, max(0, int(raw_val)))

        # 1. Draw Graphical Icon
        if icon_type == "hunger":
            # Meat drumstick icon
            pygame.draw.ellipse(screen, (255, 140, 0), (icon_x, 34, 18, 16))
            pygame.draw.rect(screen, (240, 240, 220), (icon_x + 14, 39, 10, 7), border_radius=2)
            pygame.draw.ellipse(screen, (240, 240, 220), (icon_x + 22, 37, 5, 5))
            pygame.draw.ellipse(screen, (240, 240, 220), (icon_x + 22, 43, 5, 5))

        elif icon_type == "happiness":
            # Heart icon
            pygame.draw.circle(screen, (230, 80, 180), (icon_x + 6, 38), 6)
            pygame.draw.circle(screen, (230, 80, 180), (icon_x + 16, 38), 6)
            pygame.draw.polygon(screen, (230, 80, 180), [(icon_x, 40), (icon_x + 22, 40), (icon_x + 11, 52)])

        elif icon_type == "grades":
            # Detailed Open Book Icon
            # Left & Right page covers (Cyan)
            pygame.draw.polygon(screen, (80, 180, 250), [(icon_x, 37), (icon_x + 10, 34), (icon_x + 10, 52), (icon_x, 50)])
            pygame.draw.polygon(screen, (80, 180, 250), [(icon_x + 12, 34), (icon_x + 22, 37), (icon_x + 22, 50), (icon_x + 12, 52)])
            # White inner pages
            pygame.draw.polygon(screen, (245, 245, 250), [(icon_x + 2, 38), (icon_x + 9, 36), (icon_x + 9, 50), (icon_x + 2, 49)])
            pygame.draw.polygon(screen, (245, 245, 250), [(icon_x + 13, 36), (icon_x + 20, 38), (icon_x + 20, 49), (icon_x + 13, 50)])
            # Center spine line
            pygame.draw.line(screen, (40, 50, 70), (icon_x + 11, 34), (icon_x + 11, 52), width=2)
            # Text lines on open book pages
            pygame.draw.line(screen, (100, 110, 140), (icon_x + 4, 40), (icon_x + 8, 40), width=1)
            pygame.draw.line(screen, (100, 110, 140), (icon_x + 4, 44), (icon_x + 8, 44), width=1)
            pygame.draw.line(screen, (100, 110, 140), (icon_x + 14, 40), (icon_x + 18, 40), width=1)
            pygame.draw.line(screen, (100, 110, 140), (icon_x + 14, 44), (icon_x + 18, 44), width=1)

        # 2. Determine Bar Fill Color (Turns RED if critical < 30%)
        is_critical = display_val < 30
        fill_color = (235, 55, 55) if is_critical else normal_color

        # 3. Progress Bar Outer Background
        bar_bg_rect = pygame.Rect(start_x, bar_top_y, bar_width, bar_height)
        pygame.draw.rect(screen, (15, 18, 24), bar_bg_rect, border_radius=8)

        # 4. Progress Bar Inner Fill
        fill_width = min(bar_width, int((display_val / max_val) * bar_width))
        if fill_width > 0:
            fill_rect = pygame.Rect(start_x, bar_top_y, fill_width, bar_height)
            pygame.draw.rect(screen, fill_color, fill_rect, border_radius=8)

        # 5. Bar Border (Red border glow if critical)
        border_color = (255, 90, 90) if is_critical else (90, 100, 120)
        pygame.draw.rect(screen, border_color, bar_bg_rect, width=2 if is_critical else 1, border_radius=8)

        # 6. Percentage Text Centered INSIDE the Status Bar
        text_str = f"{display_val}%"
        val_surface = font.render(text_str, True, (255, 255, 255))
        val_rect = val_surface.get_rect(center=bar_bg_rect.center)
        
        # Text drop shadow for maximum legibility over colored fill
        shadow_surface = font.render(text_str, True, (10, 10, 10))
        shadow_rect = shadow_surface.get_rect(center=(bar_bg_rect.centerx + 1, bar_bg_rect.centery + 1))
        
        screen.blit(shadow_surface, shadow_rect)
        screen.blit(val_surface, val_rect)

def get_action_button_rects():
    """
    Returns a dict mapping action names ('feed', 'play', 'study') to their Pygame Rects.
    Stacked vertically along the right hand side of the screen.
    """
    return {
        "feed": pygame.Rect(734, 120, 42, 42),
        "play": pygame.Rect(734, 194, 42, 42),
        "study": pygame.Rect(734, 268, 42, 42),
    }

def draw_action_buttons(screen, mouse_pos):
    """
    Draws a vertical panel on the right hand side of the screen containing small
    clickable action buttons with icons only (no words). Includes hover highlights.
    """
    # Outer vertical panel container on right side of screen
    panel_rect = pygame.Rect(726, 105, 58, 220)
    pygame.draw.rect(screen, (18, 22, 30), panel_rect, border_radius=12)
    pygame.draw.rect(screen, (55, 65, 85), panel_rect, width=1, border_radius=12)

    button_rects = get_action_button_rects()
    
    button_configs = {
        "feed": ((255, 140, 0), "feed"),
        "play": ((230, 80, 180), "play"),
        "study": ((80, 180, 250), "study"),
    }
    
    for action, (accent_color, icon_type) in button_configs.items():
        rect = button_rects[action]
        is_hovered = rect.collidepoint(mouse_pos)
        
        # Background fill (brighter on hover)
        bg_color = (65, 75, 95) if is_hovered else (28, 34, 46)
        pygame.draw.rect(screen, bg_color, rect, border_radius=8)
        
        # Border glow
        border_color = (255, 255, 255) if is_hovered else accent_color
        pygame.draw.rect(screen, border_color, rect, width=2 if is_hovered else 1, border_radius=8)
        
        # Icon Centered inside the 42x42 button
        cx, cy = rect.centerx, rect.centery
        
        if icon_type == "feed":
            # Meat drumstick icon inside 42x42 button
            pygame.draw.ellipse(screen, (255, 140, 0), (cx - 10, cy - 9, 17, 15))
            pygame.draw.rect(screen, (240, 240, 220), (cx + 3, cy - 3, 9, 7), border_radius=2)
            pygame.draw.ellipse(screen, (240, 240, 220), (cx + 9, cy - 6, 6, 6))
            pygame.draw.ellipse(screen, (240, 240, 220), (cx + 9, cy, 6, 6))
            
        elif icon_type == "play":
            # Heart icon inside 42x42 button
            pygame.draw.circle(screen, (230, 80, 180), (cx - 6, cy - 4), 6)
            pygame.draw.circle(screen, (230, 80, 180), (cx + 6, cy - 4), 6)
            pygame.draw.polygon(screen, (230, 80, 180), [(cx - 12, cy - 3), (cx + 12, cy - 3), (cx, cy + 9)])
            
        elif icon_type == "study":
            # Open Book icon inside 42x42 button
            pygame.draw.polygon(screen, (80, 180, 250), [(cx - 11, cy - 7), (cx - 2, cy - 10), (cx - 2, cy + 7), (cx - 11, cy + 4)])
            pygame.draw.polygon(screen, (80, 180, 250), [(cx + 2, cy - 10), (cx + 11, cy - 7), (cx + 11, cy + 4), (cx + 2, cy + 7)])
            pygame.draw.line(screen, (245, 245, 250), (cx - 8, cy - 4), (cx - 4, cy - 5), width=2)
            pygame.draw.line(screen, (245, 245, 250), (cx - 8, cy + 1), (cx - 4, cy), width=2)
            pygame.draw.line(screen, (245, 245, 250), (cx + 4, cy - 5), (cx + 8, cy - 4), width=2)
            pygame.draw.line(screen, (245, 245, 250), (cx + 4, cy), (cx + 8, cy + 1), width=2)

def draw_bottom_dialogue_box(screen, font, pearl):
    """
    Draws a black rectangle at the bottom of the screen to display in-game text messages.
    """
    # Black dialogue box anchored at the bottom (760px wide for 800px screen)
    box_rect = pygame.Rect(20, 365, 760, 95)
    
    # Fill dark black container with border
    pygame.draw.rect(screen, (12, 12, 16), box_rect, border_radius=12)
    pygame.draw.rect(screen, (255, 215, 0), box_rect, width=2, border_radius=12)  # Gold border

    # Render Current Message Text centered in box
    msg_surface = font.render(pearl.current_message, True, (240, 240, 240))
    msg_rect = msg_surface.get_rect(center=(400, 412))
    screen.blit(msg_surface, msg_rect)

def main():
    pygame.init()

    # Viewport matching 800 x 480 pixels display
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 480
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Pearl the Jaguar - Virtual Pet")

    clock = pygame.time.Clock()

    # System Fonts
    main_font = pygame.font.SysFont("Helvetica", 18)
    small_font = pygame.font.SysFont("Helvetica", 15)
    title_font = pygame.font.SysFont("Helvetica", 22, bold=True)

    # Initialize Pearl and Image Asset Dictionary
    pearl = Pearl(name="Pearl")
    image_assets = load_image_assets()

    running = True

    while running:
        dt = clock.tick(30) / 1000.0  # 30 FPS tick
        mouse_pos = pygame.mouse.get_pos()

        # Process PyGame Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    btn_rects = get_action_button_rects()
                    if btn_rects["feed"].collidepoint(event.pos):
                        pearl.feed()
                    elif btn_rects["play"].collidepoint(event.pos):
                        pearl.play()
                    elif btn_rects["study"].collidepoint(event.pos):
                        pearl.study()
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_1, pygame.K_KP1):
                    pearl.feed()
                elif event.key in (pygame.K_2, pygame.K_KP2):
                    pearl.play()
                elif event.key in (pygame.K_3, pygame.K_KP3):
                    pearl.study()
                elif event.key in (pygame.K_s, pygame.K_f):
                    pearl.cycle_time_speed()
                elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False

        # Advance Pearl state machine
        pearl.update(dt)

        # Clear background (Warm Cozy Room Background)
        screen.fill((45, 50, 62))

        # 1. Draw Top Horizontal Status Bars & Action Buttons
        draw_status_bars(screen, main_font, pearl)
        draw_action_buttons(screen, mouse_pos)

        # 2. Draw Center Canvas & Current Pearl Rectangular Image Frame
        current_frames = get_current_pearl_frames(pearl, image_assets)
        current_sprite = current_frames[pearl.anim_frame % len(current_frames)]
        
        # Center rectangular card position (Y center = 215)
        sprite_rect = current_sprite.get_rect(center=(SCREEN_WIDTH // 2, 215))

        # Background card frame & border (Red alert if distressed, sleek dark slate container otherwise)
        card_bg_color = (80, 25, 25) if pearl.state == PearlState.DISTRESSED else (25, 28, 36)
        card_border_color = (220, 60, 60) if pearl.state == PearlState.DISTRESSED else (90, 100, 120)

        bg_card_rect = sprite_rect.inflate(8, 8)
        pygame.draw.rect(screen, card_bg_color, bg_card_rect, border_radius=14)
        screen.blit(current_sprite, sprite_rect)
        pygame.draw.rect(screen, card_border_color, bg_card_rect, width=2, border_radius=14)

        # 3. Draw Bottom Black Dialogue Box (In-game text only)
        draw_bottom_dialogue_box(screen, main_font, pearl)

        # Render screen updates
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    main()

