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

def add_image_preview(data):
    for row in data:
        image_url = row.get("Image_url", "")
        if image_url:
            row["Image Preview"] = f'=IMAGE("{image_url}")'
        else:
            row["Image Preview"] = "No Image URL"

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

# Generate alt text using the Hugging Face model
def generate_alt_text(image_url, pages, alt_text, title_text, instructions):
    # Construct the prompt
    prompt = (
        f"Describe the image at this URL: {image_url}.\n"
        f"There may be valuable keywords in alt text: '{alt_text:20} (truncated to avoid bias).'\n"
        f"There may also be valuable keywords in title text: '{title_text:10} (truncated to avoid bias).'\n"
        f"The description should focus on the visual content of the image and what information might add to a page.\n"
        f"If the image is a a graph or chart, try to describe it.\n"
        f"If the image on the {pages[:5]} (truncated to avoid bias) is within a link, consider what it links to. The link name won't be important, but we should be describing what happens if a user clicks on it.\n"
        f"Limit reliance on text or context from the following pages: {pages[:10]} (truncated to avoid bias).\n"
        f"Avoide phrases like: 'Image of' or 'this is a png'. Screen reader users will already know it is an image, so it is redundant."
        f"{instructions}"
    )
    try:
        logging.debug(f"Generating alt text for URL: {image_url}")
        result = generator(prompt, max_length=100)[0]["generated_text"]
        logging.debug(f"Generated alt text: {result}")
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
        default=(
            "Please review the current alt text and title text provided for the image. "
            "If they are sufficient and accurate, validate them. "
            "If they are not helpful, generate a concise and accurate alt text that focuses on describing the visual elements of the image. "
            "This alt text must comply with WCAG 1.1.1 for accessibility."
        ),
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
        suggestion = row.get("Suggestions", "")
        if suggestion != "Alt-text passes automated tests, but does it make sense to a person?":
            image_url = row.get("Image_url", "")
            pages = row.get("Source_URLs", "")
            alt_text = row.get("Alt_text", "")
            title_text = row.get("Title", "")
            if not image_url:
                logging.warning(f"Row {idx + 1} is missing an Image URL. Skipping.")
                row["Generated Alt Text"] = "Error: Missing image URL"
                continue
            row["Generated Alt Text"] = generate_alt_text(image_url, pages, alt_text, title_text, instructions)

    # Add image preview column
    add_image_preview(data)

    # Save updated CSV
    output_csv = input_csv.replace(".csv", "_with_alt_text.csv")
    fieldnames = data[0].keys() if data else []
    save_csv(output_csv, data, fieldnames)

    logging.info(f"Processed CSV saved to: {output_csv}")
