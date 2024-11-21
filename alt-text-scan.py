import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin, urlparse, urlunparse
import argparse
from tqdm import tqdm
import xml.etree.ElementTree as ET
import random
import time
from collections import defaultdict
import re
from textblob import TextBlob
from readability.readability import Document
from textstat import text_standard
from datetime import datetime

IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.svg', '.tiff', '.avif', '.webp')

def is_valid_image(url):
    return url.lower().endswith(IMAGE_EXTENSIONS)

def parse_sitemap(sitemap_url):
    """
    Parses a sitemap to extract URLs, handling sitemaps with non-XML elements.
    """
    urls = set()
    try:
        response = requests.get(sitemap_url)
        if response.status_code != 200:
            print(f"Could not access {sitemap_url}")
            return urls

        content = response.content

        # Remove non-XML content (e.g., comments, stylesheets) if they exist
        if content.startswith(b"<?xml") or b"<sitemapindex" in content or b"<urlset" in content:
            try:
                # Parse the XML content
                root = ET.fromstring(content)
                for elem in root.iter():
                    if elem.tag.endswith("sitemap") and elem.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc") is not None:
                        nested_sitemap = elem.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text
                        urls.update(parse_sitemap(nested_sitemap))
                    elif elem.tag.endswith("url") and elem.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc") is not None:
                        url = elem.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text
                        urls.add(url)
            except ET.ParseError:
                print(f"Failed to parse XML content from {sitemap_url}. Falling back to manual crawling.")
        else:
            print(f"Sitemap at {sitemap_url} is not valid XML. Falling back to manual crawling.")
            return urls

    except Exception as e:
        print(f"Failed to parse sitemap {sitemap_url}: {e}")
    
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



def get_images(domain, sample_size=100, throttle=0):
    images_data = defaultdict(lambda: {"count": 0, "alt_text": None, "title": None, "source_urls": [], "size_kb": 0, "load_time": 0})

    sitemap_url = urljoin(domain, 'sitemap.xml')
    all_urls = list(parse_sitemap(sitemap_url))
    
    # Fallback to crawling the site if the sitemap is empty
    if not all_urls:
        print(f"Sitemap not found or invalid. Falling back to crawling the site: {domain}")
        all_urls = crawl_site(domain, max_pages=sample_size, throttle=throttle)

    sampled_urls = random.sample(all_urls, min(sample_size, len(all_urls)))
    print(f"Sampling {len(sampled_urls)} URLs out of {len(all_urls)} total found URLs.")

    url_progress = tqdm(total=len(sampled_urls), desc="Processing URLs", unit="url")
    consecutive_errors = 0  # Track consecutive errors for auto-throttling

    for url in sampled_urls:
        consecutive_errors = crawl_page(url, images_data, url_progress, domain, throttle, consecutive_errors)

        # Auto-throttle if too many consecutive errors
        if consecutive_errors > 5:
            throttle = min(throttle + 1, 10)  # Increment throttle with an upper limit
            print(f"Auto-throttling applied. Current delay: {throttle}s")

    # Remove entries with count == 0
    images_data_filtered = {k: v for k, v in images_data.items() if v["count"] > 0}

    rows = []
    for img_url, data in images_data_filtered.items():
        rows.append({
            "Image_name": img_url.split('/')[-1],
            "Image_url": img_url,
            "Alt_text": data["alt_text"],
            "Title": data["title"],
            "Count": data["count"],
            "Source_URLs": f'"{", ".join(set(data["source_urls"]))}"',
            "Size (KB)": round(data.get("size_kb", 0), 2),
            "Load_Time (s)": round(data.get("load_time", 0), 2)
        })
    df = pd.DataFrame(rows)
    url_progress.close()
    return df


