import os
import socket
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin, urlparse, urlunparse
import argparse
from tqdm import tqdm
import xml.etree.ElementTree as ET
import json
import random
import time
from collections import defaultdict
import re
from feedparser import parse
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.data import find
from textstat import text_standard
from datetime import datetime
import time


# Check if 'punkt' tokenizer is already downloaded
try:
    find('tokenizers/punkt')
except LookupError:
    print("'punkt' not found. Downloading...")
    nltk.download('punkt')

# Check if 'stopwords' is already downloaded
try:
    find('corpora/stopwords')
except LookupError:
    print("'stopwords' not found. Downloading...")
    nltk.download('stopwords')

IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.svg', '.tiff', '.avif', '.webp')

def text_analysis(alt_text):
    if not alt_text or not alt_text.strip():
        return 0, 0
    words = re.findall(r'\b\w+\b', alt_text)
    sentences = re.split(r'[.!?]', alt_text)
    num_words = len(words)
    num_sentences = len([s for s in sentences if s.strip()])
    return num_words, num_sentences

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

def is_valid_image(url):
    if not url:
        return False
    parsed_url = urlparse(url)
    path = parsed_url.path
    valid = path.lower().endswith(IMAGE_EXTENSIONS)
    if not valid:
        print(f"Skipped: Not a valid image extension - {url}")
    return valid

# Function to extract URLs from a CSV file
def extract_urls_from_csv(file_path):
    try:
        df = pd.read_csv(file_path)
        return df['URL'].dropna().tolist() if 'URL' in df.columns else []
    except Exception as e:
        print(f"Error reading CSV file {file_path}: {e}")
        return []

# Function to extract URLs from a JSON file
def extract_urls_from_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            if isinstance(data, list):
                return [url for url in data if isinstance(url, str)]
            elif isinstance(data, dict) and 'urls' in data:
                return data['urls']
            else:
                print(f"Invalid JSON structure in {file_path}.")
                return []
    except Exception as e:
        print(f"Error reading JSON file {file_path}: {e}")
        return []

# Function to extract URLs from an RSS feed
def extract_urls_from_rss(feed_url):
    try:
        feed = parse(feed_url)
        return [entry.link for entry in feed.entries if 'link' in entry]
    except Exception as e:
        print(f"Error parsing RSS feed {feed_url}: {e}")
        return []

# Function to parse a sitemap and extract URLs
def extract_urls_from_sitemap(sitemap_url, headers=None, depth=3):
    """
    Parses a sitemap and extracts URLs, supporting multi-part sitemaps.
    
    Args:
        sitemap_url (str): The URL of the sitemap.
        headers (dict, optional): HTTP headers for the request.
        depth (int): Maximum recursion depth for nested sitemaps.

    Returns:
        list: A list of extracted URLs.
    """
    # Define extensions to exclude
    EXCLUDED_EXTENSIONS = ('.pdf', '.doc', '.docx', '.zip', '.rar', '.xlsx', '.ppt', '.pptx', '.xls', '.txt', '.rss')

    urls = set()

    if depth <= 0 or len(urls) > 50_000:  # Prevent excessive recursion or infinite loops
        print(f"⚠️ Reached max depth or too many URLs ({len(urls)}). Stopping sitemap parsing.")
        return list(urls)

    try:
        # Set default headers if none are provided
        if headers is None:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Referer": sitemap_url,  # Helps with servers that block unknown requests
            }

        print(f"🔍 Fetching sitemap: {sitemap_url}")
        response = requests.get(sitemap_url, headers=headers, timeout=10)

        if response.status_code == 403:
            print(f"❌ Access to {sitemap_url} is forbidden (403).")
            return list(urls)
        if response.status_code != 200:
            print(f"❌ Could not access {sitemap_url}, status code: {response.status_code}")
            return list(urls)

        content = response.content

        # Multi-part sitemap handling
        if b"<sitemapindex" in content:  # If the sitemap contains links to other sitemaps
            print(f"🗂️ Found multi-part sitemap at {sitemap_url}. Fetching nested sitemaps...")
            root = ET.fromstring(content)
            for sitemap in root.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap"):
                loc = sitemap.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
                if loc is not None and loc.text:
                    nested_sitemap = loc.text.strip()
                    print(f"↪️ Fetching nested sitemap: {nested_sitemap}")
                    urls.update(extract_urls_from_sitemap(nested_sitemap, headers, depth - 1))
            return list(urls)  # Return all collected URLs

        # Standard URL sitemap processing
        elif b"<urlset" in content:
            print(f"📄 Processing standard sitemap: {sitemap_url}")
            root = ET.fromstring(content)
            for url_elem in root.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}url"):
                loc = url_elem.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
                if loc is not None and loc.text:
                    full_url = loc.text.strip()
                    if not full_url.lower().endswith(EXCLUDED_EXTENSIONS):  # Skip excluded file types
                        urls.add(full_url)

        else:
            print(f"⚠️ Sitemap at {sitemap_url} is not valid XML.")

    except ET.ParseError:
        print(f"❌ Failed to parse XML content from {sitemap_url}.")
    except Exception as e:
        print(f"❌ Error processing sitemap {sitemap_url}: {e}")

    return list(urls)


