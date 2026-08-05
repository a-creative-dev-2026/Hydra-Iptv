import asyncio
import aiohttp
import re
import logging
import os
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
            "https://raw.githubusercontent.com/Tukitv/Tukitv/main/Tukitv.m3u",
            "https://raw.githubusercontent.com/pizofre/iptv/master/playlist.m3u8",
            "https://raw.githubusercontent.com/Yebon/IPTV/main/playlist.m3u",
            "https://raw.githubusercontent.com/m3u8playlist/countries/main/arabic.m3u",
            "https://raw.githubusercontent.com/Moebis/TV/master/playlist.m3u8",
            "https://raw.githubusercontent.com/dtankf/Vip-Iptv/main/Vip-Iptv.m3u",
            "https://raw.githubusercontent.com/m3u8playlist/countries/main/france.m3u",
            "https://raw.githubusercontent.com/m3u8playlist/countries/main/uk.m3u",
            "https://raw.githubusercontent.com/m3u8playlist/countries/main/usa.m3u"
        ]
        self.local_playlists_dir = "data/playlists"
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
        ]
        self.semaphore = asyncio.Semaphore(10)
        self._session = None

    async def get_session(self):
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=15, connect=5)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    def get_headers(self):
        import random
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
            "Referer": "https://www.google.com/",
            "Origin": "https://www.google.com/"
        }

    async def fetch_m3u(self, session: aiohttp.ClientSession, url: str) -> str:
        async with self.semaphore:
            try:
                async with session.get(url, headers=self.get_headers()) as response:
                    if response.status == 200:
                        return await response.text()
            except Exception as e:
                logger.debug(f"Error fetching {url}: {e}")
            return ""

    def parse_m3u(self, content: str, query: str) -> List[dict]:
        results = []
        # Pattern for #EXTINF metadata and URL
        pattern = r'#EXTINF:.*?(?:tvg-id="(.*?)")?.*?(?:tvg-logo="(.*?)")?.*?(?:group-title="(.*?)")?.*?,(.*?)\n(https?://[^\s]+)'
        matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
        
        query_clean = query.lower().strip()
        query_words = query_clean.split()
        
        for tvg_id, logo, group, name, url in matches:
            name_clean = name.strip()
            name_lower = name_clean.lower()
            
            # Fast Check: Skip if name doesn't contain any query words
            if not any(word in name_lower for word in query_words):
                continue

            token_ratio = fuzz.token_set_ratio(query_clean, name_lower)
            partial_ratio = fuzz.partial_ratio(query_clean, name_lower)
            
            all_words_present = all(word in name_lower for word in query_words)
            
            if (token_ratio > 85 and all_words_present) or (partial_ratio == 100 and len(query_clean) > 2):
                quality = "SD"
                if any(q in name_lower for q in ["fhd", "1080p", "4k", "uhd"]): quality = "FHD"
                elif any(q in name_lower for q in ["hd", "720p"]): quality = "HD"
                
                score = token_ratio
                if all_words_present: score += 25
                if quality == "FHD": score += 15
                if query_clean == name_lower: score += 50
                
                results.append({
                    "name": name_clean,
                    "url": url.strip(),
                    "logo": logo if logo else f"https://ui-avatars.com/api/?name={name_clean}&background=random",
                    "group": group if group else "General",
                    "quality": quality,
                    "score": score
                })
        return results

    async def deep_hunt(self, query: str) -> List[dict]:
        # Step 1: Fast Local Search
        local_results = await self.search_local(query)
        
        # Step 2: Parallel Remote Search
        remote_results = await self.hunt_remote(query)
        
        all_results = local_results + remote_results
        
        # Deduplicate
        unique_results = {}
        for res in all_results:
            url = res['url']
            if url not in unique_results or res['score'] > unique_results[url]['score']:
                unique_results[url] = res
        
        final_list = sorted(unique_results.values(), key=lambda x: x['score'], reverse=True)

        # Step 3: Fast Validation (Top 3)
        if final_list:
            session = await self.get_session()
            top_3 = final_list[:3]
            validation_tasks = [self.validate_link(session, res['url']) for res in top_3]
            valid_flags = await asyncio.gather(*validation_tasks)
            
            for i, is_valid in enumerate(valid_flags):
                if is_valid:
                    top_3[i]['score'] += 200
                    top_3[i]['status'] = "online"
                else:
                    top_3[i]['status'] = "offline"
        
        # Final Grouping and Sorting
        qualities = {"FHD": [], "HD": [], "SD": []}
        for res in final_list:
            qualities[res.get("quality", "SD")].append(res)
        
        sorted_final = []
        for q in ["FHD", "HD", "SD"]:
            sorted_q = sorted(qualities[q], key=lambda x: x['score'], reverse=True)
            sorted_final.extend(sorted_q[:5]) 
            
        return sorted(sorted_final, key=lambda x: x['score'], reverse=True)[:20]

    async def search_local(self, query: str) -> List[dict]:
        results = []
        if os.path.exists(self.local_playlists_dir):
            tasks = []
            for filename in os.listdir(self.local_playlists_dir):
                if filename.endswith(".m3u8"):
                    filepath = os.path.join(self.local_playlists_dir, filename)
                    tasks.append(self.read_local_file(filepath, query))
            
            for res_list in await asyncio.gather(*tasks):
                results.extend(res_list)
        return results

    async def hunt_remote(self, query: str) -> List[dict]:
        session = await self.get_session()
        tasks = [self.fetch_m3u(session, url) for url in self.sources]
        contents = await asyncio.gather(*tasks)
        
        results = []
        for content in contents:
            if content:
                results.extend(self.parse_m3u(content, query))
        return results

    async def read_local_file(self, filepath: str, query: str) -> List[dict]:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return self.parse_m3u(f.read(), query)
        except:
            return []

    async def validate_link(self, session: aiohttp.ClientSession, url: str) -> bool:
        try:
            async with session.head(url, headers=self.get_headers(), timeout=5, allow_redirects=True) as response:
                return response.status in [200, 206]
        except:
            return False
