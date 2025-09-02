import os
# Disable parallelism for Hugging Face tokenizers to avoid fork-related warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import sys
import argparse
import logging
import socket
import csv
import json
import time
import requests
from PIL import Image
import re
import pytesseract
from io import BytesIO
from tqdm import tqdm  # Import tqdm for progress bar
from datetime import datetime  # Import datetime at the top of the script
import base64  # Import for Base64 encoding
from tenacity import retry, stop_after_attempt, wait_fixed

# Disable Hugging Face parallelism warnings & suppress excessive logs
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import transformers
transformers.logging.set_verbosity_error()

# ✅ Parse command-line arguments before initializing models
parser = argparse.ArgumentParser(description="Generate alt text for images based on a CSV file.")
parser.add_argument("-c", "--csv", help="Path to the input CSV file.")
parser.add_argument("-m", "--model", default="blip", choices=["blip", "anthropic", "ollama", "azure_openai"],
                    help="Model to use for text generation.")
parser.add_argument("-v", "--verbose", action="store_true", help="Enable detailed logging.")
args = parser.parse_args()

# ✅ Configure logging based on verbosity
logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ✅ Show help and exit early if no CSV is provided
if "-h" in sys.argv or "--help" in sys.argv or not args.csv:
    parser.print_help()
    sys.exit(0)

# ✅ Display startup message
print(f"\n🔵 Running Alt Text Generator\n   - Model: {args.model}\n   - CSV File: {args.csv}\n")

# ✅ Initialize model only when needed
processor = None
model = None
DEFAULT_MODEL = "blip"
client = None

if args.model == "blip":
    print("🔹 Initializing BLIP model...")
    logging.info("Initializing the BLIP model...")
    from transformers import BlipProcessor, BlipForConditionalGeneration
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

elif args.model == "anthropic":
    print("🔹 Using Anthropic Claude API...")
    import anthropic
    # export ANTHROPIC_API_KEY="your_api_key_here"
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

elif args.model == "ollama":
    print("🔹 Using Ollama model...")
    OLLAMA_API_URL = "http://localhost:11434/api/generate"  # Assuming Ollama runs locally

elif args.model == "azure_openai":
    print("🔹 Using Azure OpenAI API...")
    from openai import AzureOpenAI
    from openai import OpenAIError
    # export AZURE_OPENAI_API_KEY="your_api_key_here"
    AZURE_OPENAI_ENDPOINT = "https://civicactions-openai.openai.azure.com/"
    DEPLOYMENT_NAME = "gpt-4o"
    API_VERSION = "2024-05-01-preview"  # ✅ Define API_VERSION before using it
    subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
    if not subscription_key:
        raise ValueError("❌ ERROR: AZURE_OPENAI_API_KEY environment variable is missing.")
    
    try:
        client = AzureOpenAI(
            api_key=subscription_key,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,  # Correct base URL
            api_version=API_VERSION,
        )
        logging.info("✅ Azure OpenAI client initialized successfully.")
    except Exception as e:
        logging.exception(f"❌ Failed to initialize Azure OpenAI client: {e}")
        client = None

print("✅ Model initialization complete.\n")


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