def parse_sitemap(sitemap_url, base_domain, headers=None, depth=3):
    """
    Parses a sitemap to extract URLs, handling multi-part sitemaps and non-XML elements.
    Ensures only HTML pages are selected. Supports recursive sitemap parsing up to a specified depth.

    Args:
        sitemap_url (str): URL of the sitemap to parse.
        base_domain (str): The base domain for constructing full URLs.
        headers (dict, optional): Headers to use for the HTTP requests.
        depth (int): Maximum recursion depth for nested sitemaps.

    Returns:
        set: A set of valid HTML URLs.
    """
    # Define extensions to exclude
    EXCLUDED_EXTENSIONS = (
        '.pdf', '.doc', '.docx', '.zip', '.rar', '.xlsx', '.ppt', '.pptx',
        '.xls', '.txt', '.rss', '.xml', '.json', '.csv', '.mp3', '.mp4', '.avi'
    )

    urls = set()

    if depth <= 0 or len(urls) > 50_000:
        print(f"⚠️ Reached max depth or too many URLs ({len(urls)}). Stopping sitemap parsing.")
        return urls

    try:
        if headers is None:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Referer": sitemap_url,
            }

        print(f"🔍 Fetching sitemap: {sitemap_url}")
        response = requests.get(sitemap_url, headers=headers, timeout=10)

        if response.status_code == 403:
            print(f"❌ Access to {sitemap_url} is forbidden (403).")
            return urls
        if response.status_code != 200:
            print(f"❌ Could not access {sitemap_url}, status code: {response.status_code}")
            return urls

        content = response.content

        if b"<sitemapindex" in content:
            print(f"🗂️ Found multi-part sitemap at {sitemap_url}. Fetching nested sitemaps...")
            root = ET.fromstring(content)
            for sitemap in root.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap"):
                loc = sitemap.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
                if loc is not None and loc.text:
                    urls.update(parse_sitemap(loc.text.strip(), base_domain, headers, depth - 1))
            return urls

        elif b"<urlset" in content:
            root = ET.fromstring(content)
            for url_elem in root.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}url"):
                loc = url_elem.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
                if loc is not None and loc.text and is_html_url(loc.text.strip()):
                    urls.add(loc.text.strip())

    except ET.ParseError:
        print(f"❌ Failed to parse XML content from {sitemap_url}.")
    except Exception as e:
        print(f"❌ Error processing sitemap {sitemap_url}: {e}")

    return urls


