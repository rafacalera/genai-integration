import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("Scraping timed out")

signal.signal(signal.SIGALRM, timeout_handler)

def get_all_links(base_url):
    start_time = time.time()
    visited_urls = set()
    urls_to_visit = [base_url]
    
    signal.alarm(30)

    try: 
        while urls_to_visit:
        
            url = urls_to_visit.pop(0)
        
            if url in visited_urls:
                continue
        
            visited_urls.add(url)

            response = requests.get(url)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for link in soup.find_all('a', href=True):
                    full_url = urljoin(base_url, link['href'])
                    
                    if urlparse(full_url).netloc == urlparse(base_url).netloc and full_url not in visited_urls:
                        urls_to_visit.append(full_url)
    except TimeoutError:
        signal.alarm(0)
        return list(visited_urls.union(urls_to_visit))
    
    return visited_urls

def scrape_site(base_url):
    all_links = get_all_links(base_url)
    
    for link in all_links:
        try:
            response = requests.get(link)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                print(f"Scraping: {link}")
            
                title = soup.find('title').text if soup.find('title') else 'No title'
                content = soup.get_text()
                
                print(f"Title: {title}")
                print(f"Content: {content[:200]}...")
        except Exception as e:
            print(f"Error scraping {link}: {e}")

if __name__ == "__main__":
    base_url = 'https://www.apple.com/'
    scrape_site(base_url)
