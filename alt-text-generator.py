import os  # Add this import at the top of the script

# Disable parallelism for Hugging Face tokenizers to avoid fork-related warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import argparse
import csv
import logging
import requests
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
import re
import pytesseract
from io import BytesIO
from tqdm import tqdm  # Import tqdm for progress bar
from datetime import datetime  # Import datetime at the top of the script
import sys
import anthropic

# Add Anthropic and Ollama API base URLs and keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OLLAMA_API_URL = "http://localhost:11434/api/generate"  # Assuming Ollama runs locally
DEFAULT_MODEL = "blip"

def validate_anthropic_key(selected_model):
    """Ensure the Anthropic API key is set only if the 'anthropic' model is selected."""
    if selected_model == "anthropic" and not ANTHROPIC_API_KEY:
        raise ValueError("Anthropic API Key is not set. Please set the ANTHROPIC_API_KEY environment variable.")


# Define problematic suggestions that require alt text generation
PROBLEMATIC_SUGGESTIONS = [
    "WCAG 1.1.1 Failure: Alt text is empty or invalid.",
    "No alt text was provided. Clear WCAG failure.",
    "Avoid phrases like 'image of', 'graphic of', or 'todo' in alt text.",
    "Alt text appears to be meaningless. Replace it with descriptive content.",
    "Alt text seems too short. Consider providing more context.",
    "Consider simplifying the text.",
    "Alt text is too short. Provide more context."
]

# Set up logging for debugging
# logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

def generate_with_anthropic(prompt):
    """Generate text using Anthropic's Claude API."""
    try:
        # Initialize the Anthropic client
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        if not client.api_key:
            raise ValueError("Anthropic API Key is not set. Please set the ANTHROPIC_API_KEY environment variable.")
        
        # Format the message with very specific instructions
        # formatted_prompt = f"\n\nHuman: {prompt}\n\nAssistant:"
        formatted_prompt = (
            "\n\nHuman: Generate alt text for an image. Respond ONLY with the text that should go inside "
            "the alt attribute of an img tag. Do not include 'Alt text:', explanations, quotes, or any other text. "
            f"Image details: {prompt}"
            "\n\nAssistant: I'll provide just the alt text with no additional text:\n"
        )
        
        try:
            response = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=300,
                messages=[
                    {
                        "role": "user",
                        "content": formatted_prompt
                    }
                ]
            )
            
            # Extract and clean the response text
            generated_text = response.content[0].text.strip()
            
            # Remove common prefixes and suffixes
            prefixes_to_remove = [
                "Alt text:", 
                "Here is a concise and descriptive alt text for the image:",
                "Here is a concise and descriptive alt text for the provided image:",
                "I'll provide just the alt text with no additional text:",
            ]
            
            for prefix in prefixes_to_remove:
                if generated_text.startswith(prefix):
                    generated_text = generated_text[len(prefix):].strip()
            
            # Remove any quotes
            generated_text = generated_text.strip('"\'')
            
            # Remove any explanatory text after the main description
            if "\n" in generated_text:
                generated_text = generated_text.split("\n")[0].strip()
            
            return generated_text

        except anthropic.APIError as api_error:
            logging.error(f"Anthropic API Error: {str(api_error)}")
            return f"Error with Anthropic API: {str(api_error)}"
            
        except anthropic.APIConnectionError as conn_error:
            logging.error(f"Connection Error: {str(conn_error)}")
            return "Error connecting to Anthropic API"

    except Exception as e:
        logging.error(f"Error using Anthropic API: {e}")
        return f"Error generating text with Anthropic API: {str(e)}"


