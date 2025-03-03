#!/bin/bash
#
# Script Name: image_alt_text_generator.sh
# Description: This script generates a concise and descriptive alt text for an image 
#              using the Ollama API. It supports both local image files and remote 
#              image URLs.
#
# Usage:
#   ./image_alt_text_generator.sh <image_url_or_file> [model_name] [custom_prompt]
#
# Arguments:
#   <image_url_or_file>  - Required. The local file path or URL of the image.
#   [model_name]         - Optional. AI model to use (default: "llama3.2-vision").
#   [custom_prompt]      - Optional. Custom text prompt for image analysis 
#                          (default: "Describe the image. Be concise and descriptive...").
#
# Features:
# - Accepts an image file path or a URL as input.
# - Downloads the image if a URL is provided.
# - Converts images to Base64 for API compatibility.
# - Uses the Ollama API to generate a descriptive alt text.
# - Handles various error cases, such as invalid files or failed downloads.
#
# Dependencies:
# - `curl`: Required for downloading images and making API requests.
# - `base64`: Needed to encode images.
# - `jq`: Used for parsing JSON responses from the API.
#
# Example Usage:
#   ./image_alt_text_generator.sh example.jpg
#   ./image_alt_text_generator.sh https://example.com/image.png
#   ./image_alt_text_generator.sh image.jpg "custom-model" "Describe the scene in detail."

# Check if the user provided the required argument
if [ $# -lt 1 ]; then
    echo "Usage: $0 <image_url_or_file> [model_name] [custom_prompt]"
    exit 1
fi

# Variables
INPUT=$1
MODEL=${2:-"llama3.2-vision"}
CUSTOM_PROMPT=${3:-"Describe the image. Be concise and descriptive. The response shouldn't be more than 140 characters."}
OLLAMA_API_URL="http://localhost:11434/api/generate"

# Function to encode image file to base64
encode_image_to_base64() {
    local image_file=$1
    if [ ! -f "$image_file" ] || [ ! -s "$image_file" ]; then
        echo "Error: File not found or empty - $image_file"
        exit 1
    fi
    base64 -i "$image_file" | tr -d '\n'
}

# Handle URL or local file input
if [[ "$INPUT" =~ ^https?:// ]]; then
    TEMP_IMAGE=$(mktemp /tmp/image.XXXXXX)  # Temporary file
    echo "Downloading image from URL: $INPUT"
    curl -s -o "$TEMP_IMAGE" "$INPUT"

    if [ $? -ne 0 ] || [ ! -s "$TEMP_IMAGE" ]; then
        echo "Error: Failed to download image or file is empty."
        rm -f "$TEMP_IMAGE"
        exit 1
    fi

    FILE_TYPE=$(file --mime-type -b "$TEMP_IMAGE")
    echo "DEBUG: Downloaded file type: $FILE_TYPE"

    case "$FILE_TYPE" in
        image/png|image/jpeg|image/gif)
            BASE64_IMAGE=$(encode_image_to_base64 "$TEMP_IMAGE")
            ;;
        *)
            echo "Error: Unsupported file type - $FILE_TYPE"
            rm -f "$TEMP_IMAGE"
            exit 1
            ;;
    esac
    rm -f "$TEMP_IMAGE"  # Clean up
else
    if [ -f "$INPUT" ]; then
        BASE64_IMAGE=$(encode_image_to_base64 "$INPUT")
    else
        echo "Error: $INPUT is not a valid file."
        exit 1
    fi
fi

# Validate Base64 encoding
if [ -z "$BASE64_IMAGE" ]; then
    echo "Error: Base64 encoding failed."
    exit 1
fi

# Prepare the payload with the custom prompt
PAYLOAD=$(cat <<EOF
{
  "model": "$MODEL",
  "prompt": "$CUSTOM_PROMPT",
  "images": ["$BASE64_IMAGE"]
}
EOF
)

# Debugging: Print the payload being sent to the API
# echo "DEBUG: Payload being sent to API:"
# echo "$PAYLOAD" | jq

# Send the request to the Ollama API
RESPONSE=$(curl -s -X POST "$OLLAMA_API_URL" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD")

# Debugging: Print the raw response
# echo "DEBUG: Raw response from API:"
# echo "$RESPONSE"

# Extract and display the response content
ALT_TEXT=$(echo "$RESPONSE" | jq -r '.response // "Error: No response from API"')
echo "Alt Text: $ALT_TEXT"
