**AI Alt Text Generator Script**

This Python script is designed to generate meaningful alternative text (alt text) for images based on input data provided in a CSV file. The script uses a Hugging Face language model to evaluate and improve the existing alt text and title text, and optionally adds a preview of each image for easier validation in tools like Google Sheets.

**Features**

* Generates alt text for images based on their URL, associated pages, and current alt/title text.
* Evaluates the existing alt and title text and validates or enhances it.
* Adds a preview column to display images in tools like Google Sheets.
* Supports logging for real-time debugging.
* Outputs a CSV file with enhanced alt text and image preview formulas.

**Requirements**

**1\. Python Version**

* Python 3.9 or later.
* The script depends on the following libraries:
- `transformers`: For text generation using Hugging Face models.
- `torch`: Required for PyTorch, the backend for Hugging Face.

**2\. Required Libraries**

Save: Save the requirements.txt and install the following in your terminal:

```pip3 install -r requirements.txt```


If you plan to export to Excel (optional):

```
pip install openpyxl
```

**Installation**

1.	Clone the repository or download the script file.
2.	Install the required libraries:

```
pip install transformers openpyxl
```

	3\.	Ensure your environment has network access to download the Hugging Face model (flan-t5-large).

**Alternate Installation**

1. Set Up a Python Virtual Environment
It is recommended to use a virtual environment to avoid conflicts with system-wide Python packages. To set up a virtual environment:

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate     # On Windows
```

**Usage**

Run the script using the following command:

```
python3 alt_text_generator.py -c <input_csv_file> [-g <instructions>]
```

**Arguments**

	•	\-c, \--csv (required): Path to the input CSV file. This file should contain columns such as:

	•	Image\_url: URL of the image.

	•	Alt\_text: Current alt text for the image.

	•	Title: Title attribute of the image (if available).

	•	Source\_URLs: List of pages where the image appears.

	•	Suggestions: Current suggestions for the alt text.

	•	\-g, \--generate-instructions (optional): Custom instructions for the model to improve or validate alt text. Example:

```
-g "Focus on describing the image visually. Ignore page context unless necessary."
```

**Output**

The script outputs a new CSV file in the same directory as the input file with \_with\_alt\_text appended to the filename. Example:

```
input_csv_file.csv → input_csv_file_with_alt_text.csv
```

The output file includes:

	•	Improved alt text in the Generated Alt Text column.

	•	An Image Preview column with a formula for displaying images in Google Sheets.

**Example**

**Input CSV**

```
Image_url,Alt_text,Title,Source_URLs,Suggestions
https://example.com/image1.jpg,"A placeholder image","Homepage Banner","/home,/about","Alt text seems too generic."
https://example.com/image2.png,"","Logo","/contact","Alt text is missing."
```

**Command**

```
python3 alt_text_generator.py -c input.csv -g "Focus on describing the visual content of the image."
```

**Output CSV**

```
Image_url,Alt_text,Title,Source_URLs,Suggestions,Generated Alt Text,Image Preview
https://example.com/image1.jpg,"A placeholder image","Homepage Banner","/home,/about","Alt text seems too generic.","A banner with vibrant colors featuring a placeholder.","=IMAGE(\"https://example.com/image1.jpg\")"
https://example.com/image2.png,"","Logo","/contact","Alt text is missing.","A minimalist logo in black and white.","=IMAGE(\"https://example.com/image2.png\")"
```

**Logging**

The script logs real-time progress and errors to the console. Example:

```
2025-01-23 20:15:02,123 - INFO - Initializing the text generation model...
2025-01-23 20:15:03,456 - INFO - Processing row 1 of 10...
2025-01-23 20:15:03,789 - DEBUG - Generating alt text for URL: https://example.com/image1.jpg
2025-01-23 20:15:04,101 - DEBUG - Generated alt text: "A vibrant banner with placeholder content."
```

To suppress debug logs, modify the logging level in the script:

```
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
```

**Advanced Features**

**Image Preview**

	•	The script adds a new column (Image Preview) with a formula (=IMAGE("IMAGE\_URL")) for displaying image previews in Google Sheets.

**Optional Export to Excel**

To export results directly to an Excel file (.xlsx), modify the script to include the optional openpyxl functionality.

**Troubleshooting**

	1\.	**SSL Warnings**:

	•	You may see a warning about urllib3 and LibreSSL on macOS. This is safe to ignore or resolve by installing OpenSSL:

```
brew install openssl
```

	2\.	**Model Download Issues**:

	•	Ensure your Python environment has network access to download the Hugging Face model (google/flan-t5-large).

	3\.	**Errors Generating Alt Text**:

	•	Ensure all required columns are present in the CSV (Image\_url, Alt\_text, Title).

**Future Improvements**

	•	Support for multilingual alt text generation.

	•	Enhanced visualization in Excel (e.g., embedded images instead of formulas).

	•	Integration with image-captioning models like BLIP.

**License**

This project is licensed under the MIT License. See the LICENSE file for details.

