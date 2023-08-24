# Copyright Lewis Anderson 2023
import concurrent.futures
import openai
import os
import requests
import bs4
from bs4 import BeautifulSoup
from itertools import islice


def main():
    openai.organization = "org-RfxFQjm7zizJjdQRALbJZaZB"
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    modelToUse = "gpt-3.5-turbo"
    # modelToUse = "gpt-4"
    # loadUrls()

    filePaths = [
        "/app/testdata/0.html",
        "/app/testdata/1.html",
        "/app/testdata/2.html",
        "/app/testdata/3.html"
    ]
    pageSummaries = []
    for filePath in filePaths:
        pageSummary = loadAndSummarizePage(filePath, modelToUse)
        pageSummaries.append(pageSummary)
    
    combinePageSummaries(pageSummaries, modelToUse)


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


def loadAndSummarizePage(filePath, modelToUse):
    print(f"Loading {filePath}")
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
    if len(batches) > 10:
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


def combinePageSummaries(pageSummaries, modelToUse):
    instructionText = f"""
        Please summarize the following text. You are helping with market research, to help the user better understand the current state and future trends of a particular industry. 

        The input text is a set of summaries of different articles describing the same industry. 
        
        You should combine these individual article summaries into a list of 4-10 bullet points, which describe major trends, key challenges, and upcoming opportunities in the industry. Please do your best to be complete and capture all the major trends/challenges/opportunities. But, if you have already mentioned a trend in a bullet point, you dont need to mention it again.

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
    print(f"\n\nCombined page summaries:\n{combinedSummary}")
    return combinedSummary


if __name__ == '__main__':
    main()
