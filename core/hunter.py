import asyncio
import aiohttp
import re
import logging
from typing import List, Set
from urllib.parse import urlparse
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)

class IPTVHunter:
    def __init__(self):
        self.sources = [
            "https://iptv-org.github.io/iptv/index.m3u",
            "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8",
            "https://raw.githubusercontent.com/iptv-hub/iptv-hub/main/playlist.m3u",
            "https://iptv-org.github.io/iptv/index.nsfw.m3u",
            "https://raw.githubusercontent.com/ismailozgul/iptv/main/playlist.m3u",
        ]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.semaphore = asyncio.Semaphore(5)

    async def fetch_m3u(self, session: aiohttp.ClientSession, url: str) -> str:
        async with self.semaphore:
            try:
                async with session.get(url, headers=self.headers, timeout=20) as response:
                    if response.status == 200:
                        return await response.text()
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
            return ""

    def parse_m3u(self, content: str, query: str) -> List[dict]:
        results = []
        # Pattern to match #EXTINF and the URL
        # #EXTINF:-1 tvg-id="ID" tvg-logo="LOGO" group-title="GROUP",CHANNEL NAME\nURL
        pattern = r'#EXTINF:.*?,(.*?)\n(https?://[^\s]+)'
        matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
        
        query_clean = query.lower().replace(" ", "")
        
        for name, url in matches:
            name_clean = name.strip()
            # Simple fuzzy matching or substring
            ratio = fuzz.partial_ratio(query_clean, name_clean.lower().replace(" ", ""))
            if ratio > 80 or query_clean in name_clean.lower().replace(" ", ""):
                results.append({
                    "name": name_clean,
                    "url": url.strip(),
                    "score": ratio
                })
        return results

    async def hunt(self, query: str) -> List[dict]:
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_m3u(session, url) for url in self.sources]
            contents = await asyncio.gather(*tasks)
            
            all_results = []
            for content in contents:
                if content:
                    all_results.extend(self.parse_m3u(content, query))
            
            # Deduplicate and sort by score
            unique_results = {}
            for res in all_results:
                url = res['url']
                if url not in unique_results or res['score'] > unique_results[url]['score']:
                    unique_results[url] = res
            
            sorted_results = sorted(unique_results.values(), key=lambda x: x['score'], reverse=True)
            return sorted_results[:20]

    async def validate_link(self, session: aiohttp.ClientSession, url: str) -> bool:
        try:
            async with session.head(url, headers=self.headers, timeout=5, allow_redirects=True) as response:
                return response.status in [200, 206]
        except:
            return False

    async def get_valid_links(self, query: str) -> List[dict]:
        results = await self.hunt(query)
        async with aiohttp.ClientSession() as session:
            validation_tasks = [self.validate_link(session, res['url']) for res in results]
            valid_flags = await asyncio.gather(*validation_tasks)
            
            valid_results = [res for res, is_valid in zip(results, valid_flags) if is_valid]
            return valid_results