def check_internet(host="8.8.8.8", port=53, timeout=3):
    """
    Checks if the system has an active internet connection.
    Attempts to connect to a well-known public DNS server (Google's 8.8.8.8).
    Returns True if the connection is successful, otherwise False.
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False

def generate_with_blip(image_path_or_url, alt_text="", title_text=""):
    """
    Generate alt text using the BLIP model with a base64-encoded image.
    
    Args:
        image_path_or_url (str): Path to a local image file or URL of the image.
        alt_text (str): Existing alt text, if any, to provide context to the LLM.
        title_text (str): Existing title text, if any, to provide context to the LLM.

    Returns:
        str: Generated alt text.
    """
    try:
        # Load the image
        if image_path_or_url.startswith("http"):
            # Fetch the image from URL
            response = requests.get(image_path_or_url, stream=True)
            response.raise_for_status()
            image = Image.open(response.raw).convert("RGB")
            logging.info(f"Image fetched successfully from URL: {image_path_or_url}")
        else:
            # Load the image from a local file
            image = Image.open(image_path_or_url).convert("RGB")
            logging.info(f"Image loaded successfully from local file: {image_path_or_url}")

        # Encode the image to Base64 for logging/debugging purposes
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")
        logging.debug(f"Base64-encoded image size: {len(base64_image)} characters")

        # Prepare context for BLIP
        # context = f"Provided alt text: {alt_text}. Title text: {title_text}."
        context = ""

        # Generate alt text using BLIP
        inputs = processor(image, text=context, return_tensors="pt")
        outputs = model.generate(**inputs)
        generated_text = processor.decode(outputs[0], skip_special_tokens=True)

        # Post-process the generated text
        cleaned_text = clean_and_post_process_alt_text(generated_text)
        logging.info(f"\n\nBLIP generated alt text successfully:\n\n{cleaned_text}\n\n")
        return cleaned_text

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching image from URL: {e}")
        return "Error fetching image from URL"
    except OSError as e:
        logging.error(f"Error loading image file: {e}")
        return "Error loading image file"
    except Exception as e:
        logging.error(f"Unexpected error in BLIP generation: {e}")
        return "\nError generating alt text with BLIP"


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
        logging.info(f"Starting Ollama text generation - Model: {model_name} ...")
        
        # Determine if input is a URL or local file
        if image_path_or_url.startswith("http"):
            logging.debug(f"Fetching image from URL: {image_path_or_url} ...")
            response = requests.get(image_path_or_url, stream=True)
            response.raise_for_status()
            image_data = response.content
            logging.info("Image fetched successfully.")
        else:
            # logging.debug("Reading image from local file...")
            with open(image_path_or_url, "rb") as image_file:
                image_data = image_file.read()
            # logging.info("Image read successfully.")

        # Encode image to Base64
        base64_image = base64.b64encode(image_data).decode("utf-8")
        # logging.info("Image successfully encoded to Base64.")

        # Prepare payload
        # formatted_prompt = (
        #    "Generate alt text for an image. Respond ONLY with the text that should go inside "
        #    "the alt attribute of an img tag. Do not include 'Alt text:', explanations, quotes, "
        #    "or any other text. Keep the description concise and factual. It should be no more "
        #    "than 250 characters long, so please summarize. If there is text in the image, give "
        #    "those priority. Large text should come first. \n\n"
        #    f"Image details: {prompt}"
        # )
        formatted_prompt = (
            "\n\nHuman: Generate alt text for an image. Respond ONLY with the text that should go inside "
            "the alt attribute of an img tag. Keep it concise, factual, and limited to 350 characters. "
            f"Image details: {prompt}\n\nAssistant:"
        )
        payload = {
            "model": model_name,
            "prompt": formatted_prompt,
            "images": [base64_image],
        }

        # Send request to Ollama API
        # logging.info("Sending request to Ollama API...")
        start_time = time.time()
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=90)
        elapsed_time = time.time() - start_time
        logging.info(f"Response received from Ollama API in {elapsed_time:.2f} seconds.")

        # Parse the response containing multiple JSON objects
        raw_response = response.text
        # logging.debug(f"Raw Alternative Text from Ollama API: {raw_response}")

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
        logging.info(f"\nAlt text generated successfully: \n\n {final_text} \n\n")
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


# def generate_with_azure_openai(image_url, model, max_tokens, client):
def generate_with_azure_openai(image_url, max_tokens=300):
    """Generate alt text using Azure OpenAI with a given image URL."""
    
    if client is None:
        logging.error("❌ Azure OpenAI client is missing. Skipping this image.")
        return "Error: Azure OpenAI client missing"

    try:
        logging.info(f"🔵 Processing Image: {image_url}")
        print(f"🔵 Processing Image: {image_url}")

        # ✅ Fetch & Encode Image
        image_response = requests.get(image_url, stream=True)  # Renamed response
        image_response.raise_for_status()
        image_base64 = base64.b64encode(image_response.content).decode("utf-8")

        # ✅ Determine MIME Type
        mime_type = "image/jpeg"
        if image_url.lower().endswith(".png"):
            mime_type = "image/png"
        elif image_url.lower().endswith(".webp"):
            mime_type = "image/webp"

        # ✅ Format Image for OpenAI API
        image_data = f"data:{mime_type};base64,{image_base64}"

        # ✅ Prepare Prompt
        messages = [
            {"role": "system", "content": "Generate concise and descriptive alt text for an image."},
            {"role": "user", "content": "Describe this image in detail. Keep the response less than 40 words."},
            {"role": "user", "content": [{"type": "image_url", "image_url": {"url": image_data}}]}  # Correct format
        ]

        response = client.chat.completions.create( # Use the client object directly
            model=DEPLOYMENT_NAME,
            messages=messages,
            max_tokens=max_tokens,
        )

        # ✅ Extract Response
        if hasattr(response, "choices") and response.choices:
            alt_text = response.choices[0].message.content.strip()
            logging.info(f"✅ Generated Alt Text: {alt_text}")
            print(f"✅ Generated Alt Text: {alt_text}")
            return alt_text
        else:
            logging.error("❌ No valid response from OpenAI")
            return "Error: No valid response from OpenAI"

    except requests.exceptions.HTTPError as http_err:
        logging.error(f"❌ HTTP Error: {http_err.response.status_code} - {http_err.response.text}")
        if http_err.response.status_code == 404:
            logging.error(f"❌ 404 Error: Resource not found at {AZURE_OPENAI_ENDPOINT}")
        return f"HTTP Error: {http_err.response.status_code}"

    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Image retrieval error: {str(e)}")
        return f"Error: Unable to retrieve image - {str(e)}"

    except Exception as e:
        logging.error(f"❌ Unexpected error: {str(e)}")
        return f"Error: Something went wrong - {str(e)}"
    

def check_image_exists(image_url):
    """
    Check if the image URL exists by making a HEAD request with redirects enabled.
    If the URL contains query parameters, attempt checking the base URL without query strings.
    """
    try:
        # First attempt with full URL (including query params)
        response = requests.head(image_url, timeout=10, allow_redirects=True)

        # If redirected, log the new URL
        if response.history:
            logging.info(f"Redirected: {image_url} → {response.url}")

        # If image is accessible, return True
        if response.status_code == 200:
            return True

        # If the URL contains query parameters, try without them
        parsed_url = urlparse(image_url)
        if parsed_url.query:
            stripped_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
            logging.info(f"Retrying without query params: {stripped_url}")
            response = requests.head(stripped_url, timeout=10, allow_redirects=True)
            if response.status_code == 200:
                return True

        logging.warning(f"Image not found or inaccessible: {image_url} (Status: {response.status_code})")
        return False

    except requests.exceptions.RequestException as e:
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

    # Truncate the text to 350 characters if necessary
    if len(cleaned_text) > 360:
        cleaned_text = cleaned_text[:357].rsplit(" ", 1)[0] + "..."  # Truncate and add ellipsis

    return cleaned_text

# Generate alt text using BLIP with alt_text and title_text integration
def generate_alt_text(image_url, alt_text="", title_text="", model="blip", client=None):
    """Generate alt text using BLIP, Anthropic, Ollama, or Azure OpenAI."""

    while not check_internet():  # ✅ If no internet, pause execution
        print("⏳ Internet connection lost. Pausing scan... Retrying in 60 seconds.")
        time.sleep(60)

    try:
        # Check if the image exists (Wrap in retry logic)
        while not check_internet():  
            print("⏳ Internet connection lost. Retrying in 60 seconds...")
            time.sleep(60)

        # Skip SVG files (not supported)
        if image_url.lower().endswith(".svg"):
            logging.info(f"Skipping SVG file: {image_url}")
            return "Skipped: SVG file"

        # Check if the image exists
        if not check_image_exists(image_url):
            logging.info(f"Image not found or inaccessible: {image_url}")
            return "404 Image Not Found"

        # Extract OCR text if the image is text-heavy
        ocr_text = extract_text_with_ocr(image_url)
        if ocr_text:
            logging.info(f"OCR used for text-heavy image: {image_url}")
            return clean_ocr_text(ocr_text)

        # Generate alt text using the selected model
        if model == "blip":
            return generate_with_blip(image_url, alt_text, title_text)
        elif model == "anthropic":
            prompt = f"Generate concise and descriptive alt text for the following image URL: {image_url}."
            return generate_with_anthropic(prompt)
        elif model == "ollama":
            prompt = f"Generate concise and descriptive alt text for the following image URL: {image_url}."
            return generate_with_ollama(image_url, prompt)
        elif model == "azure_openai":
            # Ensure the client is provided for Azure OpenAI
            if model == "azure_openai" and client is None:
                raise ValueError("Azure OpenAI client is missing. Ensure it's properly initialized and passed.")
            return generate_with_azure_openai(image_url, max_tokens=300)
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
    parser.add_argument("-m", "--model", default=DEFAULT_MODEL, choices=["blip", "anthropic", "ollama", "azure_openai"], help="Model to use for text generation.")
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
            # row["Generated Alt Text"] = "Error: Missing image URL"
            row["Generated Alt Text"] = generate_alt_text(image_url, model=selected_model, client=client)
            continue

        # Check if the suggestions indicate alt text needs improvement
        suggestions = row.get("Suggestions", "")
        if any(problematic in suggestions for problematic in PROBLEMATIC_SUGGESTIONS):
            logging.info(f"\nGenerating alt text for row {idx + 1} due to suggestion: {suggestions}. \n\n\n")
            # row["Generated Alt Text"] = generate_alt_text(image_url, model=selected_model)
            row["Generated Alt Text"] = generate_alt_text(image_url, model=selected_model, client=client)
        else:
            logging.info(f"Alt text for row {idx + 1} seems fine. Skipping generation for {image_url}.")
            row["Generated Alt Text"] = "Skipped: Alt text sufficient \n\n\n"

    # Save updated CSV
    output_csv = input_csv.replace(".csv", "_with_alt_text.csv")
    fieldnames = data[0].keys() if data else []
    save_csv(output_csv, data, fieldnames)
    logging.info(f"Processed CSV saved to: {output_csv}")
