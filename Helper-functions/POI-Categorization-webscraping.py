import overturemaps as om
from overturemaps import core
import overturemaps
import pandas
import geopandas as gpd
from shapely import wkb
from lonboard import Map, PolygonLayer, ScatterplotLayer
import ipywidgets as widgets
import numpy as np
from IPython.display import display
import json
import requests
from bs4 import BeautifulSoup
import time
import concurrent.futures
import tqdm
import dspy
import os
from urllib.parse import urlparse
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM


with open('Data/category_tree.json', 'r') as f:
    category_tree = json.load(f)

def create_map(dataset):
    layer = ScatterplotLayer.from_geopandas(
        dataset,
        get_fill_color=[255, 0, 0],
        radius_min_pixels=5,
    )

    view_state = {
        "longitude": (bbox[0] + bbox[2]) / 2,
        "latitude": (bbox[1] + bbox[3]) / 2,
        "zoom": 8,
        "pitch": 45,
    }
    m = Map(layer, view_state=view_state)
    return m

def get_first_website(websites_list):
    if websites_list and isinstance(websites_list, list) and len(websites_list) > 0 and websites_list[0] and isinstance(websites_list[0], str):
        return websites_list[0]
    return ""

def ensure_http_scheme(url):
    parsed = urlparse(url)
    if not parsed.scheme:
        return 'http://' + url
    return url

def scrape_website(url, timeout = 5, retries=3) -> str:

    url = ensure_http_scheme(url)
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()  # Raise an error for bad responses
            soup = BeautifulSoup(response.text, 'html.parser')

            title = soup.title.string if soup.title and soup.title.string else 'No title found'
            meta_tag = soup.find('meta', attrs={'name': 'description'})
            meta_desc =  meta_tag.get("content", "").strip() if meta_tag else ""

            h1_tag = [tag.get_text(strip=True) for tag in soup.find_all('h1')]

            screaped_text = f"Title: {title}. Meta Description: {meta_desc}. Heading: {';'.join(h1_tag)}"

            return screaped_text
        
        except Exception as e:
            time.sleep(1)
            print(f"Failed to Scrape: {url}: {e}")
    return "Scraping failed after multiple tries"
    
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def summarize_scraped_text(text):
    if not text or text.strip() == "Scraping error" or text.strip() == "Website error":
        print(f"Raw scraped content:\n{text}\n")
        return None
    
    input_length = len(text.split())  # rough estimate of token count
    dynamic_max_length = max(8, min(30, input_length // 2 + 5))
    
    try:
        summary = summarizer(text, min_length=10, max_length=dynamic_max_length, do_sample=False)
        return summary[0]['summary_text'].strip()
    except Exception as e:
        print(f"Summarization failed: {e}")
        return "Summarization error."
    
# specify bounding box
bbox = 9.0894, 45.5342, 9.1094, 45.5542

place_dataset = core.geodataframe("place", bbox=bbox)

# Read the categories.txt file
with open('Data/categories.txt', 'r') as file:
    categories_data = file.readlines()
categories_data = categories_data[1:]

# Split the data by semicolons and extract the part before the semi-colon
categories_list = [entry.split(';')[0] for entry in categories_data]

## -------------------------------- Webscraping and Summarization --------------------------------

# Pulling out the places and websites
websites = {}
number = 0
for i in range(len(place_dataset.id)):
    # print(f"Place: {place_dataset.names[i]['primary']}")
    number += 1
    websites[place_dataset.names[i]['primary']] = place_dataset.websites[i]

# Save all websites as a comma-separated string
websites_str = " , ".join(
    site[0] if site is not None and len(site) > 0 else "Website error"
    for site in websites.values()
)

# Create a string with "place: website" for each entry
place_website_str = " , ".join(
    f"{place}: {websites[place][0] if websites[place] is not None and len(websites[place]) > 0 else 'Website error'}"
    for place in websites
)

scraped_count = 0
total_websites = len(websites)
progress_step = max(1, total_websites // 20)  # 5% step

def scrape_site_wrapper(args):
    global scraped_count
    place, site = args
    if site is not None and len(site) > 0 and site[0] != "Website error":
        try:
            scraped_content = scrape_website(site[0])
            result = (place, scraped_content if scraped_content else "Scraping error")
        except Exception:
            result = (place, "Scraping error")
    else:
        result = (place, "Website error")
    scraped_count += 1
    if scraped_count % progress_step == 0 or scraped_count == total_websites:
        percent = (scraped_count / total_websites) * 100
        # print(f"{scraped_count}/{total_websites} ({percent:.1f}%) websites scraped")
    return result

max_workers=min(64, os.cpu_count() * 5) #or 3000
with concurrent.futures.ThreadPoolExecutor(max_workers) as executor:
    print(max_workers)
    results = list(executor.map(scrape_site_wrapper, websites.items()))

scraped_websites = dict(results)
summarized_scraped_data = {}

for name, text in tqdm.tqdm(scraped_websites.items()):
    summarized_scraped_data[name] = summarize_scraped_text(text)

print(summarized_scraped_data)