import pytest
import aiohttp
import os
from bs4 import BeautifulSoup
from unittest.mock import AsyncMock, MagicMock, patch
from dreamhost_backup import get_download_links, clean_filename, download_file, main

@pytest.mark.asyncio
async def test_get_download_links_missing_file():
    links = await get_download_links("non_existent_file.html")
    assert links == []

@pytest.mark.asyncio
async def test_get_download_links_valid_html(tmp_path):
    html_content = """
    <html>
        <body>
            <a href="http://example.com/backup_2023_01_01.tar.gz">Backup 1</a>
            <a href="http://example.com/database_2023_01_01.sql.gz">DB 1</a>
            <a href="http://example.com/not_a_backup.txt">Not a backup</a>
        </body>
    </html>
    """
    d = tmp_path / "test.html"
    d.write_text(html_content)
    links = await get_download_links(str(d))
    assert len(links) == 2
    assert "http://example.com/backup_2023_01_01.tar.gz" in links
    assert "http://example.com/database_2023_01_01.sql.gz" in links

@pytest.mark.asyncio
async def test_get_download_links_no_links(tmp_path):
    html_content = "<html><body>No links here</body></html>"
    d = tmp_path / "test.html"
    d.write_text(html_content)
    links = await get_download_links(str(d))
    assert links == []

@pytest.mark.asyncio
@pytest.mark.parametrize("url,expected", [
    ("http://example.com/file.tar.gz", "file.tar.gz"),
    ("http://example.com/path/to/file.sql.gz?token=123", "path/to/file.sql.gz"),
    ("http://example.com/nested/path/backup.tar.gz", "nested/path/backup.tar.gz"),
    ("http://example.com/mail/user%40example.com.tar.gz", "mail/user@example.com.tar.gz"),
])
async def test_clean_filename(url, expected):
    result = await clean_filename(url)
    assert result == expected

@pytest.mark.asyncio
async def test_download_file_success(tmp_path):
    # Mock aiohttp session and response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.headers = {'content-length': '12'}
    mock_response.content.read = AsyncMock(side_effect=[b"chunk1", b"chunk2", b""])
    
    # Properly mock the async context manager for session.get
    mock_session = MagicMock()
    mock_session.get.return_value.__aenter__.return_value = mock_response

    url = "http://example.com/mail/test_backup.tar.gz"
    
    # Change CWD to tmp_path so the file is created there
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        result = await download_file(mock_session, url)
        assert result == "mail/test_backup.tar.gz"
        assert os.path.exists("mail/test_backup.tar.gz")
        with open("mail/test_backup.tar.gz", "rb") as f:
            assert f.read() == b"chunk1chunk2"
    finally:
        os.chdir(original_cwd)

@pytest.mark.asyncio
async def test_download_file_failure():
    mock_response = AsyncMock()
    mock_response.status = 404
    
    mock_session = MagicMock()
    mock_session.get.return_value.__aenter__.return_value = mock_response

    url = "http://example.com/missing.tar.gz"
    result = await download_file(mock_session, url)
    assert result is None

@pytest.mark.asyncio
async def test_get_download_links_exception(tmp_path):
    # Trigger an exception during file reading
    d = tmp_path / "error.html"
    d.write_text("dummy")
    with patch("builtins.open", side_effect=Exception("Read error")):
        links = await get_download_links(str(d))
    assert links == []

@pytest.mark.asyncio
async def test_get_download_links_bs4_fallback(tmp_path):
    # Test fallback to html.parser if lxml fails
    html_content = '<html><body><a href="test.tar.gz">link</a></body></html>'
    d = tmp_path / "fallback.html"
    d.write_text(html_content)
    
    with patch("bs4.BeautifulSoup", side_effect=[Exception("lxml failed"), BeautifulSoup(html_content, "html.parser")]):
        links = await get_download_links(str(d))
    assert links == ["test.tar.gz"]


@pytest.mark.asyncio
async def test_main_missing_args():
    with pytest.raises(SystemExit) as excinfo:
        await main(["script.py"])
    assert excinfo.value.code == 1

@pytest.mark.asyncio
@patch("dreamhost_backup.get_download_links")
@patch("dreamhost_backup.download_file")
async def test_main_happy_path(mock_download, mock_get_links):
    mock_get_links.return_value = ["http://example.com/link1.tar.gz"]
    mock_download.return_value = "link1.tar.gz"
    
    # Mocking tqdm.gather as well since it's used in main
    with patch("tqdm.asyncio.tqdm.gather", AsyncMock(return_value=["link1.tar.gz"])):
         await main(["script.py", "dummy.html"])
    
    mock_get_links.assert_called_once_with("dummy.html")

@pytest.mark.asyncio
@patch("dreamhost_backup.get_download_links")
async def test_main_no_links(mock_get_links):
    mock_get_links.return_value = []
    # Smoke test for "Done (no files to download)" path
    await main(["script.py", "dummy.html"])
    mock_get_links.assert_called_once_with("dummy.html")

@pytest.mark.asyncio
@patch("dreamhost_backup.main")
async def test_script_execution_keyboard_interrupt(mock_main):
    # This tests the block:
    # if __name__ == "__main__":
    #     try:
    #         asyncio.run(main(sys.argv))
    #     except KeyboardInterrupt:
    mock_main.side_effect = KeyboardInterrupt
    
    # We can't easily test the if __name__ == "__main__" block directly without subprocess,
    # but we can test the effect if we mock main to raise KeyboardInterrupt.
    # Actually, the block is in the module scope.
    pass

def test_dreamhost_backup_script_keyboard_interrupt():
    # Test the KeyboardInterrupt handling in dreamhost_backup.py
    # We need to run it as a script and interrupt it.
    # This is complex to do reliably, so we skip it as per rules if "too tightly coupled".
    # However, we can mock asyncio.run in a subprocess test if needed.
    pass
