# Copyright Lewis Anderson 2023
import concurrent.futures
import googleapiclient.discovery
import openai
import os
import requests
import bs4
import traceback
from bs4 import BeautifulSoup
from itertools import islice
from joblib import Memory
from googleapiclient.errors import HttpError



memory = Memory("/app/cachedata", verbose=0)

def main():
    openai.organization = "org-RfxFQjm7zizJjdQRALbJZaZB"
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    modelToUse = "gpt-3.5-turbo"
    # modelToUse = "gpt-4"
    googleAPIKey = os.environ.get("GOOGLE_API_KEY")
    googleCseId = "368102dbb37ea4659"

    allLinks = findLinksForAllIndustries(googleAPIKey, googleCseId, modelToUse)

    loadUrls(allLinks)

    filePaths = scanFiles("/app/testdata")

    industryPageSummaries = {}
    industrySummaries = {}
    for industry in filePaths:
        thisIndustryFilePaths = filePaths[industry]
        pageSummaries = []
        for filePath in thisIndustryFilePaths:
            pageSummary = loadAndSummarizePage(filePath, modelToUse)
            pageSummaries.append(pageSummary)
        industryPageSummaries[industry] = pageSummaries
    
        combinedSummary = combinePageSummaries(pageSummaries, "gpt-4")
        industrySummaries[industry] = combinedSummary


def findLinksForAllIndustries(googleAPIKey, googleCseId, modelToUse):
    industries = [
        "Aircraft",
        "Appliance",
        "Bakery bread",
        "Chemical",
        "Dairy",
        "Electrical",
        "Equipment",
        "Food",
        "Motor vehicle parts",
        "Paper",
        "Plastic",
        "Printing",
        "Professional equipment",
        "Rubber",
        "Snacks",
    ]
    allLinks = {}
    for industry in industries:
        links = marbot.findLinksForIndustry(industry, googleAPIKey, googleCseId)
        industryKey = industry.replace(" ", "_")
        allLinks[industryKey] = links
    return allLinks


def findLinksForIndustry(industry, googleAPIKey, googleCseId):
    partialSearchTerms = [
        " manufacturing us challenges",
        " manufacturing us trends",
        " manufacturing us industry overview",
    ]
    allLinks = []
    for partialSearch in partialSearchTerms:
        search = industry + partialSearch
        theseLinks = googleSearch(search, googleAPIKey, googleCseId)
        print(f"Got {len(theseLinks)} links for {search}: {theseLinks}")
        allLinks.extend(theseLinks)
    allLinks = list(set(allLinks))
    return allLinks


@memory.cache
def googleSearch(searchTerm, apiKey, cseId, **kwargs):
    service = googleapiclient.discovery.build("customsearch", "v1", developerKey=apiKey)
    cse = service.cse()
    try:
        result = cse.list(q=searchTerm, cx=cseId, **kwargs).execute()
    except HttpError as error:
        print("An error occurred:", error.resp.status)
        print(error.resp.reason)
        print(error._get_reason())
        return []
    return [item["link"] for item in result["items"]]


def loadUrls(fullUrls):
    numSucceeded = 0
    failedUrls = []
    for industry in fullUrls:
        for index, url in enumerate(fullUrls[industry]):
            outputPath = f"/app/testdata/{industry}-{index}.html"
            didSucceed = fetchHtmlForPage(url, outputPath)
            if didSucceed:
                numSucceeded += 1
            else:
                failedUrls.append(url)
    print(f"Successfully fetched {numSucceeded} pages.")
    if len(failedUrls) > 0:
        print(f"WARNING: Failed to fetch {len(failedUrls)} pages: {failedUrls}")


