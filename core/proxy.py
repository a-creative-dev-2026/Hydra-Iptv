import aiohttp
from fastapi import Response
from fastapi.responses import StreamingResponse
import logging

logger = logging.getLogger(__name__)

class StreamProxy:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Icy-MetaData": "1"
        }

    async def stream_generator(self, url: str):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers, timeout=None) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch stream: {response.status}")
                        return

                    async for chunk in response.content.iter_chunked(8192):
                        if chunk:
                            yield chunk
            except Exception as e:
                logger.error(f"Proxy Error: {e}")

    async def get_stream_response(self, url: str):
        # We can try to detect if it's an M3U8 or a direct TS stream
        if ".m3u8" in url.lower():
            # For M3U8, redirecting is often better for the player to handle segments
            # but we can also proxy it if we want to hide the source
            return Response(status_code=302, headers={"Location": url})
        
        # For direct TS/MP4 streams, proxying helps with stability and CORS
        return StreamingResponse(
            self.stream_generator(url),
            media_type="video/mp2t",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            }
        )
