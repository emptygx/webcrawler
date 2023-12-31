import requests
from bs4 import BeautifulSoup
from concurrent.futures import ProcessPoolExecutor
import concurrent.futures
import time
import socket
import multiprocessing

# Links will be added to text file links.txt
# Information from crawling will be added to text file visited.txt

# Keywords for analysis on scams
keyword = ['phishing',
'impersonation',
'online shopping',
'job',
'sextortion',
'lottery',
'banking',
'malware',
'advance fee',
'ponzi']

def crawl(url, file_path, file_lock, is_last_level):
    try:
        # Send http request to url
        url = url.strip()
        response = requests.get(url, timeout=5)
        
        # Parse content for keywords
        soup = BeautifulSoup(response.content, "html.parser")
        wordcount = []
        page_content = response.text.lower()

        # Check if link has relevant content before crawling
        if 'scam' not in page_content and 'fraud' not in page_content:
            return
        
        # Substring matching for chosen set of keywords
        wordcount = []
        for word in keyword:
            if word in page_content:
                wordcount.append('1')
            else:
                wordcount.append('0')

        # Getting information (response time, country, region) associated to current url
        response_time = response.elapsed.total_seconds()

        # Get IP Address
        ip = socket.gethostbyname(response.url.split('//')[1].split('/')[0])

        # Get region data from ip-api.com API
        ip_api_res = requests.get(f'http://ip-api.com/json/{ip}').json()
        # If rate limit exceeded, print the failed response message
        if ip_api_res.get("status") == "fail":
            print(ip_api_res.get("message"))
        # Get country and region names for appending
        country = ip_api_res.get("country")
        region = ip_api_res.get("regionName")
        if region == None:
            region = "Unknown"
        if country == None:
            country = "Unknown"

        # Parse html for unique urls to add if not at max depth yet
        links = []
        if not is_last_level:
            links = [a["href"] for a in soup.find_all(
                "a", href=True) if a["href"].startswith("http")]

            links = list(set(links))

        new_links = []

        # Append information to the text files with file lock
        # Access-lock mechanism to coordinate the prcoesses and ensure mutex when writing to the file, 
        # preventing duplicate links as well
        with file_lock:
            
            # Filter out duplicates and already visited URLs
            with open(file_path, "r") as file:
                existing_links = file.readlines()
                for link in links:
                    if link + "\n" not in existing_links:
                        new_links.append(link)

            # Add information of current url to visited.txt which contains information obtained from visited urls
            with open("visited.txt", "a") as file:
                line = url + "|" + ip + "|" + country + "|" + region + "|" + str(response_time)
                for count in wordcount:
                    line = line + "|" + count
                line = line.replace("\n","")
                print(line)
                file.write(line + "\n")

            # Add new links to links.txt which contains all the unique found urls thus far
            with open(file_path, "a") as file:
                for link in new_links:
                    file.write(link + "\n")

        return new_links

    # Catches exceptions that occur while crawling a url
    except Exception as e:
        print(f"Error crawling {url}: {e}")
        return []


# Main function to manage crawling using parallel processes
def main(num_workers=12, max_depth=2):
    print("Crawling started.")
    start_total_time = time.time()
    file_path = "links.txt"

    # Create a multiprocessing manager to create a shared lock
    manager = multiprocessing.Manager()
    file_lock = manager.Lock()

    # Initialise visited.txt with the field names
    with open("visited.txt", "w") as file:
        title = "URL|IP|Country|Region|Response_time"
        for word in keyword:
            title = title + "|" + word
        file.write(title + "\n")

    # Pointer to keep track of oldest uncrawled link position in links.txt
    pointer = 0

    # Initialise depth start the loop
    depth = 1
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        while depth <= max_depth:

            # Crawl initial set of urls, then batch of urls returned from previous depth subsequently
            print(f"Processing depth {depth}...")
            start_depth_time = time.time()
            
            # Save the current eof as the next pointer to use
            next_pointer = len(open(file_path).readlines())

            # Set the current batch of urls to be those from the previous iteration onwards
            urls = open(file_path).readlines()[pointer:]
            
            # Create a list to store the Future objects
            futures = []
            
            for url in urls:
                # Executor launches a process with one of the urls to crawl
                future = executor.submit(crawl, url, file_path, file_lock, depth == max_depth)
                futures.append(future)
                
                # Introduce a delay before launching the next process,
                # so as not to exceed the geolocation API rate limit
                time.sleep(2)
            
            # Move pointer to the last crawled url
            pointer = next_pointer

            # Wait for all current depth's urls to be crawled
            for future in concurrent.futures.as_completed(futures):
                links = future.result()

            print(f"Depth {depth} processed in {time.time() - start_depth_time:.2f} seconds.")
            depth += 1

    print("Crawling completed.")
    print(f"Crawling completed in {time.time() - start_total_time:.2f} seconds.")

# Driver
if __name__ == "__main__":
    # Initialise links.txt with starting urls
    starting_urls = ["https://www.safewise.com/online-scams-to-watch-for-in-2023/", 
                     "https://consumer.ftc.gov/articles/how-avoid-government-impersonator-scam#:~:text=Scammers%20send%20emails%20and%20text,Simply%20delete%20the%20message",
                     "https://www.police.gov.sg/media-room/news/20230415_police_advisory_on_resurgence_of_government_official_impersonation_scam",
                     "https://www.fdacs.gov/Consumer-Resources/Scams-and-Fraud/Online-Shopping-Scams",
                     "https://www.todayonline.com/singapore/i-responded-scammers-offering-me-lucrative-job-offers-was-what-happened-1795246",
                     "https://www.cbc.ca/news/canada/sextortion-social-media-apps-victims-1.7014262",
                     "https://www.straitstimes.com/singapore/at-least-55-lose-over-500k-this-year-to-lottery-scam-involving-religious-figures",
                     "https://www.gfsc.gg/consumers/scams/banking-scams",
                     "https://en.wikipedia.org/wiki/Advance-fee_scam",
                     "https://www.investor.gov/protect-your-investments/fraud/types-fraud/ponzi-scheme#:~:text=A%20Ponzi%20scheme%20is%20an,with%20little%20or%20no%20risk"]
    with open("links.txt", "w") as file:
        for start_url in starting_urls:
            file.write(start_url + "\n")
    
    # Run main function to start crawling
    # Set num_workers to max number of processes to launch
    # Set max_depth to how many layers of added links to crawl from the initial set of urls
    main(num_workers=5, max_depth=10)