def crawl_site(start_url, max_pages=100, throttle=0):
    """
    Crawls the site, adhering to rate limits and auto-throttling on access errors.
    """
    visited_urls = set()
    urls_to_visit = [start_url]
    crawled_urls = set()
    consecutive_errors = 0  # Track consecutive errors for auto-throttling

    print(f"Starting crawl for {start_url} with a target of {max_pages} unique HTML pages.")
    with tqdm(total=max_pages, desc="Crawling URLs", unit="url") as progress_bar:
        while urls_to_visit and len(crawled_urls) < max_pages:
            url = urls_to_visit.pop(0)
            if url in visited_urls:
                continue

            visited_urls.add(url)
            try:
                response = requests.get(url, timeout=10, stream=True)
                content_type = response.headers.get('Content-Type', '').lower()

                # Skip non-HTML content
                if 'text/html' not in content_type:
                    continue

                soup = BeautifulSoup(response.text, 'html.parser')
                crawled_urls.add(url)
                progress_bar.update(1)  # Update the progress bar

                # Find all links
                for a_tag in soup.find_all('a', href=True):
                    link = urljoin(url, a_tag['href'])
                    parsed_link = urlparse(link)

                    # Skip links with common non-HTML file extensions
                    if parsed_link.path.lower().endswith((
                        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.rar',
                        '.jpg', '.jpeg', '.png', '.gif', '.svg', '.tiff', '.mp4', '.mp3', '.avi', '.mov'
                    )):
                        continue

                    # Only add internal links
                    if parsed_link.netloc == urlparse(start_url).netloc and link not in visited_urls:
                        urls_to_visit.append(link)

                consecutive_errors = 0  # Reset consecutive errors on success
                time.sleep(throttle)  # Apply throttle delay

            except Exception as e:
                print(f"Failed to crawl {url}: {e}")
                consecutive_errors += 1
                if consecutive_errors > 5:
                    throttle = min(throttle + 1, 10)  # Auto-throttle with an upper limit
                    print(f"Auto-throttling applied. Current delay: {throttle}s")

    print(f"Completed crawling {len(crawled_urls)} HTML pages.")
    return list(crawled_urls)


def get_relative_url(url, base_domain):
    parsed_url = urlparse(url)
    if parsed_url.netloc == urlparse(base_domain).netloc:
        return urlunparse(('', '', parsed_url.path, parsed_url.params, parsed_url.query, parsed_url.fragment))
    return url


def is_image_visible(img):
    """
    Checks if an image is visible in the DOM.

    Returns:
        True if the image is visible, False otherwise.
    """
    parent = img.find_parent()

    # Check for CSS-based hiding
    style = img.get('style', '') + (parent.get('style', '') if parent else '')
    if any(hidden in style.lower() for hidden in ['display: none', 'visibility: hidden', 'opacity: 0']):
        return False

    # Check for aria-hidden
    if img.get('aria-hidden') == 'true' or (parent and parent.get('aria-hidden') == 'true'):
        return False

    # Check for HTML hidden attribute
    if img.has_attr('hidden') or (parent and parent.has_attr('hidden')):
        return False

    return True

def is_html_url(url):
    """
    Checks whether a URL points to an HTML document.
    
    Returns:
        True if the URL is an HTML page, False otherwise.
    """
    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        content_type = response.headers.get('Content-Type', '').lower()

        # If Content-Type is missing, fallback to GET and inspect the content
        if not content_type:
            response = requests.get(url, timeout=10, allow_redirects=True)
            content_type = response.headers.get('Content-Type', '').lower()

        if 'text/html' in content_type:
            return True

        print(f"⚠️ Skipping non-HTML content: {url} ({content_type})")
        return False
    except Exception as e:
        print(f"⚠️ Error checking content type for {url}: {e}")
        return False


