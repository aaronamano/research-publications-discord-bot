# bot.py
import os
import re
import json
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
NVIDIA_RESEARCH_URL = "https://research.nvidia.com/publications"
DEEPMIND_RESEARCH_URL = "https://deepmind.google/research/publications/"

ANTHROPIC_LOGO = "https://cdn.prod.website-files.com/67ce28cfec624e2b733f8a52/681d52619fec35886a7f1a70_favicon.png"
NVIDIA_LOGO = "https://companieslogo.com/img/orig/NVDA-220e1e03.png"
DEEPMIND_LOGO = "https://storage.googleapis.com/gdm-deepmind-com-prod-public/icons/google_deepmind_2x_96dp.png"

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
        embed.set_author(name="Anthropic Research", icon_url=ANTHROPIC_LOGO)
        if article["date"]:
            embed.add_field(name="Date", value=article["date"], inline=True)
        embed.add_field(
            name="Source",
            value="[Anthropic Research](https://www.anthropic.com/research)",
            inline=True,
        )

        await channel.send(embed=embed)
        await asyncio.sleep(1)


@tasks.loop(hours=12)
async def poll_nvidia_research():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        print("Channel not found. Check CHANNEL_ID.")
        return

    try:
        new_articles = await fetch_nvidia_research()
    except Exception as e:
        print(f"Error fetching NVIDIA research: {e}")
        return

    for article in new_articles:
        embed = discord.Embed(
            title=article["title"][:256],
            color=discord.Color.green(),
            url=article["url"],
        )
        embed.set_author(name="NVIDIA Research", icon_url=NVIDIA_LOGO)
        if article["date"]:
            embed.add_field(name="Date", value=article["date"], inline=True)
        embed.add_field(
            name="Source",
            value="[NVIDIA Research](https://research.nvidia.com/publications)",
            inline=True,
        )

        await channel.send(embed=embed)
        await asyncio.sleep(1)


@tasks.loop(hours=12)
async def poll_deepmind_research():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        print("Channel not found. Check CHANNEL_ID.")
        return

    try:
        new_articles = await fetch_deepmind_research()
    except Exception as e:
        print(f"Error fetching DeepMind research: {e}")
        return

    for article in new_articles:
        embed = discord.Embed(
            title=article["title"][:256],
            color=discord.Color.blue(),
            url=article["url"],
        )
        embed.set_author(name="DeepMind Research", icon_url=DEEPMIND_LOGO)
        if article["date"]:
            embed.add_field(name="Date", value=article["date"], inline=True)
        embed.add_field(
            name="Source",
            value="[DeepMind Research](https://deepmind.google/research/publications/)",
            inline=True,
        )

        await channel.send(embed=embed)
        await asyncio.sleep(1)


@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("------")
    if not poll_anthropic_research.is_running():
        poll_anthropic_research.start()
    if not poll_nvidia_research.is_running():
        poll_nvidia_research.start()
    if not poll_deepmind_research.is_running():
        poll_deepmind_research.start()


if __name__ == "__main__":
    if not DISCORD_TOKEN or CHANNEL_ID == 0:
        raise SystemExit(
            "Set DISCORD_TOKEN and CHANNEL_ID in your environment or .env file."
        )
    client.run(DISCORD_TOKEN)
