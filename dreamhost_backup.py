#!/usr/bin/env python

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import sys


async def get_download_links(filename: str) -> list:
    """Returns a list of files to download"""
    with open(filename, "r") as file:
        contents = file.read()
    soup = BeautifulSoup(contents, features="lxml")
    return [a["href"] for a in soup.find_all("a", href=True)]


async def clean_filename(filename: str) -> str:
    filename = filename.split("/")[-1]
    return filename.split("?")[0]


async def download_file(session: aiohttp.ClientSession, url: str):
    local_filename = await clean_filename(url)
    print(f"Downloading {local_filename}")
    async with session.get(url) as response:
        with open(local_filename, "wb") as f:
            while True:
                chunk = await response.content.read(8192)
                if not chunk:
                    break
                f.write(chunk)
    print(f"Finished downloading {local_filename}")
    return local_filename


async def main(args: list):
    if len(args) != 2:
        print(f"Usage {args[0]} filename")
        raise SystemExit(1)

    async with aiohttp.ClientSession() as session:
        download_links = await get_download_links(args[1])

        # Launch a download task for each file
        tasks = [
            asyncio.create_task(download_file(session, file)) for file in download_links
        ]

        # Wait for all tasks to complete
        await asyncio.gather(*tasks)

    # All tasks have completed
    print("All files downloaded")


if __name__ == "__main__":
    asyncio.run(main(sys.argv))
