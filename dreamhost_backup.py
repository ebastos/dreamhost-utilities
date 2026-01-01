#!/usr/bin/env python

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import sys
import os
from tqdm.asyncio import tqdm
from urllib.parse import unquote, urlparse


async def get_download_links(filename: str) -> list:
    """Returns a list of files to download"""
    try:
        if not os.path.exists(filename):
            print(f"Error: File '{filename}' not found.")
            return []
            
        with open(filename, "r") as file:
            contents = file.read()
            
        # Try to use lxml if available, otherwise fallback to html.parser
        try:
            soup = BeautifulSoup(contents, features="lxml")
        except Exception:
            soup = BeautifulSoup(contents, features="html.parser")
            
        links = [a["href"] for a in soup.find_all("a", href=True) if ".tar.gz" in a["href"] or ".sql.gz" in a["href"]]
        if not links:
            print("No backup links found in the provided HTML file.")
        return links
    except Exception as e:
        print(f"Error parsing file: {e}")
        return []


async def clean_filename(url: str) -> str:
    parsed_url = urlparse(url)
    path = unquote(parsed_url.path)
    # Remove leading slash if present
    if path.startswith("/"):
        path = path[1:]
    return path


async def download_file(session: aiohttp.ClientSession, url: str):
    local_filename = await clean_filename(url)
    try:
        async with session.get(url) as response:
            if response.status != 200:
                print(f"Failed to download {local_filename}: Status {response.status}")
                return None
                
            total_size = int(response.headers.get('content-length', 0))
            
            # Ensure parent directories exist
            os.makedirs(os.path.dirname(os.path.abspath(local_filename)), exist_ok=True)
            
            with open(local_filename, "wb") as f:
                with tqdm(
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    desc=local_filename,
                    leave=False
                ) as pbar:
                    while True:
                        chunk = await response.content.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        pbar.update(len(chunk))
        return local_filename
    except Exception as e:
        print(f"Error downloading {local_filename}: {e}")
        return None


async def main(args: list):
    if len(args) != 2:
        print(f"Usage: {args[0]} filename.html")
        print("Example: Save the DreamHost backup page as HTML and pass it here.")
        raise SystemExit(1)

    download_links = await get_download_links(args[1])
    if not download_links:
        print("Done (no files to download).")
        return

    async with aiohttp.ClientSession() as session:
        # We use a semaphore to limit concurrent downloads to avoid overwhelming the connection
        semaphore = asyncio.Semaphore(3)
        
        async def sem_download(url):
            async with semaphore:
                return await download_file(session, url)

        print(f"Starting download of {len(download_links)} files...")
        tasks = [sem_download(link) for link in download_links]
        
        # Use tqdm to track progress of all tasks
        results = await tqdm.gather(*tasks, desc="Total Progress")

    downloaded = [r for r in results if r]
    print(f"\nSuccessfully downloaded {len(downloaded)} out of {len(download_links)} files.")


if __name__ == "__main__":
    try:
        asyncio.run(main(sys.argv))
    except KeyboardInterrupt:
        print("\nDownload interrupted by user.")
        sys.exit(1)
