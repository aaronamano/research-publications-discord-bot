# bot.py
import os
import re
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import discord
from discord.ext import tasks
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

ANTHROPIC_RESEARCH_URL = "https://www.anthropic.com/research"

intents = discord.Intents.default()
client = discord.Client(intents=intents)

posted_links = set()


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


@tasks.loop(hours=12)
async def poll_anthropic_research():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        print("Channel not found. Check CHANNEL_ID.")
        return

    try:
        new_articles = await fetch_anthropic_research()
    except Exception as e:
        print(f"Error fetching research: {e}")
        return

    for article in new_articles:
        embed = discord.Embed(
            title=article["title"][:256],
            color=discord.Color.blurple(),
            url=article["url"],
        )
        if article["date"]:
            embed.add_field(name="Date", value=article["date"], inline=True)

        await channel.send(embed=embed)
        await channel.send(article["url"])
        await asyncio.sleep(2)


@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("------")
    if not poll_anthropic_research.is_running():
        poll_anthropic_research.start()


if __name__ == "__main__":
    if not DISCORD_TOKEN or CHANNEL_ID == 0:
        raise SystemExit(
            "Set DISCORD_TOKEN and CHANNEL_ID in your environment or .env file."
        )
    client.run(DISCORD_TOKEN)
