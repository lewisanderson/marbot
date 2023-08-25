# Copyright Lewis Anderson 2023
import concurrent.futures
import openai
import os
import requests
import bs4
import traceback
from bs4 import BeautifulSoup
from itertools import islice


def main():
    openai.organization = "org-RfxFQjm7zizJjdQRALbJZaZB"
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    modelToUse = "gpt-3.5-turbo"
    # modelToUse = "gpt-4"
    # loadUrls()

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


def loadUrls():
    fullUrls = {
        "Equipment": [
            "https://www.oemoffhighway.com/trends/document/22578646/2022-state-of-the-industry-oem-offhighway",
            "https://www.oemoffhighway.com/trends/article/22552113/oem-offhighway-state-of-the-industry-2022",
            ],
        "Plastic": [
            "https://www.deskera.com/blog/plastic-manufacturing-key-trends-and-innovations/amp/",
            "https://www.deskera.com/blog/plastic-manufacturing-critical-issues-and-challenges/amp/",
            "https://www.fortunebusinessinsights.com/amp/plastics-market-102176",
            "https://www.kaysun.com/blog/plastics-industry-trends",
            "https://www.manufacturing.net/operations/article/13057614/the-future-of-plastics-manufacturing-in-the-us",
            "https://www.syscon-intl.com/plantstar/blog/challenges-facing-plastics-manufacturing?hs_amp=true",
            "https://www.conairgroup.com/resources/resource/top-5-challenges-in-plastics-processing/",
            "https://www.cadimensions.com/the-plastics-industrys-biggest-challenges-in-2022/",
            ],
        "Bakerybread": [
            "https://www.snackandbakery.com/articles/98916-state-of-the-industry-2022-bakery-faces-formidable-challenges",
            "https://www.bakeryandsnacks.com/Article/2021/06/30/The-key-bread-trends-for-2021-and-beyond",
            "https://www.ibisworld.com/united-states/market-research-reports/bread-production-industry/",
            "https://www.mordorintelligence.com/industry-reports/bread-market",
            "https://www.techsciresearch.com/report/united-states-bread-market/12868.html",
            "https://www.globenewswire.com/en/news-release/2023/04/19/2649704/0/en/Latest-Report-Global-Bread-Market-Size-Share-Worth-USD-291-29-Billion-by-2030-at-a-3-66-CAGR-Custom-Market-Insights-Analysis-Outlook-Leaders-Report-Trends-Forecast-Segmentation-Gro.html",
            "https://www.futuremarketinsights.com/reports/packaged-bread-market",
            "https://amfbakery.com/artisan-style-bread-trends-in-2022/",
            "https://www.aptean.com/en-US/insights/blog/challenges-in-the-bakery-industry",
            "https://www.foodware365.com/en/industry-challenges/bread-and-bakery-challenges/",
            "https://americanbakers.org/news/bakery-supply-chain-challenges-infographic",
            ],
        "Snacks": [
            "https://www.ibisworld.com/united-states/market-research-reports/snack-food-production-industry/",
            "https://www.grandviewresearch.com/industry-analysis/snacks-market",
            "https://www.anythingresearch.com/industry/Snack-Food-Manufacturing.htm",
            "https://www.bakingbusiness.com/articles/57274-economist-assesses-challenges-facing-a-strong-snack-industry",
            "https://foodindustryexecutive.com/2022/12/the-future-manufacturing-workforce-how-one-of-the-worlds-largest-snack-food-companies-is-tackling-todays-labor-challenges/",
            "https://www.harvestfoodsolutions.com/top-challenges-food-manufacturers-can-expect-to-face-in-2022/",
            "https://www.profoodworld.com/home/article/13278601/seven-cpg-challenges-for-the-snack-food-industry",
            "https://www.deskera.com/blog/foods-manufacturing-critical-issues-and-challenges/",
            "https://www.powderbulksolids.com/food-beverage/3-major-issues-food-manufacturers-will-face-2022",
            ],
        "Aircraft": [
            "https://www.polarismarketresearch.com/industry-analysis/aircraft-manufacturing-market",
            "https://www.businesswire.com/news/home/20220427005797/en/Global-Aircraft-Manufacturing-Market-2022-to-2030---Share-Size-Trends-and-Industry-Analysis-Report---ResearchAndMarkets.com",
            "https://www.alliedmarketresearch.com/aircraft-manufacturing-market-A53658",
            "https://www.statista.com/markets/407/topic/939/aerospace-defense-manufacturing/#overview",
            "https://straitsresearch.com/report/north-america-aerospace-parts-manufacturing-market",
            "https://kingsburyuk.com/aerospace-manufacturing-challenges-in-the-early-years/",
            "https://www.js3global.com/blog/8-challenges-facing-the-aerospace-industry/",
            "https://www.mckinsey.com/industries/aerospace-and-defense/our-insights/taking-off-scaling-complex-manufacturing-in-the-aerospace-industry",
            "https://www.mckinsey.com/industries/aerospace-and-defense/our-insights/taking-off-scaling-complex-manufacturing-in-the-aerospace-industry",
            "https://engmag.in/how-to-overcome-aerospace-manufacturing-challenges/",
            "https://www.aviationpros.com/engines-components/article/53060096/magnetic-mro-us-aviation-supply-chain-challenges-parts-shortages-rising-costs-labor-resource-crunches",
            "https://www.aviationpros.com/engines-components/article/53060096/magnetic-mro-us-aviation-supply-chain-challenges-parts-shortages-rising-costs-labor-resource-crunches",
            ],
        "Appliance": [
            "https://www.ibisworld.com/united-states/market-research-reports/major-household-appliance-manufacturing-industry/#:~:text=Major%20Household%20Appliance%20Manufacturing%20in%20the%20US%20industry%20trends%20(2018,climb%20to%208.5%25%20in%202023",
            "https://www.grandviewresearch.com/industry-analysis/us-household-appliances-market",
            "https://www.marketresearch.com/Kentley-Insights-v4035/Major-Appliance-Manufacturing-Research-Updated-32768351/",
            "https://www.mordorintelligence.com/industry-reports/north-america-home-appliances-market-industry",
            "https://blog.salsita-3d-configurator.com/the-next-five-years-in-the-appliances-and-electronics-manufacturing-industry/",
            "https://www.servicepower.com/blog/top-5-manufacturing-challenges",
            "https://mideaph.com/an-in-depth-look-into-the-appliance-manufacturing-industry-trends-challenges-and-opportunities/",
            ],
        "Paper": [
            "https://www.deskera.com/blog/paper-manufacturing-critical-issues-and-challenges/",
            "https://scitechconnect.elsevier.com/challenges-and-opportunities-for-the-pulp-and-paper/",
            "https://www.hammondpaper.com/blog/post/challenges-and-opportunities-for-the-paper-and-pulp-industry",
            "https://www.piworld.com/article/addressing-the-challenges-in-the-paper-supply-chain/",
            "https://www.youris.com/energy/renewables/refusing-to-fold-can-paper-manufacturers-face-down-energy-challenges-.kl",
            "https://creative-solution.com/global-paper-shortage-challenges-to-hit-direct-marketers-in-2022/",
            "https://linchpinseo.com/trends-pulp-and-paper-industry/",
            "https://www.fortunebusinessinsights.com/north-america-pulp-and-paper-market-106617",
            "https://www.mckinsey.com/industries/paper-forest-products-and-packaging/our-insights/pulp-paper-and-packaging-in-the-next-decade-transformational-change",
            "https://www.tstar.com/blog/3-key-trends-in-the-pulp-and-paper-industry",
            ],
        "Dairy": [
            "https://www.dornerconveyors.com/blog/challenges-facing-the-dairy-industry",
            "https://www.dairyherd.com/news/business/dairy-supply-chain-continues-face-challenges",
            "https://www.dairyfoods.com/articles/95973-dairy-executives-tackle-todays-hot-button-issues",
            "https://www.mckinsey.com/industries/agriculture/our-insights/how-dairy-executives-are-navigating-recovery-in-2022",
            "https://spectrumnews1.com/oh/columbus/news/2021/10/07/ag-report--the-state-of-dairy",
            "https://www.feedstrategy.com/animal-feed-manufacturing/article/15442933/2022-dairy-outlook-challenges-abound-for-dairy-producers",
            "https://spectrumlocalnews.com/nys/central-ny/news/2022/09/01/dairy-farmers-face-challenges-of-inflation--supply-chain--and-weather-in-addition-to-representation-of-the-industry",
            "https://www.foodware365.com/en/industry-challenges/dairy-challenges/",
            ],
        "Chemical": [
            "https://www.americanchemistry.com/chemistry-in-america/news-trends/press-release/2023/new-report-finds-major-supply-chain-problems-continue-to-impact-chemical-manufacturing",
            "https://scanco.com/6-operational-challenges-in-the-chemical-industry-how-you-can-solve-them/",
            "https://www.supplychainbrain.com/articles/37029-supply-chain-issues-continue-to-hurt-the-us-chemical-manufacturing-sector",
            "https://www.orbichem.com/blog/predictions-challenges-for-the-chemical-industry-in-2023",
            "https://www.parkoursc.com/the-top-5-supply-chain-challenges-of-chemical-manufacturers/",
            "https://www.nesfircroft.com/resources/blog/challenges-shaping-the-chemicals-industry-in-2023/",
            "https://www.innovapptive.com/blog/5-challenges-facing-chemical-companies-in-2022-can-mobile-workforce-management-offer-a-solution",
            "https://www2.deloitte.com/us/en/pages/energy-and-resources/articles/chemical-industry-outlook.html",
            ],
        "Professionalequipment": [
            "https://www.newstreaming.com/5-biggest-challenges-for-original-equipment-manufacturers-in-2021/",
            "https://www.rdoequipment.com/resources/blogs/3-unexpected-challenges-the-equipment-industry-is-facing-in-2021-and-what-to-do-now",
            "https://www.designnews.com/automation/ongoing-manufacturing-challenges-uptime-materials-and-workers",
            "https://www2.deloitte.com/us/en/pages/energy-and-resources/articles/manufacturing-industry-outlook.html",
            "https://www2.deloitte.com/content/dam/Deloitte/us/Documents/energy-resources/us-2023-outlook-manufacturing.pdf",
            "https://www.servicepower.com/blog/top-5-manufacturing-challenges",
            "https://www.aem.org/news/5-equipment-manufacturing-trends-to-watch-in-2022",
            "https://www.dynaway.com/blog/5-current-challenges-to-overcome-for-the-manufacturing-industry",
            "https://www.automate.org/industry-insights/manufacturing-challenges-and-solutions-series-labor-shortage",
            "https://blog.thomasnet.com/top-manufacturing-challenges",
            "https://www.industryselect.com/blog/key-facts-on-the-us-industrial-machinery-sector",
            "https://www.weidert.com/blog/key-manufacturing-challenges",
            "https://www.ibaset.com/six-common-challenges-for-industrial-manufacturers/",
            "https://www.aem.org/news/5-equipment-manufacturing-trends-to-watch-in-2023",
            "https://global.hitachi-solutions.com/blog/top-manufacturing-trends/",
            ],
        "Food": [
            "https://www.fmi.org/blog/view/fmi-blog/2023/02/28/six-imperative-issues-facing-the-food-industry-in-2023",
            "https://www.oliverwyman.com/our-expertise/journals/boardroom.html?utm_source=fmi&utm_medium=website&utm_campaign=boardroom-8&utm_content=24-jan-2023",
            "https://www.deskera.com/blog/foods-manufacturing-critical-issues-and-challenges/",
            "https://www.harvestfoodsolutions.com/top-challenges-food-manufacturers-can-expect-to-face-in-2022/",
            "https://www.foodengineeringmag.com/articles/100394-the-state-of-food-manufacturing-in-2022",
            "https://www.areadevelopment.com/foodprocessing/q4-2022/three-big-challenges-facing-the-food-beverage-industry.shtml",
            "https://www.foodprocessing.com/power-lunch/article/11288962/food-industry-still-has-post-pandemic-challenges-to-face",
            "https://savoreat.com/what-are-the-problems-in-the-food-industry-how-to-overcome-them/",
            "https://www.just-food.com/comment/five-hot-topics-as-us-food-industry-enters-2023/",
            "https://www.gminsights.com/blogs/challenges-in-food-and-beverage-industry",
            "https://www.columbusglobal.com/en-gb/blog/food-industry-trends-for-2023",
            "https://www.crbgroup.com/insights/food-beverage/food-beverage-manufacturing-trends",
            "https://www.nist.gov/blogs/manufacturing-innovation-blog/five-trends-will-impact-food-industry-many-years",
            "https://www.foodmanufacturing.com/consumer-trends/blog/22081182/the-top-food-industry-trends-to-expect-in-2022",
            "https://industrytoday.com/top-2023-food-and-beverage-manufacturing-trends/",
            ],
        "Electrical": [
            "https://katanamrp.com/blog/electronics-manufacturing-process/",
            "https://www.eptac.com/blog/the-biggest-challenges-currently-facing-the-electronics-manufacturing-industry",
            "https://www.optiproerp.com/blog/7-challenges-erp-helps-electronics-manufacturers-overcome/",
            "https://www.macrofab.com/blog/supply-chain-challenges-electronics-companies/",
            "https://blog.lnsresearch.com/bid/146822/Top-6-Challenges-in-Electronics-Manufacturing",
            "https://www.evolute.in/challenges-in-electronics-manufacturing/",
            "https://blog.epectec.com/supply-chain-challenges-on-the-electronics-and-manufacturing-industry",
            "https://www.meanseng.com/top-5-challenges-faced-by-electronics-manufacturers/",
            "https://www.myelectric.coop/supply-chain-challenges-continue/",
            "https://www.smckyems.com/issues-and-challenges-in-the-ems-industry/",
            "https://www.statista.com/outlook/io/manufacturing/consumer-goods/electrical-equipment/united-states#methodology",
            "https://www.industryselect.com/blog/key-facts-on-us-electronics-manufacturing",
            ],
        "Rubber": [
            "https://www.applerubber.com/hot-topics-for-engineers/supply-chain-issues-in-the-rubber-sealing-industry/#:~:text=The%20rubber%20industry%20has%20also,quality%20rubber%20seals%20and%20gaskets.",
            "https://www.applerubber.com/hot-topics-for-engineers/what-to-expect-in-the-rubber-industry-for-2022/",
            "https://e2btek.com/top-5-challenges-rubber-plastics-manufacturers-solved/",
            "https://www.ace-laboratories.com/trends-in-rubber-industry/",
            "https://thedailycpa.com/challenges-and-solutions-for-rubber-injection-molding/",
            "https://www.rubbernews.com/news/rubber-industry-takes-labor-shortage-better-wages-benefits",
            "https://rubber-group.com/2022/06/manufacturing-resilience/",
            "https://www.universalpolymer.com/blog/pros-and-cons-of-reshoring-manufacturing/",
            "https://www.fortunebusinessinsights.com/industry-reports/rubber-market-101612",
            ],
        "Printing": [
            "https://www.phase3mc.com/thinking/supply-chain-challenges-in-the-print-industry?hs_amp=true",
            "https://www.conquestgraphics.com/blog/conquest-graphics/2021/09/28/supply-chain-challenges-affecting-the-print-industry",
            "https://keypointintelligence.com/keypoint-blogs/how-printer-manufacturers-can-weather-supply-chain-challenges?hs_amp=true",
            "https://www.piworld.com/article/inaugural-live-local-event-reveals-printing-industry-challenges-opportunities/",
            "https://www.ibisworld.com/united-states/market-research-reports/printing-industry/",
            "https://cmsmart.net/community/printing-industry-trends",
            "https://www.tonerbuzz.com/blog/printing-industry-trends/",
            "https://www.zakeke.com/blog/top-10-printing-industry-trends/amp/",
            "https://www.whymeridian.com/blog/top-production-print-trends?hs_amp=true",
            ],
        "Motorvehicleparts": [
            "https://abas-erp.com/en/resources/erp-blog/how-are-mid-size-auto-parts-manufacturers-addressing-todays-biggest-challenges",
            "https://gmb.net/blog/parts-manufacturers-challenges/",
            "https://www2.deloitte.com/us/en/insights/industry/retail-distribution/consumer-behavior-trends-state-of-the-consumer-tracker/auto-industry-challenges.html",
            "https://www.newstreaming.com/top-5-supply-chain-challenges-in-the-automotive-industry/amp/",
            "https://www.blumeglobal.com/learning/automotive-supply-chain/",
            "https://www.gminsights.com/blogs/top-challenges-in-the-automotive-industry-pre-COVID/amp",
            "https://www.just-auto.com/features/pressing-issues-for-automotive-supply-chains/#catfish",
            "https://sheaglobal.com/the-supply-chain-challenges-of-the-automotive-industry/",
            "https://www.forbes.com/sites/forbesbusinesscouncil/2021/09/22/overcoming-supply-chain-issues-automotive-oems-and-suppliers-must-work-together/amp/",
            "https://www.globenewswire.com/news-release/2023/03/07/2622226/0/en/Auto-Parts-Manufacturing-Market-Report-2022-2030-Focus-on-Innovation-to-Provide-a-Competitive-Edge.html",
            "https://www.expertmarketresearch.com/reports/auto-parts-manufacturing-market",
            ],
        }
    # urls = [
    #     "https://www.deskera.com/blog/plastic-manufacturing-key-trends-and-innovations/amp/",
    #     "https://www.fortunebusinessinsights.com/amp/plastics-market-102176",
    #     "https://www.kaysun.com/blog/plastics-industry-trends",
    #     "https://www.manufacturing.net/operations/article/13057614/the-future-of-plastics-manufacturing-in-the-us"
    # ]
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

    with open(outputPath, 'w') as outputFile:
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


def combinePageSummaries(pageSummaries, modelToUse):
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
    print(f"\n\nCombined page summaries:\n{combinedSummary}")
    return combinedSummary


if __name__ == '__main__':
    main()
