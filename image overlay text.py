"""
Pinterest Image Text Overlay Batch Processor
Processes images with text overlays and uploads to Google Drive
"""

import os
import sys
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.service_account import Credentials
import time

class ImageProcessor:
    def __init__(self, credentials_file, folder_id=None):
        """
        Initialize with Google Drive credentials
        
        Args:
            credentials_file: Path to your Google service account JSON file
            folder_id: Google Drive folder ID (optional, uploads to root if None)
        """
        self.credentials = Credentials.from_service_account_file(
            credentials_file,
            scopes=['https://www.googleapis.com/auth/drive']
        )
        self.drive_service = build('drive', 'v3', credentials=self.credentials)
        self.folder_id = folder_id
        
    def add_text_to_image(self, image_url, text, output_filename):
        """
        Download image, add text overlay, return processed image bytes
        
        Args:
            image_url: URL of the source image
            text: Text to overlay
            output_filename: Name for the output file
            
        Returns:
            BytesIO object with processed image
        """
        try:
            # Download the image
            print(f"Downloading: {image_url}")
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Open image
            img = Image.open(BytesIO(response.content))
            
            # Convert to RGB if necessary (handles PNG transparency)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Create drawing context
            draw = ImageDraw.Draw(img)
            
            # Calculate font size based on image width (responsive sizing)
            font_size = max(24, int(img.width * 0.04))
            
            # Try to load a nice font, fall back to default if not available
            try:
                # Windows
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                try:
                    # Mac
                    font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
                except:
                    try:
                        # Linux
                        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
                    except:
                        # Fallback to default
                        font = ImageFont.load_default()
            
            # Get text dimensions
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Calculate position (center bottom with padding)
            x = (img.width - text_width) // 2
            y = img.height - text_height - 30  # 30px padding from bottom
            
            # Add text with black outline for better readability
            outline_width = 2
            for adj_x in range(-outline_width, outline_width + 1):
                for adj_y in range(-outline_width, outline_width + 1):
                    if adj_x != 0 or adj_y != 0:
                        draw.text((x + adj_x, y + adj_y), text, font=font, fill='black')
            
            # Add main white text
            draw.text((x, y), text, font=font, fill='white')
            
            # Save to BytesIO
            output = BytesIO()
            img.save(output, format='PNG', quality=95)
            output.seek(0)
            
            return output
            
        except Exception as e:
            print(f"Error processing {image_url}: {str(e)}")
            return None
    
    def upload_to_drive(self, image_bytes, filename):
        """
        Upload processed image to Google Drive
        
        Args:
            image_bytes: BytesIO object with image data
            filename: Name for the file in Drive
            
        Returns:
            File ID if successful, None if failed
        """
        try:
            file_metadata = {
                'name': filename,
                'parents': [self.folder_id] if self.folder_id else []
            }
            
            media = MediaIoBaseUpload(
                image_bytes,
                mimetype='image/png',
                resumable=True
            )
            
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            print(f"✓ Uploaded: {filename} (ID: {file.get('id')})")
            return file.get('id')
            
        except Exception as e:
            print(f"✗ Upload failed for {filename}: {str(e)}")
            return None
    
    def process_batch(self, image_objects, delay=1):
        """
        Process a batch of images
        
        Args:
            image_objects: List of dicts with 'url' and 'text' keys
                          Example: [{'url': 'https://...', 'text': 'Pinterest text'}, ...]
            delay: Seconds to wait between processing (to be nice to servers)
        """
        total = len(image_objects)
        successful = 0
        failed = 0
        results = []
        
        print(f"Starting batch processing of {total} images...")
        
        for i, item in enumerate(image_objects, 1):
            # Auto-generate filename from URL or index
            filename = self._generate_filename(item.get('url', ''), i)
            
            print(f"\nProcessing {i}/{total}: {filename}")
            
            # Process image
            processed_image = self.add_text_to_image(
                item['url'], 
                item['text'], 
                filename
            )
            
            if processed_image:
                # Upload to Drive
                file_id = self.upload_to_drive(processed_image, filename)
                if file_id:
                    successful += 1
                    results.append({
                        'original_url': item['url'],
                        'text': item['text'],
                        'filename': filename,
                        'drive_file_id': file_id,
                        'status': 'success'
                    })
                else:
                    failed += 1
                    results.append({
                        'original_url': item['url'],
                        'text': item['text'],
                        'filename': filename,
                        'drive_file_id': None,
                        'status': 'upload_failed'
                    })
            else:
                failed += 1
                results.append({
                    'original_url': item['url'],
                    'text': item['text'],
                    'filename': filename,
                    'drive_file_id': None,
                    'status': 'processing_failed'
                })
            
            # Brief delay to be respectful
            if i < total:
                time.sleep(delay)
        
        print(f"\n=== BATCH COMPLETE ===")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Total: {total}")
        
        return results
    
    def _generate_filename(self, url, index):
        """Generate a filename from URL or use index"""
        try:
            # Extract filename from URL
            import urllib.parse
            parsed = urllib.parse.urlparse(url)
            original_name = os.path.basename(parsed.path)
            name_without_ext = os.path.splitext(original_name)[0]
            
            if name_without_ext:
                return f"pinterest_{name_without_ext}_{index}.png"
            else:
                return f"pinterest_pin_{index:03d}.png"
        except:
            return f"pinterest_pin_{index:03d}.png"