def generate_with_ollama(prompt, model_name="llama3.1:latest"):
    """Generate text using a hosted Ollama model with improved response handling."""
    try:
        # Create a more specific prompt that explicitly requests just the alt text
        formatted_prompt = (
            "Generate alt text for an image. Respond ONLY with the text that should go inside "
            "the alt attribute of an img tag. Do not include 'Alt text:', explanations, quotes, "
            "or any other text. Keep the description concise and factual.\n\n"
            f"Image details: {prompt}"
        )
        
        payload = {
            "model": model_name,
            "prompt": formatted_prompt,
            "stream": False,
            "system": "You are a helpful assistant that generates alt text for images. Respond only with the alt text itself, without any explanations, disclaimers, or meta-commentary."
        }
        
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=30)
        response.raise_for_status()
        
        try:
            response_data = response.json()
            generated_text = ""
            
            if "response" in response_data:
                generated_text = response_data["response"].strip()
            elif "text" in response_data:
                generated_text = response_data["text"].strip()
            else:
                return "Error: Unexpected response structure from Ollama"
            
            # Clean up the response
            # Remove common prefixes
            prefixes_to_remove = [
                "Alt text:",
                "Here is",
                "The alt text is",
                "I suggest",
                "Based on the image,",
                "A concise alt text would be",
                "Here's a descriptive alt text:",
                "The appropriate alt text is",
            ]
            
            for prefix in prefixes_to_remove:
                if generated_text.lower().startswith(prefix.lower()):
                    generated_text = generated_text[len(prefix):].strip()
            
            # Remove quotes and leading/trailing punctuation
            generated_text = generated_text.strip('"\'".,: ')
            
            # Remove any explanatory text after the main description
            if "\n" in generated_text:
                generated_text = generated_text.split("\n")[0].strip()
            
            # Ensure proper sentence format
            generated_text = generated_text.strip(".")
            if generated_text:
                generated_text = generated_text[0].upper() + generated_text[1:] + "."
            
            return generated_text
            
        except ValueError as val_err:
            logging.error(f"JSON decode error with Ollama API: {val_err}")
            return "Error: Malformed JSON from Ollama API"
            
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"Ollama API HTTP error: {http_err}")
        return f"Error using Ollama API: {http_err}"
    except Exception as e:
        logging.error(f"Error using Ollama API: {e}")
        return f"Error generating text with Ollama API: {str(e)}"


def check_image_exists(image_url):
    """
    Check if the image URL exists by making a HEAD request to minimize bandwidth usage.
    Returns True if the image exists, False otherwise.
    """
    try:
        response = requests.head(image_url, timeout=10)
        if response.status_code == 200:
            return True
        else:
            logging.warning(f"Image not found or inaccessible: {image_url} (Status: {response.status_code})")
            return False
    except Exception as e:
        logging.error(f"Error checking image existence for {image_url}: {e}")
        return False

def extract_text_with_ocr(image_url):
    try:
        # Fetch the image
        response = requests.get(image_url, stream=True)
        response.raise_for_status()

        # Validate content type to ensure it's an image
        content_type = response.headers.get("Content-Type", "")
        if not content_type.startswith("image/"):
            logging.error(f"URL does not point to a valid image: {image_url} (Content-Type: {content_type})")
            return "Invalid image URL or unsupported type"

        # Load the image using Pillow
        image = Image.open(BytesIO(response.content))

        # Validate image format
        if image.format not in ["JPEG", "PNG", "BMP", "TIFF"]:
            logging.error(f"Unsupported image format: {image.format} for URL: {image_url}")
            return f"Unsupported image format: {image.format}"

        # Use Tesseract to extract text
        ocr_text = pytesseract.image_to_string(image)

        # Count the number of words or lines to determine if the image is text-heavy
        word_count = len(ocr_text.split())
        if word_count > 20:  # Arbitrary threshold for text-heavy images
            logging.info(f"Text-heavy image detected: {image_url}")
            return ocr_text.strip()
        else:
            return ""

    except requests.exceptions.RequestException as e:
        logging.error(f"Network error while fetching image: {e}")
        return "Network error while fetching image"
    except OSError as e:
        logging.error(f"Error loading image with Pillow: {e}")
        return "Error loading image"
    except Exception as e:
        logging.error(f"Unexpected error processing image with OCR: {e}")
        return "Unexpected error processing image"

# Initialize the BLIP model and processor
logging.info("Initializing the BLIP model...")
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

