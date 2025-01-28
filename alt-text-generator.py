import os  # Add this import at the top of the script

# Disable parallelism for Hugging Face tokenizers to avoid fork-related warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import argparse
import csv
import json
import time
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
import base64  # Import for Base64 encoding
from tenacity import retry, stop_after_attempt, wait_fixed


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
# Enable logging with timestamps
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")


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
        
        print(f"INFO: Sending the following prompt to the LLM (Claude):\n{formatted_prompt}\n")

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


@retry(stop=stop_after_attempt(3), wait=wait_fixed(10))  # Retry logic with up to 3 attempts
def send_request_with_retry(payload, timeout=60):
    """
    Send a request to the Ollama API with retry logic.
    """
    response = requests.post(OLLAMA_API_URL, json=payload, timeout=timeout)
    response.raise_for_status()
    return response


def generate_with_ollama(image_path_or_url, prompt, model_name="llama3.2-vision:latest"):
    """Generate text using a hosted Ollama model with enhanced streaming response handling."""
    try:
        logging.info("Starting Ollama text generation...")
        
        # Determine if input is a URL or local file
        if image_path_or_url.startswith("http"):
            logging.debug("Fetching image from URL...")
            response = requests.get(image_path_or_url, stream=True)
            response.raise_for_status()
            image_data = response.content
            logging.info("Image fetched successfully.")
        else:
            logging.debug("Reading image from local file...")
            with open(image_path_or_url, "rb") as image_file:
                image_data = image_file.read()
            logging.info("Image read successfully.")

        # Encode image to Base64
        base64_image = base64.b64encode(image_data).decode("utf-8")
        logging.info("Image successfully encoded to Base64.")

        # Prepare payload
        formatted_prompt = (
            "Generate alt text for an image. Respond ONLY with the text that should go inside "
            "the alt attribute of an img tag. Do not include 'Alt text:', explanations, quotes, "
            "or any other text. Keep the description concise and factual.\n\n"
            f"Image details: {prompt}"
        )
        payload = {
            "model": model_name,
            "prompt": formatted_prompt,
            "images": [base64_image],
        }

        # Send request to Ollama API
        logging.info("Sending request to Ollama API...")
        start_time = time.time()
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=90)
        elapsed_time = time.time() - start_time
        logging.info(f"Response received from Ollama API in {elapsed_time:.2f} seconds.")

        # Parse the response containing multiple JSON objects
        raw_response = response.text
        logging.debug(f"Raw response text from Ollama API: {raw_response}")

        # Split and parse each JSON object
        final_text = ""
        for line in raw_response.splitlines():
            try:
                json_object = json.loads(line)
                if "response" in json_object:
                    final_text += json_object["response"]
                if json_object.get("done", False):
                    break  # Stop if "done" is true
            except json.JSONDecodeError as e:
                logging.error(f"JSON decoding failed for line: {line}. Error: {e}")
                continue

        # Clean and format the final text
        final_text = final_text.strip('"\'").,: ')
        if final_text:
            final_text = final_text[0].upper() + final_text[1:] + "."
        logging.info("Alt text generated successfully.")
        return final_text

    except requests.exceptions.Timeout:
        logging.error("Request to Ollama API timed out.")
        return "Error: Request to Ollama API timed out."
    except requests.exceptions.RequestException as req_err:
        logging.error(f"HTTP Error: {req_err}")
        return f"Error: Failed to connect to Ollama API: {req_err}"
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return f"Error generating alt text: {str(e)}"


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
            print(f"INFO: Sending the following prompt to the LLM (BLIP):\n{context}\n")
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
            # return generate_with_ollama(prompt)
            return generate_with_ollama(image_url, prompt)
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
