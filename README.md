## POI Categorization Automation

A repository for organizing and categorizing Points of Interest (POIs) using an LLM base, Web-Scraping, Social-Scraping and Rule Based Approach

## What’s Inside

1. Scripts
   * POI-Categorization-webscraping.py – crawls and extracts POI details from business websites
   * POI-Categorization-socialscraping.py – gathers POI metadata from social platforms
   * category-tree.py – utilities to parse, and traverse the POI category hierarchy

2. Notebooks
   * POI-Categorization(original).ipynb – first-pass exploration and baseline experiments with original expensive approach
   * POI-Categorization(cheaper).ipynb – cost optimized pipeline tweaks and performance comparisons
   * POI_Alt-Category-Automation.ipynb – Application to predict alternative categories using LLM call

3. Data
   * category_tree.json – JSON file defining the full category taxonomy for POIs 

# Getting Started

1. Clone the repo  
  ```bash
  git clone https://github.com/project-terraforma/POI-Category-Automation
  cd POI-Category-Automation
  ```
2. Install dependencies
  ```bash
  open POI-Categorization(original).ipynb
  Run 1st cell
  ```

3. Explore web-scraping
  ```bash
  cd Helper-functions
  python POI-Categorization-webscraping.py
  ```

4. Explore social-scraping
  ```bash
  cd Helper-functions
  python POI-Categorization-socialscraping.py
  ```

5. Run POI Categorization (Original)
  ```bash
  Open POI-Categorization(original).ipynb
  Replace: API key = <Your API key>
  Run All
  ```