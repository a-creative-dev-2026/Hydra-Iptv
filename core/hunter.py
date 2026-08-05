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
        self.semaphore = asyncio.Semaphore(5)

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
                # Reduced timeout to 10s to prevent global timeout
                async with session.get(url, headers=self.get_headers(), timeout=10) as response:
                    if response.status == 200:
                        return await response.text()
            except Exception as e:
                logger.debug(f"Error fetching {url}: {e}")
            return ""

    def parse_m3u(self, content: str, query: str) -> List[dict]:
        results = []
        pattern = r'#EXTINF:.*?(?:tvg-id="(.*?)")?.*?(?:tvg-logo="(.*?)")?.*?(?:group-title="(.*?)")?.*?,(.*?)\n(https?://[^\s]+)'
        matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
        
        query_clean = query.lower().strip()
        
        for tvg_id, logo, group, name, url in matches:
            name_clean = name.strip()
            name_lower = name_clean.lower()
            
            token_ratio = fuzz.token_set_ratio(query_clean, name_lower)
            partial_ratio = fuzz.partial_ratio(query_clean, name_lower)
            
            query_words = query_clean.split()
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

    async def shadow_search(self, query: str) -> List[dict]:
        return []

    async def deep_hunt(self, query: str) -> List[dict]:
        all_results = await self.hunt(query)
        
        if not all_results:
            all_results = await self.shadow_search(query)

        # Optimization: Only validate top 3 if we have many results, to save time
        if all_results:
            async with aiohttp.ClientSession() as session:
                top_results = all_results[:3]
                validation_tasks = [self.validate_link(session, res['url']) for res in top_results]
                valid_flags = await asyncio.gather(*validation_tasks)
                
                for i, is_valid in enumerate(valid_flags):
                    if is_valid:
                        top_results[i]['score'] += 200
                        top_results[i]['status'] = "online"
                    else:
                        top_results[i]['status'] = "offline"
        
        qualities = {"FHD": [], "HD": [], "SD": []}
        for res in all_results:
            qualities[res.get("quality", "SD")].append(res)
        
        final_list = []
        for q in ["FHD", "HD", "SD"]:
            sorted_q = sorted(qualities[q], key=lambda x: x['score'], reverse=True)
            final_list.extend(sorted_q[:5]) 
            
        return sorted(final_list, key=lambda x: x['score'], reverse=True)[:20]

    async def hunt(self, query: str) -> List[dict]:
        all_results = []
        local_tasks = []
        if os.path.exists(self.local_playlists_dir):
            for filename in os.listdir(self.local_playlists_dir):
                if filename.endswith(".m3u8"):
                    filepath = os.path.join(self.local_playlists_dir, filename)
                    local_tasks.append(self.read_local_file(filepath, query))
        
        local_results = await asyncio.gather(*local_tasks)
        for res in local_results:
            all_results.extend(res)

        async with aiohttp.ClientSession() as session:
            remote_tasks = [self.fetch_m3u(session, url) for url in self.sources]
            contents = await asyncio.gather(*remote_tasks)
            
            for content in contents:
                if content:
                    all_results.extend(self.parse_m3u(content, query))
            
            unique_results = {}
            for res in all_results:
                url = res['url']
                if url not in unique_results or res['score'] > unique_results[url]['score']:
                    unique_results[url] = res
            
            return sorted(unique_results.values(), key=lambda x: x['score'], reverse=True)

    async def read_local_file(self, filepath: str, query: str) -> List[dict]:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return self.parse_m3u(f.read(), query)
        except:
            return []

    async def validate_link(self, session: aiohttp.ClientSession, url: str) -> bool:
        try:
            headers = self.get_headers()
            async with session.head(url, headers=headers, timeout=5, allow_redirects=True) as response:
                return response.status in [200, 206]
        except:
            return False

    async def get_valid_links(self, query: str) -> List[dict]:
        results = await self.deep_hunt(query)
        return [r for r in results if r.get('status') == 'online']
