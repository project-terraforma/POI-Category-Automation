POI Categorization Repository PROJECT B

A repo for organizing and categorizing Points of Interest (POIs) using an LLM base, web-scraping, and a couple more magic spells

## What’s Inside

1. Scripts
   * POI-Categorization-webscraping.py – crawls and extracts POI details from business websites
   * POI-Categorization-socialscraping.py – gathers POI metadata from social platforms and review sites
   * category-tree.py – utilities to parse, traverse and manipulate the POI category hierarchy

2. Notebooks
   * POI-Categorization(original).ipynb – first-pass exploration and baseline experiments
   * POI-Categorization(cheaper).ipynb – cost optimized pipeline tweaks and performance comparisons
   * POI_Alt-Category-Automation.ipynb – automated routines for bulk category assignments and rule based tagging

3. Data
   * category_tree.json – JSON file defining the full category taxonomy for POIs

## Why This Toolkit

This repository is modular so you can mix and match scraping methods with your own data flows  
It is scalable with notebooks demonstrating both proofs of concept and production ready strategies  
It is extensible since the category tree lives in JSON and can be updated by editing a single file  

# Getting Started

1. Clone the repo  
   ```bash
   git clone https://github.com/project-terraforma/POI-Category-Automation
   cd poi-categorization
 2. Install dependencies
   ```bash
   pip install -r requirements.txt

 3. Explore the category tree
   ```bash
   python category-tree.py --print-tree

 4. Run a quick scrape
   ```bash
   python POI-Categorization-webscraping.py --input urls.txt --output pois.csv

 5. Open the notebooks
   ```bash
   jupyter lab
