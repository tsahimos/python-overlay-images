import os
import json
import requests
import re
import shutil
import csv
from pathlib import Path
from urllib.parse import urlparse
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_highest_numbered_file(directory):
    """Find the highest numbered file in the directory and return the next number."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")
        return 1
    
    highest_num = 0
    pattern = re.compile(r'^(\d+)\.')
    
    for filename in os.listdir(directory):
        match = pattern.match(filename)
        if match:
            num = int(match.group(1))
            if num > highest_num:
                highest_num = num
    
    next_num = highest_num + 1
    logger.info(f"Highest numbered file found: {highest_num}, starting from: {next_num}")
    return next_num

def get_file_extension_from_url(url):
    """Extract file extension from URL."""
    parsed_url = urlparse(url)
    path = parsed_url.path
    _, ext = os.path.splitext(path)
    return ext.lower() if ext else '.jpg'  # Default to .jpg if no extension found

def download_image(url, destination_path):
    """Download image from URL to destination path."""
    try:
        logger.info(f"Downloading image from: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        with open(destination_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Successfully downloaded: {destination_path}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to download image from {url}: {str(e)}")
        raise

def create_csv_file(data, json_filename, csv_folder):
    """Create CSV file from processed data."""
    try:
        # Create CSV filename from JSON filename
        csv_filename = json_filename.replace('.json', '.csv')
        csv_path = os.path.join(csv_folder, csv_filename)
        
        # Create CSV folder if it doesn't exist
        if not os.path.exists(csv_folder):
            os.makedirs(csv_folder)
            logger.info(f"Created CSV folder: {csv_folder}")
        
        # Write CSV file
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(['Title', 'Media URL', 'Pinterest board', 'Link', 'Publish date'])
            
            # Write data rows
            for image_url, image_data in data.items():
                writer.writerow([
                    image_data.get('pinTitle', ''),
                    image_data.get('location', ''),
                    image_data.get('board', ''),
                    image_data.get('link', ''),
                    image_data.get('date', '')
                ])
        
        logger.info(f"Created CSV file: {csv_path}")
        return csv_path
    
    except Exception as e:
        logger.error(f"Failed to create CSV file: {str(e)}")
        raise
    """Download image from URL to destination path."""
    try:
        logger.info(f"Downloading image from: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        with open(destination_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Successfully downloaded: {destination_path}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to download image from {url}: {str(e)}")
        raise

def process_json_file(json_file_path, images_folder, processed_folder, csv_folder):
    """Process a single JSON file."""
    logger.info(f"Processing JSON file: {json_file_path}")
    
    # Read and parse JSON file
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Successfully loaded JSON with {len(data)} entries")
    except Exception as e:
        logger.error(f"Failed to read or parse JSON file {json_file_path}: {str(e)}")
        raise
    
    # Get starting number for images
    current_num = get_highest_numbered_file(images_folder)
    
    # Process each image
    for image_url, image_data in data.items():
        try:
            # Get file extension from URL
            extension = get_file_extension_from_url(image_url)
            
            # Create new filename
            new_filename = f"{current_num}{extension}"
            destination_path = os.path.join(images_folder, new_filename)
            
            # Download image
            download_image(image_url, destination_path)
            
            # Add location to image data
            image_data['location'] = destination_path
            
            logger.info(f"Processed image {current_num}: {image_url} -> {new_filename}")
            current_num += 1
            
        except Exception as e:
            logger.error(f"Failed to process image {image_url}: {str(e)}")
            raise
    
    # Save updated JSON file
    try:
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Updated JSON file with location data")
    except Exception as e:
        logger.error(f"Failed to save updated JSON file: {str(e)}")
        raise
    
    # Create CSV file
    json_filename = os.path.basename(json_file_path)
    create_csv_file(data, json_filename, csv_folder)
    
    # Move JSON file to processed folder
    try:
        if not os.path.exists(processed_folder):
            os.makedirs(processed_folder)
            logger.info(f"Created processed folder: {processed_folder}")
        
        processed_path = os.path.join(processed_folder, os.path.basename(json_file_path))
        shutil.move(json_file_path, processed_path)
        logger.info(f"Moved JSON file to: {processed_path}")
    except Exception as e:
        logger.error(f"Failed to move JSON file to processed folder: {str(e)}")
        raise

def main():
    # Define paths
    json_folder = r"C:\Users\tsahi\My Drive (tsahi@mossdigitalpublishing.com)\Script\Pinterest bulk upload pins\json files"
    images_folder = r"C:\Users\tsahi\My Drive (tsahi@mossdigitalpublishing.com)\Script\Python overlay images\Shared Python Pinterest images"
    processed_folder = r"C:\Users\tsahi\My Drive (tsahi@mossdigitalpublishing.com)\Script\Pinterest bulk upload pins\json files\Processed JSON files"
    csv_folder = r"C:\Users\tsahi\My Drive (tsahi@mossdigitalpublishing.com)\Script\Pinterest bulk upload pins\csv files"
    
    # Pattern for JSON files: yyyy-mm-dd_siteName.json
    json_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}_\w+\.json$')
    
    logger.info("Starting Pinterest image processing script")
    logger.info(f"JSON folder: {json_folder}")
    logger.info(f"Images folder: {images_folder}")
    logger.info(f"Processed folder: {processed_folder}")
    logger.info(f"CSV folder: {csv_folder}")
    
    # Check if source folder exists
    if not os.path.exists(json_folder):
        logger.error(f"Source folder does not exist: {json_folder}")
        return
    
    # Find matching JSON files
    json_files = []
    for filename in os.listdir(json_folder):
        if json_pattern.match(filename):
            json_files.append(os.path.join(json_folder, filename))
    
    if not json_files:
        logger.info("No matching JSON files found")
        return
    
    logger.info(f"Found {len(json_files)} JSON files to process")
    
    # Process each JSON file
    for json_file in json_files:
        try:
            logger.info(f"\n{'='*50}")
            process_json_file(json_file, images_folder, processed_folder, csv_folder)
            logger.info(f"Successfully processed: {os.path.basename(json_file)}")
        except Exception as e:
            logger.error(f"Aborting due to error processing {json_file}: {str(e)}")
            break
    
    logger.info("Script completed")

if __name__ == "__main__":
    main()