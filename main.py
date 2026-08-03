import os
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from core.hunter import IPTVHunter
from core.proxy import StreamProxy
from db.cache import AsyncCache
from models.channel import SearchResult
from db.channels import COUNTRY_CHANNELS, CATEGORIES, get_country_url, get_category_url
import uvicorn
import requests

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HydraIPTV")

app = FastAPI(
    title="Hydra IPTV API",
    description="Advanced IPTV Proxy and Search Engine",
    version="4.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Components
hunter = IPTVHunter()
proxy = StreamProxy()
cache = AsyncCache()

# Static files
if not os.path.exists("static"):
    os.makedirs("static")

@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def index():
    try:
        with open("static/index.html", "r") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Hydra IPTV v4.0</h1><p>Dashboard file not found. Check static/index.html</p>"

@app.get("/search/{query}", response_model=SearchResult)
async def search(query: str):
    logger.info(f"Searching for: {query}")
    
    # Check cache
    cached = await cache.get(query)
    if cached:
        logger.info(f"Cache hit for: {query}")
        return cached

    results = await hunter.get_valid_links(query)
    
    if not results:
        return JSONResponse(
            status_code=404,
            content={"found": False, "query": query, "count": 0, "links": []}
        )

    response_data = {
        "query": query,
        "found": True,
        "count": len(results),
        "links": [r['url'] for r in results],
        "channels": results
    }
    
    await cache.set(query, response_data)
    return response_data

@app.get("/channel/{name}")
async def get_channel(name: str):
    logger.info(f"Streaming channel: {name}")
    
    # Try to find the channel
    results = await hunter.get_valid_links(name)
    if not results:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # Use the best link (first one)
    best_link = results[0]['url']
    return await proxy.get_stream_response(best_link)

@app.get("/playlist/country/{code}")
async def get_country_playlist(code: str):
    url = get_country_url(code)
    if not url:
        raise HTTPException(status_code=404, detail="Country not found")
    
    try:
        # We can proxy the M3U or redirect
        return RedirectResponse(url=url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/playlist/category/{name}")
async def get_category_playlist(name: str):
    url = get_category_url(name)
    if not url:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return RedirectResponse(url=url)

@app.get("/countries")
async def list_countries():
    return [{"code": k, "name": v['name']} for k, v in COUNTRY_CHANNELS.items()]

@app.get("/categories")
async def list_categories():
    return [{"id": k, "name": v['name']} for k, v in CATEGORIES.items()]

@app.get("/stats")
async def stats():
    return {
        "status": "online",
        "cache": cache.get_stats(),
        "total_countries": len(COUNTRY_CHANNELS),
        "total_categories": len(CATEGORIES),
        "version": "4.0.0"
    }

if __name__ == "__main__":
    # Render and other platforms often use the PORT environment variable.
    # We default to 10000 if not set, but respect the system's choice.
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