def crawl_page(url, images_data, url_progress, domain, throttle, consecutive_errors):
    """
    Crawls a single page, extracting image data with rate limiting and error handling.
    """
    if not is_html_url(url):
        return consecutive_errors  # # Skip this URL without incrementing error count

    url_progress.update(1)
    start_time = time.time()

    while not check_internet():  # ✅ If no internet, pause execution
        print("⏳ Internet connection lost. Pausing scan... Retrying in 60 seconds.")
        time.sleep(60)

    try:
        # print(f"Attempting to crawl: {url}")
        try:
            print(f"🔍 Debug: Fetching URL - {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Ensure we get a successful response
        except requests.exceptions.Timeout:
            print(f"⏳ Warning: Timeout while fetching {url}. Skipping this URL.")
            return []  # Skip and move on
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: Failed to fetch {url}. Error: {e}")
            return []
        load_time = time.time() - start_time

        if response.status_code != 200:
            print(f"Non-200 status code for {url}: {response.status_code}")
            return consecutive_errors + 1

        soup = BeautifulSoup(response.text, 'html.parser')
        img_tags = soup.find_all('img')
        print(f"Found {len(img_tags)} <img> tags on {url}")

        # Keep track of seen images to skip duplicates
        seen_images = set()

        for img in img_tags:
            img_src = img.get('src')
            if not img_src:
                print(f"Skipping <img> tag with no src attribute on {url}")
                continue

            if not is_image_visible(img):  # New visibility check
                print(f"Skipping hidden image: {img_src} on {url}")
                continue

            img_url = urljoin(url, img_src)
            if img_url in seen_images:
                print(f"Duplicate image skipped: {img_url}")
                continue
            seen_images.add(img_url)

            if is_valid_image(img_url):
                process_image(img_url, img, url, domain, images_data)

        return 0

    except Exception as e:
        print(f"Error processing {url}: {e}")
        return consecutive_errors + 1


def get_images(domain, sample_size=100, throttle=0, crawl_only=False):
    """
    Fetch images and their metadata from a website.
    
    Args:
        domain (str): The base domain to analyze.
        sample_size (int): The maximum number of URLs to process.
        throttle (int): Throttle delay between requests.
        crawl_only (bool): If True, bypass sitemap and start crawling directly.
    
    Returns:
        pd.DataFrame: Dataframe containing image metadata.
    """
    images_data = defaultdict(lambda: {
        "count": 0,
        "alt_text": None,
        "title": None,
        "source_urls": [],
        "size_kb": 0
    })

    all_urls = []

    if crawl_only:
        print(f"Starting direct crawl for {domain} without checking sitemap...")
        all_urls = crawl_site(domain, max_pages=sample_size, throttle=throttle)
    else:
        # Attempt to parse sitemap
        sitemap_url = urljoin(domain, 'sitemap.xml')
        print(f"Trying to parse sitemap: {sitemap_url}")
        all_urls = list(parse_sitemap(sitemap_url, domain))
        print(f"Found {len(all_urls)} URLs in sitemap.")

        if not all_urls:
            print(f"Sitemap not found or invalid. Falling back to crawling {domain}")
            all_urls = crawl_site(domain, max_pages=sample_size, throttle=throttle)

        print(f"✅ Debug: Sampling {sample_size} random URLs from {len(all_urls)} total URLs...")
        sampled_urls = random.sample(all_urls, min(sample_size, len(all_urls)))
        print(f"✅ Debug: Successfully selected {len(sampled_urls)} URLs!")

    url_progress = tqdm(total=len(sampled_urls), desc="Processing URLs", unit="url")
    consecutive_errors = 0

    for url in sampled_urls:
        consecutive_errors = crawl_page(url, images_data, url_progress, domain, throttle, consecutive_errors)
        if consecutive_errors > 5:
            throttle = min(throttle + 1, 10)
            print(f"Auto-throttling applied. Current delay: {throttle}s")

    filtered_data = {k: v for k, v in images_data.items() if v["count"] > 0}
    print(f"Processed {len(filtered_data)} valid images.")
    return pd.DataFrame([
        {
            "Image_url": k,
            "Alt_text": v["alt_text"],
            "Title": v["title"],
            "Longdesc": v.get("longdesc"),
            "Aria_label": v.get("aria_label"),
            "Aria_describedby": v.get("aria_describedby"),
            "Count": v["count"],
            "Source_URLs": ", ".join(v["source_urls"]),
            "Size (KB)": round(v["size_kb"], 2)
        }
        for k, v in filtered_data.items()
    ])


def process_image(img_url, img, page_url, domain, images_data):
    """
    Processes a single image, fetching metadata and adding it to images_data.
    """
    try:
        response = requests.head(img_url, timeout=5, allow_redirects=True)
        size = int(response.headers.get('content-length', 0)) / 1024 if response.ok else 0
    except Exception as e:
        print(f"Failed to fetch metadata for {img_url}: {e}")
        size = 0

    alt_text = img.get('alt', None)
    title = img.get('title', None)
    longdesc = img.get('longdesc', None)
    aria_label = img.get('aria-label', None)

    # Extract text referenced by aria-describedby
    aria_describedby = img.get('aria-describedby', None)
    aria_describedby_text = None
    if aria_describedby:
        desc_element = img.find_parent().find(id=aria_describedby)
        if desc_element:
            aria_describedby_text = desc_element.get_text(strip=True)

    source_url = get_relative_url(page_url, domain)

    # Add image metadata to the dataset
    images_data[img_url].update({
        "count": images_data[img_url]["count"] + 1,
        "alt_text": alt_text,
        "title": title,
        "longdesc": longdesc,
        "aria_label": aria_label,
        "aria_describedby": aria_describedby_text,
        "size_kb": size,
    })
    if source_url not in images_data[img_url]["source_urls"]:
        images_data[img_url]["source_urls"].append(source_url)


def analyze_alt_text(images_df, domain_or_file, sample_size, scan_type="sitemap"):
    """
    Analyzes alt text and saves results to a CSV file with a custom name.

    Args:
        images_df (pd.DataFrame): Dataframe containing image data.
        domain_or_file (str): The domain or file used for scanning.
        sample_size (int): The number of URLs selected for scanning.
        scan_type (str): The type of scan (default: "sitemap").
    """
    if images_df.empty:
        print("❌ No image data available for analysis. Exiting.")
        return

    domain_name = urlparse(domain_or_file).netloc if domain_or_file.startswith("http") else os.path.basename(domain_or_file)
    current_date = datetime.now().strftime("%Y-%m-%d")
    output_file = f"{domain_name}_{scan_type}_{sample_size}_images_{current_date}.csv"
    images_df["Date"] = current_date

    suggestions = []

    wcag_failure_values = ["null", "tbd", "none", "alt text", ""]
    suspicious_words = ['image of', 'graphic of', 'picture of', 'photo of', 'placeholder', 'spacer', 'tbd', 'todo']
    meaningless_alt = ['alt', 'chart', 'decorative', 'image', 'graphic', 'photo', 'placeholder image', 'spacer', 'tbd', 'todo', 'undefined']

    for _, row in images_df.iterrows():
        alt_text = row.get('Alt_text', "")
        if alt_text is None:
            alt_text = ""  # Fix to prevent AttributeError

        img_url = row.get('Image_url', "")
        title_text = row.get('Title', "") or ""
        size_kb = row.get('Size (KB)', 0)
        suggestion = []

        if not alt_text.strip() or alt_text.strip().lower() in wcag_failure_values:
            suggestion.append("WCAG 1.1.1 Failure: Alt text is empty or invalid.")

        if isinstance(size_kb, (int, float)) and size_kb > 250:
            suggestion.append("Consider reducing the image size for a better user experience.")

        if any(word in alt_text.lower() for word in suspicious_words):
            suggestion.append("Avoid phrases like 'image of', 'graphic of', or 'todo' in alt text.")
        if alt_text.lower() in meaningless_alt:
            suggestion.append("Alt text appears meaningless. Replace it with a descriptive value.")

        words, sentences = text_analysis(alt_text)
        if len(alt_text) < 25:
            suggestion.append("Alt text seems too short. Provide more context.")
        if len(alt_text) > 250:
            suggestion.append("Alt text may be too long. Consider shortening.")
        if words / max(sentences, 1) > 20:
            suggestion.append("Consider simplifying the text.")

        if title_text.strip():
            suggestion.append("Consider removing the title text. Often, it reduces usability for screen readers.")

        if not suggestion:
            suggestion.append("Alt-text passes automated tests, but does it make sense to a person?")

        suggestions.append("; ".join(suggestion))

    images_df['Suggestions'] = suggestions
    images_df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"✅ Data saved to {output_file}")


