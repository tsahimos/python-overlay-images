from PIL import Image, ImageDraw, ImageFont
import os

def add_text_overlay(image_path, output_path, text, font_name, position=(50, 50), 
                    font_size=40, font_color=(255, 255, 255)):
    """
    Add text overlay to an image and save it.
    
    Args:
        image_path: Path to input image
        output_path: Path to save the output image
        text: Text to overlay
        position: (x, y) coordinates for text placement
        font_size: Size of the font
        font_color: RGB color tuple for text
    """
    try:
        # Load the image
        image = Image.open(image_path)
        
        # Create a drawing context
        draw = ImageDraw.Draw(image)

        # Calculate font size based on image width (larger sizing)
        font_size = max(40, int(image.width * 0.08))  # Increased from 0.04 to 0.08
        
        # Try to use a system font, fall back to default if not available
        try:
            font = ImageFont.truetype(font_name, font_size)
        except OSError:
            font = ImageFont.load_default()
        
        # Get text dimensions
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Calculate position (center bottom with more padding)
        x = (image.width - text_width) // 2
        y = image.height - text_height - 60  # Increased padding from 30px to 60px

        # Add text with thicker black outline for better readability
        outline_width = 3  # Increased from 2 to 3 for larger text
        for adj_x in range(-outline_width, outline_width + 1):
            for adj_y in range(-outline_width, outline_width + 1):
                if adj_x != 0 or adj_y != 0:
                    draw.text((x + adj_x, y + adj_y), text, font=font, fill='black')

        # Add text to image
        # draw.text(position, text, font=font, fill=font_color)
        # Add main white text
        draw.text((x, y), text, font=font, fill='white')
        
        # Save the image
        image.save(output_path)
        print(f"Image saved successfully to: {output_path}")
        
    except Exception as e:
        print(f"Error: {e}")

# Example usage
if __name__ == "__main__":
    input_image = "Depositphotos_552504928_L.jpg"  # Change to your image path
    font_options = [
        ("arial.ttf", "Arial"),
        ("arialbd.ttf", "Arial Bold"),
        ("calibri.ttf", "Calibri"),
        ("calibrib.ttf", "Calibri Bold"),
        ("georgia.ttf", "Georgia"),
        ("georgiab.ttf", "Georgia Bold"),
        ("impact.ttf", "Impact"),
        ("times.ttf", "Times New Roman"),
        ("timesbd.ttf", "Times New Roman Bold"),
        ("trebuc.ttf", "Trebuchet MS"),
        ("trebucbd.ttf", "Trebuchet MS Bold"),
        ("verdana.ttf", "Verdana"),
        ("verdanab.ttf", "Verdana Bold"),
        ("comic.ttf", "Comic Sans MS"),
        ("comicbd.ttf", "Comic Sans MS Bold")
    ]
    font = font_options[14]
    output_image = f"output_img_font_{font[0]}.jpg"
    overlay_text = "Your Text Here"

    
    add_text_overlay(input_image, output_image, overlay_text, font_options[14][0])