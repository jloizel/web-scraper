import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from bs4 import MarkupResemblesLocatorWarning
import warnings

warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

startTime = datetime.now()

PAGINATED_URL = "https://historicengland.org.uk/images-books/photos/results/?searchType=HE+Archive+New&search=jlp01&filteroption=images&page={}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
}

# Function to scrape a page
def scrape_page(url):
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return None  
    
    soup = BeautifulSoup(response.text, "html.parser")
    results = soup.find_all("div", class_="archive-search-results-list__result-container")

    data = []
    for result in results:
        link = result.find("a")["href"]

        # --- IMAGE SCRAPING ---
        img_container = result.find("div", class_="archive-search-results-list__image-container")
        image_url = "No image"

        if img_container:
            noscript_tag = img_container.find('noscript')  
            if noscript_tag:
                noscript_image = noscript_tag.find('div', class_="archive-record__thumbnail")
                if noscript_image:
                    image_url = noscript_image.get('data-url', 'No image')

        # Fetch the real image URL 
        if image_url != 'No image':
            body_content = scrape_urlPage(f"https://historicengland.org.uk{image_url}")
            image_url = body_content

        # --- DETAILS SCRAPING ---
        details_container = result.find("div", class_="archive-search-results-list__details-container")
        title = "No title"
        details_dict = {}  

        if details_container:
            # Extract title
            title_container = details_container.find("div", class_="archive-search-result__title-container")
            if title_container:
                title = title_container.find("a").get_text(strip=True)

            # Extract all <dl> elements
            dl_elements = details_container.find_all("dl", class_="archive-record__dl")
            for dl in dl_elements:
                dt = dl.find("dt")  # key
                dd = dl.find("dd")  # value

                if dt and dd:
                    dt_text = dt.get_text(strip=True)  
                    dd_text = dd.get_text(strip=True)  
                    details_dict[dt_text] = dd_text  

        # print(f"Title: {title}, Image URL: {image_url}, Details: {details_dict}")

        # --- APPEND DATA ---
        row_data = {
            "Title": title,
            "Link": f"https://historicengland.org.uk{link}",
            "Image": image_url
        }
        # Merge dt: dd pairs dynamically into row_data
        row_data.update(details_dict)

        data.append(row_data)

    return data 

# Function to get the image src URL
def scrape_urlPage(url):
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Failed to retrieve page: {url}")
        return None
    
    soup = BeautifulSoup(response.text, "html.parser")
    body_content = soup.get_text(strip=True)
     
    return body_content

# Ask user how many pages to scrape
try:
    num_pages = input("Enter number of pages to scrape (leave blank for all): ").strip()
    num_pages = int(num_pages)
except ValueError:
    print("Invalid input. Scraping all pages.")
    num_pages = None

all_data = []

page = 1
while True:
    if num_pages and page > num_pages:  # Stop if user-defined limit is reached
        print(f"Reached {num_pages} pages. Stopping.")
        break

    print(f"Scraping page {page}...")
    page_data = scrape_page(PAGINATED_URL.format(page))
    
    if not page_data:  # Stop if no more results
        print("No more results found. Stopping.")
        break
    
    all_data.extend(page_data)
    page += 1

# Save results to Excel
df = pd.DataFrame(all_data)
df.to_excel("historic_england_results.xlsx", index=False, engine="openpyxl")
print("Data saved to historic_england_results.xlsx")

endTime = datetime.now()
elapsed_time = (endTime - startTime).total_seconds()

print('Script ran in', round(elapsed_time, 2), 'seconds.')
