import requests


def fetch_remote_content(file_url: str, timeout: int = 5) -> str:
    """
    Fetches raw text content from a remote URL.
    """
    response = requests.get(file_url, timeout=timeout)
    response.raise_for_status()
    return response.text
