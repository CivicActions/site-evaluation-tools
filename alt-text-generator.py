import argparse
import csv
import logging
from transformers import pipeline

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize the Hugging Face model (using flan-t5-small for lightweight generation)
logging.info("Initializing the text generation model...")
# generator = pipeline("text2text-generation", model="google/flan-t5-small")
generator = pipeline("text2text-generation", model="google/flan-t5-large")

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

# Generate alt text
def generate_alt_text(image_url, pages, alt_text, title_text, instructions):
    # Provide default values for NoneType inputs
    pages = pages or "No associated pages available"
    alt_text = alt_text or "No alt text provided"
    title_text = title_text or "No title text provided"
    
    # Construct the prompt
    prompt = (
        "I would like to have alternative text for the image below that complies with WCAG 1.1.1 for accessibility."
        "There are good examples of how to do this from the US Government: https://www.section508.gov/create/alternative-text/"
        "And also from accessibility experts WebAim: https://webaim.org/techniques/alttext/"
        "And also from Harvard University: https://accessibility.huit.harvard.edu/describe-content-images"
        f"Describe the image at this URL: {image_url}.\n"
        "Please review the current alt text and title text provided for the image. "
        "If they are sufficient and accurate, validate them. "
        f"Current alt text: '{alt_text[:20]}'\n"
        f"Current title text: '{title_text[:10]}'\n"
        "If they are not helpful, generate a concise and accurate alt text that focuses on describing the visual elements of the image. "
        "The description should focus on the visual content of the image and what information it might add to a page. \n"
        "Alt text should not include file names, although the filename in the URL may give you some intention of the author about why they chose the file"
        "Alt text should not include suspicious words like: 'image of', 'graphic of', 'picture of', 'photo of', 'placeholder', 'spacer', 'tbd', 'todo', 'to do'"
        "Alt text should avoid using meaningless words like 'alt', 'chart', 'decorative', 'image', 'graphic', 'photo', 'placeholder image', 'spacer', 'tbd', 'todo', 'to do', 'undefined'"
        f"Limit reliance on text or context from the following pages: {pages[:10]}.\n"
        f"Instructions: {instructions}\n"
    )
    try:
        logging.debug(f"Generating alt text for URL: {image_url}")
        result = generator(prompt, max_length=100)[0]["generated_text"]
        # logging.debug(f"Generated alt text: {result}")
        logging.debug(f"DEBUG: Row {idx + 1} values - Image URL: {image_url}, Alt Text: {alt_text}, Title Text: {title_text}, Pages: {pages}")
        return result.strip()
    except Exception as e:
        logging.error(f"Error generating alt text for {image_url}: {e}")
        return f"Error generating alt text: {e}"


# Main function
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate alt text for images based on a CSV file.")
    parser.add_argument("-c", "--csv", required=True, help="Path to the input CSV file.")
    parser.add_argument(
        "-g",
        "--generate-instructions",
        default="Provide meaningful, concise alternative text for images, adhering to accessibility standards (WCAG 1.1.1).",
        help="Custom instructions for generating alt text.",
    )
    args = parser.parse_args()

    input_csv = args.csv
    instructions = args.generate_instructions

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

        # Retrieve other fields
        pages = row.get("Source_URLs", "")
        alt_text = row.get("Alt_text", "")
        title_text = row.get("Title", "")

        # Generate alt text
        row["Generated Alt Text"] = generate_alt_text(image_url, pages, alt_text, title_text, instructions)

    # Add image preview
    # add_image_preview(data)

    # Save updated CSV
    output_csv = input_csv.replace(".csv", "_with_alt_text.csv")
    fieldnames = data[0].keys() if data else []
    save_csv(output_csv, data, fieldnames)

    logging.info(f"Processed CSV saved to: {output_csv}")