# Define a function to load the CSV file
def load_csv(file_path):
    try:
        # Increase the CSV field size limit
        csv.field_size_limit(sys.maxsize)
        
        logging.info(f"Loading CSV file from: {file_path}")
        with open(file_path, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            data = list(reader)
        logging.info("CSV file loaded successfully.")
        return data
    except Exception as e:
        logging.error(f"Failed to load CSV file: {e}")
        raise

# Define a function to save the CSV file
def save_csv(file_path, data, fieldnames):
    try:
        # Extract the base name and directory from the file path
        base_name, ext = os.path.splitext(file_path)
        
        # Append the current date and time in the format YYYYMMDD_HHMM
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        updated_file_path = f"{base_name}_{timestamp}{ext}"
        
        logging.info(f"Saving updated CSV file to: {updated_file_path}")
        
        # Save the file with the updated name
        with open(updated_file_path, mode="w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        logging.info("CSV file saved successfully.")
        print(f"✅ CSV file has been successfully saved to: {updated_file_path}")  # Add this print statement
    except Exception as e:
        logging.error(f"Failed to save CSV file: {e}")
        raise

def clean_ocr_text(ocr_text):
    # Split into lines and remove duplicates or meaningless text
    lines = ocr_text.split("\n")
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if line and line not in cleaned_lines:
            cleaned_lines.append(line)
    return " ".join(cleaned_lines)

def clean_and_post_process_alt_text(generated_text):
    """
    Cleans and post-processes generated alt text by removing unhelpful phrases, 
    duplicate words, and ensuring proper sentence case.
    """
    # List of unhelpful phrases to remove
    unhelpful_phrases = [
        "The image is", "This is an image of", "The alt text is",
        "file with", "a jpg file", "a png file", "graphic of", "picture of",
        "photo of", "image of"
    ]
    for phrase in unhelpful_phrases:
        generated_text = generated_text.replace(phrase, "").strip()

    # Remove duplicate words or phrases
    words = generated_text.split()
    cleaned_words = []
    for i, word in enumerate(words):
        if i == 0 or word != words[i - 1]:  # Skip consecutive duplicates
            cleaned_words.append(word)
    cleaned_text = " ".join(cleaned_words)

    # Ensure sentence case: Capitalize the first letter and end with a period
    cleaned_text = cleaned_text.strip(". ").capitalize() + "."

    return cleaned_text

# Generate alt text using BLIP with alt_text and title_text integration
def generate_alt_text(image_url, alt_text="", title_text="", model="blip"):
    """Generate alt text using BLIP, Anthropic, or Ollama."""
    try:
        # Skip SVG files
        if image_url.lower().endswith(".svg"):
            logging.info(f"Skipping SVG file: {image_url}")
            return "Skipped: SVG file"

        # Check if the image exists
        if not check_image_exists(image_url):
            logging.info(f"Image not found or inaccessible: {image_url}")
            return "404 Image Not Found"

        # Check if the image is text-heavy using OCR
        ocr_text = extract_text_with_ocr(image_url)
        if ocr_text:
            logging.info(f"OCR used for text-heavy image: {image_url}")
            return clean_ocr_text(ocr_text)

        if model == "blip":
            # Use BLIP
            response = requests.get(image_url, stream=True)
            response.raise_for_status()
            image = Image.open(response.raw).convert("RGB")
            context = f" Provided alt text: {alt_text}. Title text: {title_text}."
            inputs = processor(image, text=context, return_tensors="pt")
            outputs = model.generate(**inputs)
            generated_text = processor.decode(outputs[0], skip_special_tokens=True)
            return clean_and_post_process_alt_text(generated_text)
        elif model == "anthropic":
            # Use Anthropic
            prompt = (
                f"Generate concise and descriptive alt text for the following image URL: {image_url}. "
                # f"Provided alt text: '{alt_text}'. Title text: '{title_text}'. "
                "Focus on accessibility and provide an appropriate description."
            )
            return generate_with_anthropic(prompt)
        elif model == "ollama":
            # Use Ollama
            prompt = (
                f"Generate concise and descriptive alt text for the following image URL: {image_url}. "
                # f"Provided alt text: '{alt_text}'. Title text: '{title_text}'. "
                # "Focus on accessibility and provide an appropriate description."
            )
            return generate_with_ollama(prompt)
        else:
            return f"Unsupported model: {model}"

    except Exception as e:
        logging.error(f"Error generating alt text for {image_url}: {e}")
        return f"Error generating alt text: {e}"
    

# Main function
if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Generate alt text for images based on a CSV file.")
    parser.add_argument("-c", "--csv", required=True, help="Path to the input CSV file.")
    parser.add_argument("-m", "--model", default=DEFAULT_MODEL, choices=["blip", "anthropic", "ollama"], help="Model to use for text generation.")
    args = parser.parse_args()

    # Assign input arguments to variables
    input_csv = args.csv
    selected_model = args.model

    # Validate Anthropic API key only if 'anthropic' model is selected
    validate_anthropic_key(selected_model)

    # Load CSV data
    data = load_csv(input_csv)

    # Process data and generate alt text
    logging.info("Processing rows in the CSV file...")
    for idx, row in enumerate(tqdm(data, desc="Processing images", unit="image")):
        image_url = row.get("Image_url", "")
        if not image_url:
            logging.warning(f"Row {idx + 1} is missing an Image URL. Skipping.")
            row["Generated Alt Text"] = "Error: Missing image URL"
            continue

        # Check if the suggestions indicate alt text needs improvement
        suggestions = row.get("Suggestions", "")
        if any(problematic in suggestions for problematic in PROBLEMATIC_SUGGESTIONS):
            logging.info(f"Generating alt text for row {idx + 1} due to suggestion: {suggestions}")
            row["Generated Alt Text"] = generate_alt_text(image_url, model=selected_model)
        else:
            logging.info(f"Alt text for row {idx + 1} seems fine. Skipping generation.")
            row["Generated Alt Text"] = "Skipped: Alt text sufficient"

    # Save updated CSV
    output_csv = input_csv.replace(".csv", "_with_alt_text.csv")
    fieldnames = data[0].keys() if data else []
    save_csv(output_csv, data, fieldnames)
    logging.info(f"Processed CSV saved to: {output_csv}")
