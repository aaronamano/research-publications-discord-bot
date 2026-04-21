import aiohttp
from bs4 import BeautifulSoup

from shared import posted_links

NVIDIA_RESEARCH_URL = "https://research.nvidia.com/publications"


async def fetch_nvidia_research():
    """Scrape NVIDIA research Publications section."""
    async with aiohttp.ClientSession() as session:
        async with session.get(NVIDIA_RESEARCH_URL) as response:
            if response.status != 200:
                raise Exception(f"HTTP {response.status}")
            html = await response.text()

    soup = BeautifulSoup(html, "html.parser")

    articles = []
    seen = set()

    for row in soup.select("div.views-row"):
        title_elem = row.select_one("div.views-field-title a")
        if not title_elem:
            continue

        href = title_elem.get("href")
        if not href:
            continue

        title = title_elem.get_text(strip=True)
        if not title or len(title) < 5:
            continue

        full_url = f"https://research.nvidia.com{href}"
        if full_url in seen:
            continue
        seen.add(full_url)

        if full_url not in posted_links:
            posted_links.add(full_url)
            articles.append(
                {"title": title[:256], "url": full_url, "date": "", "image": ""}
            )

    articles.reverse()
    return articles
