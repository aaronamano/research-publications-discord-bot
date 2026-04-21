import re
import aiohttp
from bs4 import BeautifulSoup

from shared import posted_links

DEEPMIND_RESEARCH_URL = "https://deepmind.google/research/publications/"


async def fetch_deepmind_research():
    """Scrape DeepMind research Publications section."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(DEEPMIND_RESEARCH_URL, headers=headers) as response:
            if response.status != 200:
                raise Exception(f"HTTP {response.status}")
            html = await response.text()

    soup = BeautifulSoup(html, "html.parser")

    articles = []
    seen = set()

    for link in soup.select("a[href*='/research/publications/']"):
        href = link.get("href")
        if not href or href == "/research/publications/":
            continue

        title = link.get_text(strip=True)
        if not title or len(title) < 5:
            continue

        if title in ("Publications", "Research", "Learn more", "Read more"):
            continue

        date = ""
        match = re.match(r"^(\d{1,2}\s+[A-Za-z]+\s+\d{4})\s*(.+)$", title)
        if match:
            date = match.group(1)
            title = match.group(2).strip()
        elif " - " in title:
            parts = title.rsplit(" - ", 1)
            if re.match(r"\d{1,2}\s+[A-Za-z]+\s+\d{4}$", parts[1].strip()):
                title = parts[0].strip()
                date = parts[1].strip()

        if href.startswith("/research/publications/"):
            full_url = f"https://deepmind.google{href}"
        elif href.startswith("http"):
            full_url = href
        else:
            continue

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
