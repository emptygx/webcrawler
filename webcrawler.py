import requests
from bs4 import BeautifulSoup
from concurrent.futures import ProcessPoolExecutor
import concurrent.futures
import time
import os
import socket
import multiprocessing
import urllib.request
from ip2geotools.databases.noncommercial import DbIpCity

# Keywords for analysis on scams
keyword = ['phishing',
'impersonation',
'online shopping',
'recruitment',
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
        time.sleep(5)
        response = requests.get(url, timeout=5)

        # Getting information associated to current url
        response_time = response.elapsed.total_seconds()
        ip = socket.gethostbyname(response.url.split('//')[1].split('/')[0])
        region = DbIpCity.get(ip, api_key='free').region
        if region == None:
            region = " "
        
        # Parse content for keywords
        soup = BeautifulSoup(response.content, "html.parser")
        wordcount = []
        #page_content = urllib.request.urlopen(url).read().decode('utf-8')
        page_content = response.text.lower()
        if 'scam' not in page_content and 'fraud' not in page_content:
            print('irrelevant link - exiting')
            return
        wordcount = []
        for word in keyword:
            if word in page_content:
                wordcount.append('1')
            else:
                wordcount.append('0')

        # Parse html for unique urls
        links = []
        if not is_last_level:
            links = [a["href"] for a in soup.find_all(
                "a", href=True) if a["href"].startswith("http")]

            links = list(set(links))


        new_links = []
        # Append information to the text files with file lock
        with file_lock:
            # Filter out duplicates and already visited URLs
            with open(file_path, "r") as file:
                existing_links = file.readlines()
                for link in links:
                    if link + "\n" not in existing_links:
                        new_links.append(link)

            # Add information of current url to visited.txt which contains information obtained from visited urls
            with open("visited.txt", "a") as file:
                line = url + "|" + ip + "|" + region + "|" + str(response_time)
                for count in wordcount:
                    line = line + "|" + count
                line = line.replace("\n","")
                print(line)
                file.write(line + "\n")

            # Add new links to links.txt which contains all the urls to parse
            with open(file_path, "a") as file:
                for link in new_links:
                    link.rstrip('%0A')
                    file.write(link + "\n")

        return new_links

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
        title = "URL|IP|Region|Response_time"
        for word in keyword:
            title = title + "|" + word
        file.write(title + "\n")

    pointer = 0

    depth = 1
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        while depth <= max_depth:

            # Crawl initial set of urls, then batch of urls returned from previous depth subsequently
            print(f"Processing depth {depth}...")
            start_depth_time = time.time()
            next_pointer = len(open(file_path).readlines())
            futures = [executor.submit(crawl, url, file_path, file_lock, depth==max_depth) for url in open(file_path).readlines()[pointer:]]
            pointer = next_pointer

            for future in concurrent.futures.as_completed(futures):
                links = future.result()

            print(f"Depth {depth} processed in {time.time() - start_depth_time:.2f} seconds.")
            depth += 1

    print("Crawling completed.")
    print(f"Crawling completed in {time.time() - start_total_time:.2f} seconds.")

# Driver
if __name__ == "__main__":
    # Added this part for convenience but remove when time for submission and just put the initial urls in the file as stated in the pdf
    # Add starting urls to the array
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
    main(num_workers=5, max_depth=9)
