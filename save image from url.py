import requests
from pathlib import Path
import os

def save_image_from_url(image_url, filename=None, save_folder="Shared Python Pinterest images"):
    """
    Downloads an image from a URL and saves it to a local folder.
    
    Args:
        image_url (str): The URL of the image to download
        filename (str): Optional custom filename. If None, extracts from URL
        save_folder (str): Local folder path to save the image (default: "images")
    
    Returns:
        str: Path to the saved image file, or None if failed
    """
    try:
        # Create folder if it doesn't exist
        Path(save_folder).mkdir(parents=True, exist_ok=True)
        
        # Get the image
        response = requests.get(image_url, stream=True)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        
        # Determine filename
        if filename is None:
            filename = os.path.basename(image_url.split('?')[0])  # Remove query params
            if not filename or '.' not in filename:
                filename = "downloaded_image.jpg"  # Fallback name
        
        # Full path for saving
        file_path = Path(save_folder) / filename
        
        # Save the image
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Image saved successfully: {file_path}")
        return str(file_path)
        
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image: {e}")
        return None
    except Exception as e:
        print(f"Error saving image: {e}")
        return None

# Example usage:
# save_image_from_url("https://example.com/image.jpg")
# save_image_from_url("https://example.com/image.jpg", "custom_name.jpg", "my_images")
save_image_from_url("https://gardentabs.com/wp-content/uploads/2025/07/Depositphotos_18699831_L.jpg", "1.jpg")