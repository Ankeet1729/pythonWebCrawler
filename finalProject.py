import argparse
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import lxml
from colorama import init, Fore, Style
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

visited = set()  # Initialized an empty set which would store the already visited sites
count = {}  # dictionary for storing the number of files
files = {}  # dictionary for storing the file names
max_depth=0 # A variable for storing the number of recursions performed (this will be useful when there is no threshold provided)

def crawl_noHandle(url, threshold, output_file):

    # Finding the domain of the url passed as command line argument
    parsed_url = urlparse(url)
    input_domain = parsed_url.netloc


    # This function extracts the file type of the link being analyzed
    def extract_file_type(link):
        parsed_url = urlparse(link)
        path = parsed_url.path
        file_type = None
        if "." in path.split("/")[-1]:
            file_type = path.split("/")[-1].split(".")[-1].lower()
        return file_type

    def process_url(url, depth):

        # Returning if url already visited or depth has exceeded the maximum threshold
        if url in visited or (threshold is not None and depth > threshold):
            global max_depth
            max_depth=max(depth,max_depth)
            return

        visited.add(url)  # Add the URL to the set of visited URLs to keep track of visited pages

        try:
            response = requests.get(url, timeout=10, verify=False, allow_redirects=True)  # Send a GET request to the URL and retrieve the response, timeout if it takes more than 10 seconds
            soup = BeautifulSoup(response.content, 'lxml')  # Creates a BeautifulSoup object which parses the HTML content and provides methods to navigate and search the HTML structure

            if depth not in count:
                # Creating dictionary within dictionary to store the corresponding values WITHIN EACH RECURSIVE DEPTH
                count[depth] = {}
                files[depth] = {}

            links = soup.find_all(["a", "img", "link", "script"])  # retrieve all the HTML tags that match the given tag names

            for link in links:
                href = link.get("href")  # Extracting the value of the href attribute from the current link
                src = link.get("src")  # Extracting the value of the src attribute from the current link


                
                # Handling the href attribute
                if href:
                    # getting the domain of the crawled URL
                    href = urljoin(url, href)
                    parsed_href = urlparse(href)
                    current_domain = parsed_href.netloc

                    file_type = extract_file_type(href)  # Extracting file type of the link

                    if file_type:
                        # Adding the required content corresponding to a particular recursive depth in the files and count dictionaries
                        if file_type not in files[depth]:
                            files[depth][file_type] = {"internal": [], "external": []}
                        if href not in files[depth][file_type]["internal"] and href not in files[depth][file_type]["external"]:
                            if current_domain == input_domain:
                                files[depth][file_type]["internal"].append(href)
                            else:
                                files[depth][file_type]["external"].append(href)
                            count[depth][file_type] = count[depth].get(file_type, 0) + 1
                    
                    else:
                        # if there is no proper file type for that link, then storing it under miscellaneous
                        file_type="MISCELLANEOUS"
                        if file_type not in files[depth]:
                            files[depth][file_type] = {"internal": [], "external": []}
                        if href not in files[depth][file_type]["internal"] and href not in files[depth][file_type]["external"]:
                            if current_domain == input_domain:
                                files[depth][file_type]["internal"].append(href)
                            else:
                                files[depth][file_type]["external"].append(href)
                            count[depth][file_type] = count[depth].get(file_type, 0) + 1

                    if current_domain == input_domain:
                        process_url(href, depth + 1)

                # Handling the src attribute
                if src:
                    # getting the domain of the crawled URL
                    src = urljoin(url, src)
                    parsed_src = urlparse(src)
                    current_domain = parsed_src.netloc

                    file_type = extract_file_type(src)  # Extracting file type of the link

                    if file_type:
                        # Adding the required content corresponding to a particular recursive depth in the files and count dictionaries
                        if file_type not in files[depth]:
                            files[depth][file_type] = {"internal": [], "external": []}
                        if src not in files[depth][file_type]["internal"] and src not in files[depth][file_type]["external"]:
                            if current_domain == input_domain:
                                files[depth][file_type]["internal"].append(src)
                            else:
                                files[depth][file_type]["external"].append(src)
                            count[depth][file_type] = count[depth].get(file_type, 0) + 1
                    
                    else:
                        # if there is no proper file type for that link, then storing it under miscellaneous
                        file_type="MISCELLANEOUS"
                        if file_type not in files[depth]:
                            files[depth][file_type] = {"internal": [], "external": []}
                        if src not in files[depth][file_type]["internal"] and src not in files[depth][file_type]["external"]:
                            if current_domain == input_domain:
                                files[depth][file_type]["internal"].append(src)
                            else:
                                files[depth][file_type]["external"].append(src)
                            count[depth][file_type] = count[depth].get(file_type, 0) + 1

                    if current_domain == input_domain:
                        process_url(src, depth + 1)

        # Handle Timeout error
        except requests.Timeout:
            print(f"Timeout occured while crawling: {url}")
            return
        
        # Handle SSL certificate verification error
        except requests.exceptions.SSLError as e:
            print("An error occurred:", str(e))
            return
        
            

    process_url(url, 1)

    # Printing to the terminal
    if output_file is None:
        for depth in range(1, max_depth + 1):
            if depth in count:
                print(f"At recursion level {depth}")
                print(f"Total files found: {sum(count[depth].values())}")

                # print(files[depth].values())


                for file_type, file_urls in files[depth].items():
                    print(f"{file_type.upper()}: {len(file_urls['internal'])} (internal)")
                    for file_url in file_urls['internal']:
                        clickable_link = f'{Fore.BLUE}{file_url}{Style.RESET_ALL}'
                        print(clickable_link)
                    print(f"{file_type.upper()}: {len(file_urls['external'])} (external)")
                    for file_url in file_urls['external']:
                        clickable_link = f'{Fore.BLUE}{file_url}{Style.RESET_ALL}'
                        print(clickable_link)
                print()

    # Writing to the output file
    else:
        with open(output_file, "a") as file:
            for depth in range(1, max_depth + 1):
                if depth in count:
                    file.write(f"At recursion level {depth}\n")
                    file.write(f"Total files found: {sum(count[depth].values())}\n")
                    for file_type, file_urls in files[depth].items():
                        file.write(f"{file_type.upper()}: {len(file_urls['internal'])} (internal)\n")
                        for file_url in file_urls['internal']:
                            clickable_link = f'{Fore.BLUE}{file_url}{Style.RESET_ALL}'
                            file.write(clickable_link + "\n")
                    file.write(f"{file_type.upper()}: {len(file_urls['external'])} (external)\n")
                    for file_url in file_urls['external']:
                        clickable_link = f'{Fore.BLUE}{file_url}{Style.RESET_ALL}'
                        file.write(clickable_link + "\n")
                file.write("\n")