def crawl_page(url, images_data, url_progress, domain, throttle, consecutive_errors):
    """
    Crawls a single page, extracting image data with rate limiting and error handling.
    """
    url_progress.update(1)
    start_time = time.time()
    found_images = False  # Track if any valid images are found

    try:
        response = requests.get(url)
        load_time = time.time() - start_time

        if response.status_code != 200:
            images_data[url]["load_time"] = load_time
            return consecutive_errors + 1  # Increment consecutive errors

        soup = BeautifulSoup(response.text, 'html.parser')
        img_tags = soup.find_all('img')

        for img in img_tags:
            img_src = img.get('src')
            if img_src:
                img_url = urljoin(url, img_src)
                if is_valid_image(img_url):
                    found_images = True  # Set flag to True when at least one valid image is found
                    image_name = img_url.split('/')[-1]

                    # Check for decorative images explicitly
                    if img.has_attr('alt') and img['alt'] == "":
                        alt_text = ""
                    elif img.has_attr('alt'):
                        alt_text = img['alt']
                    else:
                        alt_text = None

                    title = img.get('title') if img.has_attr('title') else None

                    response = requests.head(img_url, allow_redirects=True)
                    size = int(response.headers.get('content-length', 0)) / 1024 if response.ok else 0

                    images_data[img_url]["count"] += 1
                    images_data[img_url]["alt_text"] = alt_text
                    images_data[img_url]["title"] = title
                    images_data[img_url]["size_kb"] = size
                    # Normalize the relative URL (remove fragments)
                    relative_url = get_relative_url(url, domain)
                    normalized_url = urlparse(relative_url)._replace(fragment="").geturl()

                    # Add the normalized URL to source_urls if not already added
                    if normalized_url not in images_data[img_url]["source_urls"]:
                        images_data[img_url]["source_urls"].append(normalized_url)

        images_data[url]["load_time"] = load_time

        if not found_images:  # Remove the page if no images are found
            images_data.pop(url, None)

        time.sleep(throttle)  # Apply throttle delay
        return 0  # Reset consecutive errors on success

    except Exception as e:
        load_time = time.time() - start_time
        images_data[url]["load_time"] = load_time
        print(f"Failed to process {url}: {e}")
        time.sleep(throttle)  # Apply throttle even on failure
        return consecutive_errors + 1  # Increment consecutive errors



def analyze_alt_text(images_df, domain, readability_threshold=8):
    # Add a date column to the images DataFrame
    current_date = datetime.now().strftime("%Y-%m-%d")
    images_df["Date"] = current_date

    suggestions = []

    for _, row in images_df.iterrows():
        alt_text = row['Alt_text']
        img_url = row['Image_url']
        title_text = row.get('Title', None)  # Fetch the Title attribute
        suggestion = []

        # Check for aria-hidden or hidden attributes (simulate by searching in the source HTML if available)
        source_html = row.get('Source_HTML', '')  # Assuming you can extract source HTML as an additional column
        if re.search(r'aria-hidden="true"|hidden(?:="hidden")?', source_html):
            suggestion.append("Image hidden with no semantic value.")
        elif pd.isna(alt_text):  # No alt text provided
            suggestion.append("No alt text provided.")
        elif re.search(r'\.svg$', img_url, re.IGNORECASE) and (pd.isna(alt_text) or alt_text.strip() == ""):
            suggestion.append("Check if the SVG file includes a title.")
        elif alt_text.strip() == "" or alt_text.strip() == " ":
            suggestion.append("Decorative image.")
        else:
            # Existing checks
            if re.search(r'\.(png|jpg|jpeg|gif|svg)', alt_text, re.IGNORECASE):
                suggestion.append("Avoid including file extensions in alt text.")
            if len(alt_text) < 25:
                suggestion.append("Alt text is too short. Provide more context.")
            if len(alt_text) > 250:
                suggestion.append("Alt text is too long. Consider shortening.")
            if re.search(r'\b(A picture of|An image of|A graphic of)\b', alt_text, re.IGNORECASE):
                suggestion.append("Avoid phrases like 'A picture of', 'An image of', or 'A graphic of' in alt text.")
            
            # Check readability and apply threshold logic
            readability_score = text_standard(alt_text, float_output=True)
            if readability_score > readability_threshold:
                suggestion.append("Consider simplifying the text.")

        # Add a suggestion for title text if present
        if title_text and title_text.strip():
            suggestion.append("Consider removing the title text.")

        # Add "Alt-text passes automated tests." only if no other suggestions are present
        if not suggestion:
            suggestion.append("Alt-text passes automated tests.")

        suggestions.append("; ".join(suggestion) if suggestion else "")

    images_df['Suggestions'] = suggestions

    # Save the updated DataFrame to CSV
    csv_filename = f"{urlparse(domain).netloc}_images.csv"
    images_df.to_csv(csv_filename, index=False, encoding='utf-8')
    print(f"Data saved to {csv_filename}")


def main(domain, sample_size=100, throttle=0):
    """
    Main function to collect image data and analyze alt text, with throttling.
    """
    # Collect images and their metadata
    images_df = get_images(domain, sample_size=sample_size, throttle=throttle)

    # Run the alt text analysis and append suggestions
    analyze_alt_text(images_df, domain)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Crawl a website and collect image data with alt text.")
    parser.add_argument('domain', type=str, help='The domain to crawl (e.g., https://example.com)')
    parser.add_argument('--sample_size', type=int, default=100, help='Number of URLs to sample from the sitemap')
    parser.add_argument('--throttle', type=int, default=1, help='Throttle delay (in seconds) between requests')
    args = parser.parse_args()
    main(args.domain, args.sample_size, throttle=args.throttle)
