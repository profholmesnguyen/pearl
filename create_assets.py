import os
from PIL import Image, ImageDraw

def create_placeholders():
    os.makedirs("assets", exist_ok=True)
    
    # Target sprite size: 240x240
    width, height = 240, 240
    
    # Color palette
    bg_color = (40, 44, 52)          # Dark Slate
    jaguar_body = (255, 180, 50)     # Golden Yellow
    jaguar_spots = (120, 60, 20)     # Dark Brown
    eye_color = (255, 255, 255)
    pupil_color = (20, 20, 20)

    states = {
        "pearl_idle.png": ("Lounging Jaguar", (100, 220, 100)),
        "pearl_feed.png": ("Feeding Jaguar 🍖", (255, 140, 0)),
        "pearl_play.png": ("Playing Jaguar 🎾", (230, 80, 180)),
        "pearl_study.png": ("Studying Jaguar 📚", (80, 180, 250)),
        "pearl_distressed.png": ("Distressed Jaguar", (220, 50, 50)),
    }

    for filename, (label, accent_color) in states.items():
        img = Image.new("RGBA", (width, height), bg_color)
        draw = ImageDraw.Draw(img)

        # Draw Jaguar Body Placeholder (Cute pixel-style rounded jaguar shape)
        draw.ellipse([50, 80, 190, 200], fill=jaguar_body, outline=(200, 130, 30), width=4)
        
        # Jaguar Ears
        draw.polygon([(60, 90), (45, 50), (85, 75)], fill=jaguar_body)
        draw.polygon([(180, 90), (195, 50), (155, 75)], fill=jaguar_body)
        
        # Jaguar Spots
        spots = [(80, 120), (140, 110), (100, 160), (160, 150), (70, 150)]
        for sx, sy in spots:
            draw.ellipse([sx, sy, sx+16, sy+14], fill=jaguar_spots)
            
        # Eyes
        draw.ellipse([85, 105, 105, 125], fill=eye_color)
        draw.ellipse([135, 105, 155, 125], fill=eye_color)
        draw.ellipse([93, 110, 101, 120], fill=pupil_color)
        draw.ellipse([143, 110, 151, 120], fill=pupil_color)
        
        # Nose & Whiskers
        draw.polygon([(115, 130), (125, 130), (120, 138)], fill=(40, 20, 20))
        draw.line([(70, 135), (45, 130)], fill=(200, 200, 200), width=2)
        draw.line([(70, 140), (45, 145)], fill=(200, 200, 200), width=2)
        draw.line([(170, 135), (195, 130)], fill=(200, 200, 200), width=2)
        draw.line([(170, 140), (195, 145)], fill=(200, 200, 200), width=2)

        # State Specific Accessory / Expression
        if "feed" in filename:
            # Drumstick / Meat
            draw.ellipse([150, 150, 195, 185], fill=(180, 60, 40))
            draw.rectangle([180, 160, 210, 175], fill=(240, 240, 220))
        elif "play" in filename:
            # Ball
            draw.ellipse([150, 150, 190, 190], fill=(230, 80, 180), outline=(255, 255, 255), width=3)
        elif "study" in filename:
            # Glasses & Book
            draw.rectangle([80, 103, 110, 127], outline=(50, 50, 50), width=3)
            draw.rectangle([130, 103, 160, 127], outline=(50, 50, 50), width=3)
            draw.line([(110, 115), (130, 115)], fill=(50, 50, 50), width=3)
            # Book at bottom
            draw.rectangle([70, 180, 170, 210], fill=(80, 180, 250))
            draw.line([(120, 180), (120, 210)], fill=(255, 255, 255), width=3)
        elif "distressed" in filename:
            # Tear drops
            draw.ellipse([82, 125, 92, 140], fill=(80, 180, 250))
            draw.ellipse([148, 125, 158, 140], fill=(80, 180, 250))

        # Accent border & Label
        draw.rectangle([0, 0, width-1, height-1], outline=accent_color, width=5)

        img.save(os.path.join("assets", filename))
        print(f"Created asset: assets/{filename}")

if __name__ == "__main__":
    create_placeholders()
