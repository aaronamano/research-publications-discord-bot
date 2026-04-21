import re
import aiohttp
from bs4 import BeautifulSoup

from shared import posted_links

ANTHROPIC_RESEARCH_URL = "https://www.anthropic.com/research"


async def fetch_anthropic_research():
    """Scrape Anthropic research Publications section."""
    async with aiohttp.ClientSession() as session:
        async with session.get(ANTHROPIC_RESEARCH_URL) as response:
            if response.status != 200:
                raise Exception(f"HTTP {response.status}")
            html = await response.text()

    soup = BeautifulSoup(html, "html.parser")

    publications = soup.find(
        string=lambda t: t and "Publications" in t and t.strip() == "Publications"
    )
    if not publications:
        return []

    pub_header = publications.find_parent(["section", "div"])
    if not pub_header:
        return []

    pub_section = pub_header.find_next_sibling()
    if not pub_section:
        return []

    articles = []
    seen = set()

    for a in pub_section.select("a[href^='/research/'], a[href^='/news/']"):
        href = a.get("href")
        if not href or href in ("/research", "/news"):
            continue

        title = a.get_text(strip=True)
        if not title or len(title) < 5:
            continue

        date_match = re.search(
            r"^([A-Z][a-z]{2}\s+\d{1,2},?\s+\d{4})",
            title,
        )
        if date_match:
            date = date_match.group(1)
            title = title[len(date) :].strip()
            title = re.sub(
                r"^(Alignment|Economic Research|Interpretability|Societal Impacts|Policy|Science)\s*",
                "",
                title,
            )
        else:
            date = ""

        full_url = f"https://www.anthropic.com{href}"
        if full_url in seen:
            continue
        seen.add(full_url)

        if full_url not in posted_links:
            posted_links.add(full_url)
            articles.append(
                {"title": title[:256], "url": full_url, "date": date, "image": ""}
            )

    articles.reverse()
    return articles
