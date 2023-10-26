import requests
from bs4 import BeautifulSoup
from concurrent.futures import ProcessPoolExecutor
import concurrent.futures
import time


# Function to crawl a given URL and extract links
def crawl(url, visited_urls):
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.content, "html.parser")
        links = [a["href"] for a in soup.find_all("a", href=True) if a["href"].startswith("http")]
        
        # Filter out already visited URLs
        links = [link for link in links if link not in visited_urls]
        
        # Add new links to the text file
        with open("links.txt", "a") as file:
            for link in links:
                file.write(link + "\n")
        
        return links
    except Exception as e:
        print(f"Error crawling {url}: {e}")
        return []

# Main function to manage crawling using parallel processes
def main(start_url, num_workers=5, max_depth=3):
    visited_urls = set()
    visited_urls.add(start_url)
    with open("links.txt", "w") as file:
        file.write(start_url + "\n")

    depth = 1
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        while depth <= max_depth:
            print(f"Processing depth {depth}...")
            start_time = time.time()
            futures = [executor.submit(crawl, url, visited_urls) for url in visited_urls]
            visited_urls.clear()

            for future in concurrent.futures.as_completed(futures):
                links = future.result()
                visited_urls.update(links)

            depth += 1
            print(f"Depth {depth} processed in {time.time() - start_time:.2f} seconds.")
    print("Crawling completed.")


# Example usage
if __name__ == "__main__":
    start_url = "https://www.safewise.com/online-scams-to-watch-for-in-2023/"  # Replace this with your desired starting URL
    main(start_url, num_workers=5, max_depth=2)
