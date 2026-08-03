import aiohttp
from fastapi import Response
from fastapi.responses import StreamingResponse
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class StreamProxy:
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
            "VLC/3.0.18 LibVLC/3.0.18",
            "OTT-Player/1.0"
        ]

    def get_smart_headers(self, url: str):
        import random
        domain = urlparse(url).netloc
        headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "*/*",
            "Icy-MetaData": "1",
            "Connection": "keep-alive",
            "Referer": f"https://{domain}/",
            "Origin": f"https://{domain}"
        }
        return headers

    async def stream_generator(self, url: str):
        headers = self.get_smart_headers(url)
        # Increase timeout and use a more robust session
        timeout = aiohttp.ClientTimeout(total=None, connect=10, sock_read=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.get(url, headers=headers, allow_redirects=True) as response:
                    if response.status not in [200, 206]:
                        logger.error(f"Failed to fetch stream: {response.status} for {url}")
                        return

                    # Forward essential headers from the source
                    async for chunk in response.content.iter_chunked(16384): # Larger chunks for smoother HD
                        if chunk:
                            yield chunk
            except Exception as e:
                logger.error(f"Monster Proxy Error for {url}: {e}")

    async def get_stream_response(self, urls: list):
        """The Monster Proxy: Tries multiple URLs if one fails"""
        if not urls:
            return Response(status_code=404, content="No valid links found")

        # Try to find the first working URL
        for url in urls:
            try:
                # Quick check if link is alive
                async with aiohttp.ClientSession() as session:
                    async with session.head(url, timeout=3, allow_redirects=True) as resp:
                        if resp.status in [200, 206]:
                            if ".m3u8" in url.lower():
                                return Response(status_code=302, headers={"Location": url})
                            
                            return StreamingResponse(
                                self.stream_generator(url),
                                media_type="video/mp2t",
                                headers={
                                    "Access-Control-Allow-Origin": "*",
                                    "Cache-Control": "no-cache",
                                    "Connection": "keep-alive"
                                }
                            )
            except:
                continue
        
        # Fallback to the first one even if HEAD failed
        return Response(status_code=302, headers={"Location": urls[0]})
