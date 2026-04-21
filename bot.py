# bot.py
import os
import asyncio
import discord
from discord.ext import tasks
from dotenv import load_dotenv
from fetchers import (
    fetch_anthropic_research,
    fetch_nvidia_research,
    fetch_deepmind_research,
)

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

ANTHROPIC_LOGO = "https://cdn.prod.website-files.com/67ce28cfec624e2b733f8a52/681d52619fec35886a7f1a70_favicon.png"
NVIDIA_LOGO = "https://companieslogo.com/img/orig/NVDA-220e1e03.png"
DEEPMIND_LOGO = "https://storage.googleapis.com/gdm-deepmind-com-prod-public/icons/google_deepmind_2x_96dp.png"

intents = discord.Intents.default()
client = discord.Client(intents=intents)


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