def load_from_csv(csv_file):
    """
    Load image data from CSV file
    
    CSV should have columns: url, text, filename
    """
    try:
        df = pd.read_csv(csv_file)
        required_columns = ['url', 'text', 'filename']
        
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"CSV must have columns: {required_columns}")
        
        return df.to_dict('records')
    except Exception as e:
        print(f"Error loading CSV: {str(e)}")
        return []

def main():
    """
    Main function - modify these settings for your use case
    """
    
    # CONFIGURATION - UPDATE THESE PATHS
    CREDENTIALS_FILE = "path/to/your/google-credentials.json"  # Download from Google Cloud Console
    DRIVE_FOLDER_ID = "your-google-drive-folder-id"  # Optional: specific folder ID
    
    # Validate credentials file exists
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"Error: Credentials file not found: {CREDENTIALS_FILE}")
        print("Download your Google service account JSON from Google Cloud Console")
        return
    
    # EXAMPLE: Your image objects
    image_objects = [
        {
            'url': 'https://yourwebsite.com/image1.jpg',
            'text': 'Amazing Pinterest Pin Text'
        },
        {
            'url': 'https://yourwebsite.com/image2.png', 
            'text': 'Another Great Pin for Pinterest'
        },
        {
            'url': 'https://yourwebsite.com/blog/photo.jpg',
            'text': 'Blog Post Title - Perfect for Pinterest!'
        }
    ]
    
    # Initialize processor
    processor = ImageProcessor(CREDENTIALS_FILE, DRIVE_FOLDER_ID)
    
    # Process the batch
    results = processor.process_batch(image_objects)
    
    # Print results summary
    print("\n=== DETAILED RESULTS ===")
    for result in results:
        status_icon = "✓" if result['status'] == 'success' else "✗"
        print(f"{status_icon} {result['filename']}: {result['status']}")
        if result['drive_file_id']:
            print(f"   Drive ID: {result['drive_file_id']}")
    
    return results

# Alternative: Load from your existing data source
def process_from_your_script(image_objects, credentials_file, folder_id=None):
    """
    Function you can call directly from your existing script
    
    Args:
        image_objects: List of {'url': str, 'text': str} objects
        credentials_file: Path to Google credentials JSON
        folder_id: Optional Google Drive folder ID
        
    Returns:
        List of results with Drive file IDs
    """
    processor = ImageProcessor(credentials_file, folder_id)
    return processor.process_batch(image_objects)

# Example of how to create the CSV programmatically
def create_sample_csv():
    """
    Create a sample CSV file for testing
    """
    sample_data = [
        {
            'url': 'https://example.com/image1.jpg',
            'text': 'Amazing Pinterest Pin #1',
            'filename': 'pinterest_pin_001.png'
        },
        {
            'url': 'https://example.com/image2.jpg', 
            'text': 'Great Content for Pinterest',
            'filename': 'pinterest_pin_002.png'
        }
    ]
    
    df = pd.DataFrame(sample_data)
    df.to_csv('images_to_process.csv', index=False)
    print("Sample CSV created: images_to_process.csv")

if __name__ == "__main__":
    # Uncomment to create sample CSV:
    # create_sample_csv()
    
    main()