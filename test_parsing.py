import asyncio
from dreamhost_backup import get_download_links

async def test():
    links = await get_download_links("backup.html")
    print(f"Found {len(links)} links")
    for link in links[:5]:
        print(link)

if __name__ == "__main__":
    asyncio.run(test())
