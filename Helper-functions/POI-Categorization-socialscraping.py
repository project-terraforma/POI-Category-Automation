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

def scrape_website(url, timeout = 5):
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()  # Raise an error for bad responses
        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.title.string if soup.title else 'No title found'
        meta_desc =  ""
        meta_tag = soup.find('meta', attrs={'name': 'description'})
        if meta_tag:
            meta_desc = meta_tag.get('content', '')

        h1_tag = [tag.get_text(strip=True) for tag in soup.find_all('h1')]

        screaped_text = f"Title: {title}. Meta Description: {meta_desc}. Heading: {';'.join(h1_tag)}"

        return screaped_text
    
    except Exception as e:
        print(f"Failed to Scrape: {url}: {e}")
        return ""
    
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def summarize_scraped_text(text):
    if not text:
        return None
    
    input_length = len(text.split())
    dynamic_max = max(8, min(30, input_length // 2 + 5))
    dynamic_min = max(15, dynamic_max // 3)
    
    try:
        summary = summarizer(text, min_length=dynamic_min, max_length=dynamic_max, do_sample=False)
        return summary[0]['summary_text'].strip()
    except Exception as e:
        # print(f"Summarization failed: {e}")
        return "Summarization error."
    
# specify bounding box
bbox = 9.0894, 45.4942, 9.0994, 45.5042

place_dataset = core.geodataframe("place", bbox=bbox)
print(place_dataset.shape)

# Read the categories.txt file
with open('Data/categories.txt', 'r') as file:
    categories_data = file.readlines()
categories_data = categories_data[1:]

# Split the data by semicolons and extract the part before the semi-colon
categories_list = [entry.split(';')[0] for entry in categories_data]
    
# Pulling out the places' social media links
socials_dict = {}
for i in range(len(place_dataset.id)):
    place_name = place_dataset.names[i]['primary']
    social_links = place_dataset.socials[i]
    socials_dict[place_name] = social_links

socials_str_list = []
for place_name, social_links_list in socials_dict.items():
    if social_links_list:
        # If social_links_list is a list of strings:
        if isinstance(social_links_list, list) and all(isinstance(link, str) for link in social_links_list):
            links_str = ", ".join(social_links_list)
        # If social_links_list is a dictionary (e.g., {'facebook': 'url', 'instagram': 'url'}):
        elif isinstance(social_links_list, dict):
            links_str = ", ".join([f"{platform}: {url}" for platform, url in social_links_list.items()])
        # Add more conditions if other structures are possible or convert to string directly
        else:
            links_str = str(social_links_list) # Fallback to string conversion
        socials_str_list.append(f"{place_name}: [{links_str}]")
    else:
        socials_str_list.append(f"{place_name}: No socials found")

scraped_socials_content = {}
tasks_for_social_scraping = []

for place_name, social_links_list in socials_dict.items():
    if social_links_list is not None:
        if isinstance(social_links_list, (list, np.ndarray)):
            for social_url in social_links_list:
                if isinstance(social_url, str) and social_url.startswith(('http://', 'https://')):
                    tasks_for_social_scraping.append((place_name, social_url))
        elif isinstance(social_links_list, str) and social_links_list.startswith(('http://', 'https://')): # Handle case where it might be a single string
            tasks_for_social_scraping.append((place_name, social_links_list))


total_social_urls = len(tasks_for_social_scraping)
scraped_social_urls_count = 0
progress_step_social = max(1, total_social_urls // 20) if total_social_urls > 0 else 1

def scrape_social_url_wrapper(args):
    global scraped_social_urls_count
    place_name, url = args
    scraped_content = scrape_website(url) # Using the existing scrape_website function
    
    # Increment and print progress
    scraped_social_urls_count += 1
    if total_social_urls > 0 and (scraped_social_urls_count % progress_step_social == 0 or scraped_social_urls_count == total_social_urls):
        percent = (scraped_social_urls_count / total_social_urls) * 100
        print(f"Scraped {scraped_social_urls_count}/{total_social_urls} ({percent:.1f}%) social URLs.")
        
    return place_name, url, scraped_content if scraped_content else "Scraping Failed or No Content"

print(f"Found {total_social_urls} social URLs to scrape.")

# Use ThreadPoolExecutor for concurrent scraping
with concurrent.futures.ThreadPoolExecutor(max_workers=3000) as executor: # Adjusted max_workers for social media sites
    social_results = list(executor.map(scrape_social_url_wrapper, tasks_for_social_scraping))

# Store the results
for place_name, url, content in social_results:
    if place_name not in scraped_socials_content:
        scraped_socials_content[place_name] = []
    scraped_socials_content[place_name].append({url: content})
        
if not scraped_socials_content:
    print("No social media content was scraped.")

formatted_social_info_output_list = []

if isinstance(scraped_socials_content, dict):
    for place_name_key, list_of_content_dicts in scraped_socials_content.items():
        # list_of_content_dicts is a list of dicts, e.g., [{'url1': 'scraped_text1'}, {'url2': 'scraped_text2'}]
        
        all_scraped_texts_for_this_place = []
        for single_url_content_dict in list_of_content_dicts:
            for scraped_text_item in single_url_content_dict.values():
                if scraped_text_item and isinstance(scraped_text_item, str): # Ensure it's a non-empty string
                    all_scraped_texts_for_this_place.append(scraped_text_item)
        
        aggregated_social_info = " | ".join(all_scraped_texts_for_this_place)
        
        # Escape double quotes in place_name_key and aggregated_social_info to ensure valid string literals in the output
        place_name_escaped = str(place_name_key).replace('"', '\\"')
        aggregated_social_info_escaped = aggregated_social_info.replace('"', '\\"')
        
        formatted_line = f'"{place_name_escaped}": "{aggregated_social_info_escaped}"'
        formatted_social_info_output_list.append(formatted_line)

    if not formatted_social_info_output_list:
        print("No social media content was available in scraped_socials_content to format.")
else:
    print("Variable 'scraped_socials_content' is not a dictionary. Cannot produce formatted social info.")

summarized_socials = {}

for place_name, list_of_content_dicts in scraped_socials_content.items():
    all_texts = []
    for single_url_content_dict in list_of_content_dicts:
        scraped_text_item = next(iter(single_url_content_dict.values()))
        if scraped_text_item and isinstance(scraped_text_item, str):
            all_texts.append(scraped_text_item)

    aggregated_social_info = " | ".join(all_texts)
    summary = summarize_scraped_text(aggregated_social_info)
    if summary:
        summarized_socials[place_name] = summary
    else:
        # If no summary, store raw aggregated text or a placeholder
        summarized_socials[place_name] = aggregated_social_info or "No social content"

output_items = []
for place, summary_text in summarized_socials.items():
    # Escape any internal double quotes
    place_escaped = place.replace('"', '\\"')
    summary_escaped = summary_text.replace('"', '\\"')
    output_items.append(f'"{place_escaped}": "{summary_escaped}"')

# Join with ',,, ' and print whole line
final_output_line = ",,, ".join(output_items)
print(final_output_line)