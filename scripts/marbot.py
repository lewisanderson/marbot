# Copyright Lewis Anderson 2023

import requests
import bs4
from bs4 import BeautifulSoup
from itertools import islice


def main():
    # loadUrls()

    humanText = processHtmlFile("/app/testdata/0.html")
    maxCharsPerBatch = 4000
    batches = list(batched(humanText, maxCharsPerBatch))
    print(f"Split into {len(batches)} batches of max {maxCharsPerBatch} chars")
    for index, batch in enumerate(batches):
        summary = summarize(batch)
        print(f"Summary {index}: {summary}")




def loadUrls():
    urls = [
        "https://www.deskera.com/blog/plastic-manufacturing-key-trends-and-innovations/amp/",
        "https://www.fortunebusinessinsights.com/amp/plastics-market-102176",
        "https://www.kaysun.com/blog/plastics-industry-trends",
        "https://www.manufacturing.net/operations/article/13057614/the-future-of-plastics-manufacturing-in-the-us"
    ]
    for index, url in enumerate(urls):
        outputPath = f"/app/testdata/{index}.html"
        fetchHtmlForPage(url, outputPath)


def fetchHtmlForPage(url, outputPath):
    print(f"Fetching {url}")
    response = requests.get(url)
    with open(outputPath, 'w') as outputFile:
        outputFile.write(response.text)
    
    print(f"Saved {len(response.text)} chars to {outputPath}")


def processHtmlFile(inputPath):
    with open(inputPath, 'r') as inputFile:
        html = inputFile.read()
    print(f"Read {len(html)} chars from {inputPath}")
    
    soup = BeautifulSoup(html, 'html.parser')
    humanReadableText = ""
    for element in soup.descendants:
        if (isinstance(element, (bs4.NavigableString)) and 
            element.string and 
            element.string.strip() and
            element.parent.name not in ['script', 'style']):
            humanReadableText += f"<{element.parent.name}> {element.string.strip()} </{element.parent.name}>\n"
    
    # print(humanReadableText)
    print(f"Read {len(humanReadableText)} chars of human readable text")
    return humanReadableText


def batched(iterable, n):
    """
    Batch data into tuples of length n. The last batch may be shorter.
    from https://docs.python.org/3/library/itertools.html#itertools-recipes
    """
    # batched('ABCDEFG', 3) --> ABC DEF G
    if n < 1:
        raise ValueError('n must be at least one')
    it = iter(iterable)
    while (batch := tuple(islice(it, n))):
        yield batch


def summarize(text):
    # TODO: use

if __name__ == '__main__':
    main()