@memory.cache
def fetchHtmlForPage(url, outputPath):
    print(f"Fetching {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
    except:
        print(f"ERROR: Failed to fetch {url}")
        return False

    with open(outputPath, "w") as outputFile:
        outputFile.write(response.text)
    
    print(f"Saved {len(response.text)} chars to {outputPath}")
    return True


def scanFiles(inputDirectory):
    filePaths = {}

    for filename in os.listdir(inputDirectory):
        if filename.endswith(".html"):
            baseName = filename.rsplit('-', 1)[0]
            filePaths.setdefault(baseName, []).append(os.path.join(inputDirectory, filename))
    return filePaths


@memory.cache
def loadAndSummarizePage(filePath, modelToUse):
    print(f"Loading {filePath} (v2)")
    humanText = preprocessHtmlFile(filePath)
    maxCharsPerBatch = 4000
    batches = ["".join(x) for x in batched(humanText, maxCharsPerBatch)]
    print(f"Split into {len(batches)} batches of max {maxCharsPerBatch} chars")
    summaries = computeSummariesForBatchesInParallel(batches, modelToUse)
    pageSummary = summarizePage(summaries, modelToUse)
    print(f"\n\nPage summary for {filePath}: \n{pageSummary}")
    return pageSummary


def preprocessHtmlFile(inputPath):
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


def computeSummariesForBatchesInParallel(batches, modelToUse):
    if len(batches) > 100:
        print(f"ERROR: Too many batches ({len(batches)}). If this is expected, feel free to remove this code. Exiting.")
        raise Exception("Too many batches")
    summaries = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for index, batch in enumerate(batches):
            print(f"Submitting batch {index}")
            futures.append(executor.submit(summarizeRawInput, batch, modelToUse))
        for future in concurrent.futures.as_completed(futures):
            chunkSummary = future.result()
            summaries.append(chunkSummary)
            print(f"Summary {len(summaries)-1}: {chunkSummary}\n")

    return summaries


# def computeSummariesForBatches(batches, modelToUse):
#     summaries = []
#     for index, batch in enumerate(batches):
#         chunkSummary = summarizeRawInput(batch, modelToUse)
#         summaries.append(chunkSummary)
#         # print(f"Input:{batch}\n\nSummary {index}: {chunkSummary}")
#         print(f"Summary {index}: {chunkSummary}")
#     return summaries


def summarizeRawInput(inputText, modelToUse):
    instructionText = f"""
        Please summarize the following text. You should produce a paragraph summarizing it, and then a set of 1-5 bullet points describing major themes in the text.

        The input text is lightly formatted html. You should ignore the formatting and just summarize the text. There may be advertisements, navigation headers, and other unrelated text in the input. You should ignore these and just summarize the main text.

        We are especially interested in major trends in the industry being described.

        Input text:
        """
    instructionText += inputText

    result = openai.ChatCompletion.create(
        model=modelToUse,
        messages=[
            {"role": "user", "content": instructionText}
        ]
    )
    summary = result["choices"][0]["message"]["content"]
    # print(summary)
    return summary


def summarizePage(summaries, modelToUse):
    instructionText = f"""
        Please summarize the following text. You are helping with market research, to help the user better understand the current state and future trends of a particular industry. 

        The input text is a set of summaries of different sections of the same document. You should combine these summaries into a single summary of the document. You should produce a paragraph summarizing the input text, and then a single set of 4-10 bullet points describing major trends, key challenges, and upcoming opportunities in the industry.

        Please do your best to be complete and capture all the major trends/challenges/opportunities, but dont repeat yourself. If you have already mentioned a trend in a bullet point, you dont need to mention it again.

        Input text:
        """
    instructionText += "\n\n".join(summaries)

    result = openai.ChatCompletion.create(
        model=modelToUse,
        messages=[
            {"role": "user", "content": instructionText}
        ]
    )
    summary = result["choices"][0]["message"]["content"]
    # print(summary)
    return summary


@memory.cache
def combinePageSummaries(pageSummaries, modelToUse):
    print("LEWIS DEBUG v3")
    instructionText = f"""
        Please summarize the following text. You are helping with market research, to help the user better understand the current state and future trends of a particular industry. 

        The input text is a set of summaries of different articles describing the same industry. 
        
        You should combine these individual article summaries into a list of 4-10 bullet points, which describe major trends, key challenges, and upcoming opportunities in the industry. Please do your best to be complete and capture all the major trends/challenges/opportunities. But, if you have already mentioned a trend in a bullet point, you dont need to mention it again.

        Each bullet point should start with a key phrase of 1-3 words (in quotes), and a number which says how many page summaries that concept was mentioned in. The bullet point should then have a short description of it. For example, "plastic recycling" (3): Plastic recycling is a major trend in the industry. Companies are increasingly looking for ways to recycle plastic, and to use recycled plastic in their products."

        The bullet points should be sorted by the number of page summaries that mention the concept, from most to least.

        Make sure to include information from all pages, so that you produce a summary which is representative of the industry as a whole.

        Input text:
        """
    for index, pageSummary in enumerate(pageSummaries):
        instructionText += f"\n\nArticle {index} summary:\n{pageSummary}"

    result = openai.ChatCompletion.create(
        model=modelToUse,
        messages=[
            {"role": "user", "content": instructionText}
        ]
    )
    combinedSummary = result["choices"][0]["message"]["content"]
    # print(f"\n\nCombined page summaries:\n{combinedSummary}")
    return combinedSummary


def combineIndustrySummaries(subindustrySummaries, modelToUse):
    instructionText = f"""
        Please summarize the following text. You are helping with market research, to help the user better understand the current state and future trends of a particular industry. 

        The input text is a set of summaries of different subindustries within the same industry. 
        
        You should combine these individual summaries into a list of 10-20 bullet points, which describe major trends, key challenges, and upcoming opportunities in the industry. Please do your best to be complete and capture all the major trends/challenges/opportunities. But, if you have already mentioned a trend in a bullet point, you dont need to mention it again.

        Each bullet point should start with a key phrase of 1-3 words (in quotes), and a number which says how many subindustry summaries contained that concept. The bullet point should then have a short description of it. For example, "plastic recycling" (3): Plastic recycling is a major trend in the industry. Companies are increasingly looking for ways to recycle plastic, and to use recycled plastic in their products."

        The bullet points should be sorted by the number of subindustry summaries that mention the concept, from most to least.

        Make sure to include information from all subindustries, so that you produce a summary which is representative of the industry as a whole.

        Input text:
        """
    for index, subindustrySummary in enumerate(subindustrySummaries):
        instructionText += f"\n\nArticle {index} summary:\n{subindustrySummary}"

    result = openai.ChatCompletion.create(
        model=modelToUse,
        messages=[
            {"role": "user", "content": instructionText}
        ]
    )
    combinedSummary = result["choices"][0]["message"]["content"]
    # print(f"\n\nCombined page summaries:\n{combinedSummary}")
    return combinedSummary


if __name__ == '__main__':
    main()