def crawl_Handle(url, threshold, output_file):

    # Finding the domain of the url passed as command line argument
    parsed_url = urlparse(url)
    input_domain = parsed_url.netloc


    # This function extracts the file type of the link being analyzed
    def extract_file_type(link):
        parsed_url = urlparse(link)
        path = parsed_url.path
        file_type = None
        if "." in path.split("/")[-1]:
            file_type = path.split("/")[-1].split(".")[-1].lower()
        return file_type

    def process_url(url, depth):

        # Returning if url already visited or depth has exceeded the maximum threshold
        if url in visited or (threshold is not None and depth > threshold):
            global max_depth
            max_depth=max(depth,max_depth)
            return

        visited.add(url)  # Add the URL to the set of visited URLs to keep track of visited pages

        try:
            response = requests.get(url, timeout=10, verify=False, allow_redirects=True)  # Send a GET request to the URL and retrieve the response, timeout if it takes more than 10 seconds
            soup = BeautifulSoup(response.content, 'lxml')  # Creates a BeautifulSoup object which parses the HTML content and provides methods to navigate and search the HTML structure

            if depth not in count:
                # Creating dictionary within dictionary to store the corresponding values WITHIN EACH RECURSIVE DEPTH
                count[depth] = {}
                files[depth] = {}

            links = soup.find_all(["a", "img", "link", "script"])  # retrieve all the HTML tags that match the given tag names

            for link in links:
                href = link.get("href")  # Extracting the value of the href attribute from the current link
                src = link.get("src")  # Extracting the value of the src attribute from the current link


                try:
                    # Handling the href attribute
                    if href:
                        # getting the domain of the crawled URL
                        href = urljoin(url, href)
                        response = requests.get(href, timeout=10, verify=False, allow_redirects=True)
                        response.raise_for_status() # raises an exception if there is an error code received
                        parsed_href = urlparse(href)
                        current_domain = parsed_href.netloc

                        file_type = extract_file_type(href)  # Extracting file type of the link

                        if file_type:
                            # Adding the required content corresponding to a particular recursive depth in the files and count dictionaries
                            if file_type not in files[depth]:
                                files[depth][file_type] = {"internal": [], "external": []}
                            if href not in files[depth][file_type]["internal"] and href not in files[depth][file_type]["external"]:
                                if current_domain == input_domain:
                                    files[depth][file_type]["internal"].append(href)
                                else:
                                    files[depth][file_type]["external"].append(href)
                                count[depth][file_type] = count[depth].get(file_type, 0) + 1

                        else:
                            # if there is no proper file type for that link, then storing it under miscellaneous
                            file_type="MISCELLANEOUS"
                            if file_type not in files[depth]:
                                files[depth][file_type] = {"internal": [], "external": []}
                            if href not in files[depth][file_type]["internal"] and href not in files[depth][file_type]["external"]:
                                if current_domain == input_domain:
                                    files[depth][file_type]["internal"].append(href)
                                else:
                                    files[depth][file_type]["external"].append(href)
                                count[depth][file_type] = count[depth].get(file_type, 0) + 1


                        if current_domain == input_domain:
                            process_url(href, depth + 1)
                
                except requests.RequestException as e:
                    print(f"Error occurred while crawling: {href}")
                    print(f"Error message: {str(e)}")

                try:
                    # Handling the src attribute
                    if src:
                        # getting the domain of the crawled URL
                        src = urljoin(url, src)
                        response = requests.get(src, timeout=10, verify=False, allow_redirects=True)
                        response.raise_for_status() # raises an exception if there is an error code received
                        parsed_src = urlparse(src)
                        current_domain = parsed_src.netloc

                        file_type = extract_file_type(src)  # Extracting file type of the link

                        if file_type:
                            # Adding the required content corresponding to a particular recursive depth in the files and count dictionaries
                            if file_type not in files[depth]:
                                files[depth][file_type] = {"internal": [], "external": []}
                            if src not in files[depth][file_type]["internal"] and src not in files[depth][file_type]["external"]:
                                if current_domain == input_domain:
                                    files[depth][file_type]["internal"].append(src)
                                else:
                                    files[depth][file_type]["external"].append(src)
                                count[depth][file_type] = count[depth].get(file_type, 0) + 1

                        else:
                            # if there is no proper file type for that link, then storing it under miscellaneous
                            file_type="MISCELLANEOUS"
                            if file_type not in files[depth]:
                                files[depth][file_type] = {"internal": [], "external": []}
                            if src not in files[depth][file_type]["internal"] and src not in files[depth][file_type]["external"]:
                                if current_domain == input_domain:
                                    files[depth][file_type]["internal"].append(src)
                                else:
                                    files[depth][file_type]["external"].append(src)
                                count[depth][file_type] = count[depth].get(file_type, 0) + 1


                        if current_domain == input_domain:
                            process_url(src, depth + 1)

                except requests.RequestException as e:
                    print(f"Error occurred while crawling: {src}")
                    print(f"Error message: {str(e)}")

        # Handle timeout error
        except requests.Timeout:
            print(f"Timeout occured while crawling: {url}")
        
        # Handle SSL certificate verification error
        except requests.exceptions.SSLError as e:
            print("An error occurred:", str(e))
            return
            

    process_url(url, 1)

    # Printing to the terminal
    if output_file is None:
        for depth in range(1, max_depth + 1):
            if depth in count:
                print(f"At recursion level {depth}")
                print(f"Total files found: {sum(count[depth].values())}")


                for file_type, file_urls in files[depth].items():
                    print(f"{file_type.upper()}: {len(file_urls['internal'])} (internal)")
                    for file_url in file_urls['internal']:
                        clickable_link = f'{Fore.BLUE}{file_url}{Style.RESET_ALL}'
                        print(clickable_link)
                    print(f"{file_type.upper()}: {len(file_urls['external'])} (external)")
                    for file_url in file_urls['external']:
                        clickable_link = f'{Fore.BLUE}{file_url}{Style.RESET_ALL}'
                        print(clickable_link)
                print()

    # Writing to the output file
    else:
        with open(output_file, "a") as file:
            for depth in range(1, max_depth + 1):
                if depth in count:
                    file.write(f"At recursion level {depth}\n")
                    file.write(f"Total files found: {sum(count[depth].values())}\n")
                    for file_type, file_urls in files[depth].items():
                        file.write(f"{file_type.upper()}: {len(file_urls['internal'])} (internal)\n")
                        for file_url in file_urls['internal']:
                            clickable_link = f'{Fore.BLUE}{file_url}{Style.RESET_ALL}'
                            file.write(clickable_link + "\n")
                    file.write(f"{file_type.upper()}: {len(file_urls['external'])} (external)\n")
                    for file_url in file_urls['external']:
                        clickable_link = f'{Fore.BLUE}{file_url}{Style.RESET_ALL}'
                        file.write(clickable_link + "\n")
                file.write("\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Web Crawler")  # Creating an ArgumentParser object to handle command line arguments
    parser.add_argument("-u", "--url", help="URL to crawl", required=True)  # Adding argument for url
    parser.add_argument("-t", "--threshold", type=int, help="Recursion threshold")  # Adding argument for recursion threshold
    parser.add_argument("-o", "--output", help="Output file")  # Adding argument for output file
    parser.add_argument("-H", "--handle", action="store_true", help="Error handler") # Argument which if provided takes care of error handling

    args = parser.parse_args()

    # Storing the command line arguments in suitable variables
    url = args.url
    threshold = args.threshold
    output_file = args.output
    handle = args.handle if args.handle else None


    print()
    print()
    print()
    print()
    print("░██╗░░░░░░░██╗███████╗██████╗░░░░░░░░█████╗░██████╗░░█████╗░░██╗░░░░░░░██╗██╗░░░░░███████╗██████╗░")
    print("░██║░░██╗░░██║██╔════╝██╔══██╗░░░░░░██╔══██╗██╔══██╗██╔══██╗░██║░░██╗░░██║██║░░░░░██╔════╝██╔══██╗")
    print("░╚██╗████╗██╔╝█████╗░░██████╦╝█████╗██║░░╚═╝██████╔╝███████║░╚██╗████╗██╔╝██║░░░░░█████╗░░██████╔╝")
    print("░░████╔═████║░██╔══╝░░██╔══██╗╚════╝██║░░██╗██╔══██╗██╔══██║░░████╔═████║░██║░░░░░██╔══╝░░██╔══██╗")
    print("░░╚██╔╝░╚██╔╝░███████╗██████╦╝░░░░░░╚█████╔╝██║░░██║██║░░██║░░╚██╔╝░╚██╔╝░███████╗███████╗██║░░██║")
    print("░░░╚═╝░░░╚═╝░░╚══════╝╚═════╝░░░░░░░░╚════╝░╚═╝░░╚═╝╚═╝░░╚═╝░░░╚═╝░░░╚═╝░░╚══════╝╚══════╝╚═╝░░╚═╝")
    print()
    print()
    print()
    print()
    
    # Prompting an error message for an invalid threshold value
    if threshold is not None:
        if threshold <= 0:
            print("Invalid threshold. Threshold must be greater than 0.")
            exit(1)
    if handle is None:
        # calling function crawl_noHandle()
        if output_file:
            crawl_noHandle(url, threshold, output_file)
            print(f"Written data to {output_file}")
        else:
            crawl_noHandle(url, threshold, None)
    else:
        #calling function crawl_handle()
        if output_file:
            crawl_Handle(url, threshold, output_file)
            print(f"Written data to {output_file}")
        else:
            crawl_Handle(url, threshold, None)



'''
Customizations made to the code:
    1. Colorized the links when printing it to the terminal or writing it to the file.
    2. Segregated the files into internal and external.
    3. Added timeout handling to avoid waiting for the server_response indefinitely.
    4. Added argument for handling of error codes from the server. For example: 404 Error Not Found. The error message is printed if there is an error.
'''