def main(sample_size=100, throttle=0, crawl_only=False):
    """
    Main function to collect image data and analyze alt text, with throttling.
    Ensures 200 unique HTML pages are selected before processing.
    """
    urls = []

    # Extract URLs from input sources
    if args.csv:
        urls = extract_urls_from_csv(args.csv)
        print(f"Extracted {len(urls)} URLs from CSV.")
        input_file = args.csv
    elif args.json:
        urls = extract_urls_from_json(args.json)
        print(f"Extracted {len(urls)} URLs from JSON.")
        input_file = args.json
    elif args.rss:
        urls = extract_urls_from_rss(args.rss)
        print(f"Extracted {len(urls)} URLs from RSS feed.")
        input_file = args.rss
    elif args.sitemap:
        urls = extract_urls_from_sitemap(args.sitemap)
        print(f"Extracted {len(urls)} URLs from Sitemap.")
        input_file = args.sitemap
    elif args.domain:
        urls = crawl_site(args.domain, max_pages=sample_size, throttle=throttle)
        print(f"Crawled {len(urls)} URLs from domain.")
        input_file = args.domain  # Use the domain name as a placeholder

    if not urls:
        print("❌ No URLs found. Exiting.")
        exit(1)

    # ✅ Ensure all selected URLs are valid HTML pages before sampling
    valid_html_urls = set()
    attempts = 0

    print(f"🔍 Checking {len(urls)} URLs to select {sample_size} valid HTML pages...")

    while len(valid_html_urls) < sample_size and attempts < len(urls) * 2:
        random.shuffle(urls)  # Shuffle to ensure random selection
        for url in urls:
            if len(valid_html_urls) >= sample_size:
                break  # Stop if we reach the desired count
            if url not in valid_html_urls and is_html_url(url):
                valid_html_urls.add(url)
        attempts += 1

    valid_html_urls = list(valid_html_urls)  # Convert back to a list

    if len(valid_html_urls) < sample_size:
        print(f"⚠️ Warning: Only found {len(valid_html_urls)} valid HTML pages.")

    print(f"✅ Selected {len(valid_html_urls)} valid HTML URLs for processing.")

    # Crawl and parse each page to extract images
    images_data = defaultdict(lambda: {
        "count": 0,
        "alt_text": None,
        "title": None,
        "source_urls": [],
        "size_kb": 0
    })

    for url in tqdm(valid_html_urls, desc="Crawling URLs for images", unit="url"):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200 and 'text/html' in response.headers.get('Content-Type', '').lower():
                soup = BeautifulSoup(response.text, 'html.parser')
                img_tags = soup.find_all('img')
                for img in img_tags:
                    img_src = img.get('src')
                    if img_src:
                        img_url = urljoin(url, img_src)
                        process_image(img_url, img, url, args.domain if args.domain else "unknown", images_data)
            else:
                print(f"⚠️ Skipped non-HTML URL: {url}")
        except Exception as e:
            print(f"❌ Failed to crawl {url}: {e}")

    # Convert images_data to DataFrame
    filtered_data = {k: v for k, v in images_data.items() if v["count"] > 0}
    images_df = pd.DataFrame([
        {
            "Image_url": k,
            "Alt_text": v["alt_text"],
            "Title": v["title"],
            "Longdesc": v.get("longdesc"),
            "Aria_label": v.get("aria_label"),
            "Aria_describedby": v.get("aria_describedby"),
            "Count": v["count"],
            "Source_URLs": ", ".join(v["source_urls"]),
            "Size (KB)": round(v["size_kb"], 2)
        }
        for k, v in filtered_data.items()
    ])

    # Run analysis
    print(f"🔍 Running analysis on {len(images_df)} images...")
    analyze_alt_text(images_df, input_file, sample_size, scan_type="sitemap")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Scan a website or file for alt text analysis.")
    parser.add_argument("-s", "--sample_size", type=int, default=100, help="Number of URLs to sample (default: 100).")
    parser.add_argument("-t", "--throttle", type=int, default=1, help="Throttle delay between requests (default: 1).")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-c", "--csv", help="Path to a CSV file containing URLs.")
    group.add_argument("-j", "--json", help="Path to a JSON file containing URLs.")
    group.add_argument("-r", "--rss", help="RSS feed URL to extract URLs.")
    group.add_argument("-x", "--sitemap", help="Sitemap URL to extract URLs.")
    group.add_argument("-d", "--domain", help="Domain to crawl for URLs.")
    args = parser.parse_args()

    # Debugging: Print parsed arguments
    print(f"Parsed arguments: {args}")

    # Call the main function
    main(sample_size=args.sample_size, throttle=args.throttle, crawl_only=False)
