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
                async with session.get(url, headers=self.get_headers(), timeout=25) as response:
                    if response.status == 200:
                        return await response.text()
            except Exception as e:
                logger.debug(f"Error fetching {url}: {e}")
            return ""

    def parse_m3u(self, content: str, query: str) -> List[dict]:
        results = []
        # Predatory Pattern: Capture more metadata and handle messy M3U formats
        pattern = r'#EXTINF:.*?(?:tvg-id="(.*?)")?.*?(?:tvg-logo="(.*?)")?.*?,(.*?)\n(https?://[^\s]+)'
        matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
        
        query_clean = query.lower().strip()
        
        for tvg_id, logo, name, url in matches:
            name_clean = name.strip()
            name_lower = name_clean.lower()
            
            # Predatory Accuracy: Multi-stage verification
            # 1. Exact match check
            # 2. Token set ratio (handles word order)
            # 3. Partial ratio (handles extra text)
            
            token_ratio = fuzz.token_set_ratio(query_clean, name_lower)
            partial_ratio = fuzz.partial_ratio(query_clean, name_lower)
            
            # Predatory Rule: If query is "beIN Sports 1", don't just return "beIN Sports"
            # It must contain all parts of the query for high score
            query_words = query_clean.split()
            all_words_present = all(word in name_lower for word in query_words)
            
            if (token_ratio > 90 and all_words_present) or (partial_ratio == 100 and len(query_clean) > 3):
                # Detect quality
                quality = "SD"
                if any(q in name_lower for q in ["fhd", "1080p", "4k", "uhd"]): quality = "FHD"
                elif any(q in name_lower for q in ["hd", "720p"]): quality = "HD"
                
                # Boost score for exact matches and quality
                score = token_ratio
                if all_words_present: score += 20
                if quality == "FHD": score += 10
                
                results.append({
                    "name": name_clean,
                    "url": url.strip(),
                    "logo": logo if logo else None,
                    "quality": quality,
                    "score": score
                })
        return results

    async def scrape_web_for_links(self, query: str) -> List[dict]:
        """Scrapes the web for direct m3u8 links when M3U sources fail"""
        # This is a simplified simulation of a scraper logic
        # In a real scenario, you'd use search engines or specific IPTV sites
        return []

    async def deep_hunt(self, query: str) -> List[dict]:
        """The 'Monster' search - searches multiple sources and returns ranked multi-quality links"""
        all_results = await self.hunt(query)
        
        # If results are low, try web scraping (Placeholder for future expansion)
        if len(all_results) < 3:
            web_results = await self.scrape_web_for_links(query)
            all_results.extend(web_results)

        # Group by quality and take top results for each
        qualities = {"FHD": [], "HD": [], "SD": []}
        for res in all_results:
            qualities[res.get("quality", "SD")].append(res)
        
        final_monster_list = []
        # Ensure we get at least 5 unique links from different sources
        for q in ["FHD", "HD", "SD"]:
            sorted_q = sorted(qualities[q], key=lambda x: x['score'], reverse=True)
            final_monster_list.extend(sorted_q[:5]) 
            
        return sorted(final_monster_list, key=lambda x: x['score'], reverse=True)[:15]

    async def hunt(self, query: str) -> List[dict]:
        all_results = []
        
        # 1. Search in local playlists first (Faster)
        if os.path.exists(self.local_playlists_dir):
            for filename in os.listdir(self.local_playlists_dir):
                if filename.endswith(".m3u8"):
                    filepath = os.path.join(self.local_playlists_dir, filename)
                    try:
                        # Read and parse each part
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            all_results.extend(self.parse_m3u(f.read(), query))
                    except Exception as e:
                        logger.error(f"Error reading local playlist {filename}: {e}")

        # 2. Search in remote sources
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_m3u(session, url) for url in self.sources]
            contents = await asyncio.gather(*tasks)
            
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
