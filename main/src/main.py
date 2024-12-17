from requests import get
from os import getenv, path
from pathlib import Path
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import pickle as pkl
from alive_progress import alive_bar
import sys

load_dotenv(dotenv_path=Path("data.env"))
BASE_URL = getenv("BASE_URL")
DATA_PATH = Path(getenv("DATA_PATH"))
sys.setrecursionlimit(10000)

#class object container for the individual quotes
class Quote:

    def __init__(self, text: str =None, author: str =None, tags: list[str] =None):
        self.text = text
        self.author = author
        self.tags = tags


def get_and_parse_content(url: str):
    """
    Gets the HTML of the page and parses it using BeautifulSoup.

    Args:
        url (str): The URL of the page to process.

    Returns:
        parsed (BeautifulSoup): The parsed content of the HTML code of the page.
    """
    content = get(url).content
    
    parsed = BeautifulSoup(content, "html5lib")

    return parsed


def get_quotes(parsed: BeautifulSoup):
    """
    Gets the quotes and relevant details from the parsed BeautifulSoup object and parses them into Quote objects.

    Args:
        parsed (BeautifulSoup): The parsed content in BeautifulSoup format.

    Returns:
        result (List[Quote]): The list of the Quote objects.
    """
    result = []

    #find the div elements with class = "quote" -> div elements for the quotes

    quotes = parsed.find_all(name="div", attrs={"class":"quote"})

    i: BeautifulSoup = None
    for i in quotes:
        
        #find the span element with class = "text" and get the text -> text of the quote
        text = i.find(name="span", attrs={"class": "text"}, recursive=False).text.replace("”", "").replace("“", "")

        #find the small element recursively with class = "author" and get the content -> name of the author of the quote
        author = i.find(name="small", attrs={"class": "author"}).contents

        #find the meta element recursively with class = "keywords" and get the content attr. and split it on comma -> tags of the quote
        tags = i.find(name="meta", attrs={"class": "keywords"})["content"].split(",")

        temp = Quote(text=text, author=author, tags=tags)

        result.append(temp)

    
    return result


def check_if_page_invalid(parsed: BeautifulSoup):
    """
    Check if a page is invalid (there are no quotes on the page to scrape).

    Args:
        parsed (BeautifulSoup): The parsed HTML content of the page

    Returns:
        (bool): True if page is invalid (does not contain any quotes), False otherwise.
    """
    elements = parsed.find_all()

    content = [i.text.strip() for i in elements]

    if any(["No quotes found!" in i for i in content]):
        return True
    
    return False

def scrape_page(url: str):

    """
    Scrapes the page and returns accordingly.

    Returns:
        (bool | list[Quote]): Returns false if the page given by the url is invalid, the list of Quote objects giving the quotes on the page, otherwise.
    """
    #parse the page
    data = get_and_parse_content(url)

    #check if page is invalid
    is_invalid = check_if_page_invalid(data)

    if is_invalid:
        return False
    
    else:
        return get_quotes(data)
    
def save_load_data(data_path: Path, data: list[Quote] = None):

    """
    Saves/Loads the data to/from the pkl file at data_path.

    Returns:
        (None | list[Quote]): The data that is loaded, None otherwise.
    """
    if path.isfile(data_path):
        return [Quote(text=i[0], author= i[1], tags = i[2]) for i in pkl.load(open(data_path, "rb"))]

    else:
        if data != None:

            out = [(i.text, i.author, i.tags) for i in data]
            pkl.dump(out, open(data_path, "wb"))

def main():

    """
    Main loop of the program, displays the quotes scraped from the website <BASE_URL>. Saves the quotes as a list of Quote objects in <DATA_PATH>.
    """

    data = save_load_data(DATA_PATH)

    if data != None:

        i: Quote = None

        for i in data:
            print("%s\n by: %s\n tags: %s" % (i.text, i.author, str(i.tags)))

    else:

        result, i, state = [], 1, True
        
        with alive_bar() as bar:

            while state:
                
                current_url = BASE_URL + "page/%d" % i

                output = scrape_page(current_url)

                if not output:

                    state = False
                
                else:

                    result.extend(output)
                
                i += 1
                bar()

        save_load_data(DATA_PATH, result)

        main()

main()


