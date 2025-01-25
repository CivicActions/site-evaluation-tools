import argparse
import csv
import logging
import requests
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
import re

# Define problematic suggestions that require alt text generation
PROBLEMATIC_SUGGESTIONS = [
    "WCAG 1.1.1 Failure: Alt text is empty or invalid.",
    "No alt text was provided. Clear WCAG failure.",
    "Avoid phrases like 'image of', 'graphic of', or 'todo' in alt text.",
    "Alt text appears to be meaningless. Replace it with descriptive content.",
    "Alt text seems too short. Consider providing more context.",
    "Consider simplifying the text.",
]

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize the BLIP model and processor
logging.info("Initializing the BLIP model...")
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

# Define a function to load the CSV file
def load_csv(file_path):
    try:
        logging.info(f"Loading CSV file from: {file_path}")
        with open(file_path, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            data = list(reader)
        logging.info("CSV file loaded successfully.")
        return data
    except Exception as e:
        logging.error(f"Failed to load CSV file: {e}")
        raise

# Add image preview
def add_image_preview(data):
    for row in data:
        image_url = row.get("Image_url", "")
        row["Image Preview"] = f'=IMAGE("{image_url}")' if image_url else "No Image URL"

# Define a function to save the CSV file
def save_csv(file_path, data, fieldnames):
    try:
        logging.info(f"Saving updated CSV file to: {file_path}")
        with open(file_path, mode="w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        logging.info("CSV file saved successfully.")
    except Exception as e:
        logging.error(f"Failed to save CSV file: {e}")
        raise

# Post-process generated text
def post_process_alt_text(generated_text):
    unhelpful_phrases = [
        "The image is", "This is an image of", "The alt text is",
        "file with", "a jpg file", "a png file"
    ]
    for phrase in unhelpful_phrases:
        generated_text = generated_text.replace(phrase, "").strip()
    return generated_text.strip(". ")

# Generate alt text using BLIP
def generate_alt_text(image_url):
    try:
        # Skip SVG files
        if image_url.lower().endswith(".svg"):
            logging.info(f"Skipping SVG file: {image_url}")
            return "Skipped: SVG files are not processed"
        
        # Fetch the image from the URL
        logging.debug(f"Fetching image from URL: {image_url}")
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        image = Image.open(response.raw).convert("RGB")

        # Prepare inputs for the BLIP model
        inputs = processor(image, return_tensors="pt")

        # Generate alt text
        outputs = model.generate(**inputs)
        generated_text = processor.decode(outputs[0], skip_special_tokens=True)

        # Post-process the generated alt text
        return post_process_alt_text(generated_text)

    except Exception as e:
        logging.error(f"Error generating alt text for {image_url}: {e}")
        return f"Error generating alt text: {e}"
    

# Main function
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate alt text for images based on a CSV file.")
    parser.add_argument("-c", "--csv", required=True, help="Path to the input CSV file.")
    args = parser.parse_args()

    input_csv = args.csv

    # Load CSV data
    data = load_csv(input_csv)

# Process data and generate alt text
logging.info("Processing rows in the CSV file...")
for idx, row in enumerate(data):
    logging.info(f"Processing row {idx + 1} of {len(data)}...")
    image_url = row.get("Image_url", "")
    if not image_url:
        logging.warning(f"Row {idx + 1} is missing an Image URL. Skipping.")
        row["Generated Alt Text"] = "Error: Missing image URL"
        continue

    # Check if the suggestions indicate alt text needs improvement
    suggestions = row.get("Suggestions", "")
    if any(problematic in suggestions for problematic in PROBLEMATIC_SUGGESTIONS):
        logging.info(f"Generating alt text for row {idx + 1} due to suggestion: {suggestions}")
        row["Generated Alt Text"] = generate_alt_text(image_url)
    else:
        logging.info(f"Alt text for row {idx + 1} seems fine. Skipping generation.")
        row["Generated Alt Text"] = ""

# Save updated CSV
output_csv = input_csv.replace(".csv", "_with_alt_text.csv")
fieldnames = data[0].keys() if data else []
save_csv(output_csv, data, fieldnames)
logging.info(f"Processed CSV saved to: {output_csv}")
