import os
import logging
import time
from fastapi import FastAPI, Request, HTTPException, Depends
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
    title="Hydra IPTV - Absolute Sovereignty",
    description="Ultra-Advanced IPTV Predator & Proxy Engine",
    version="5.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting Logic
rate_limit_data = {}
async def rate_limiter(request: Request):
    client_ip = request.client.host
    now = time.time()
    if client_ip in rate_limit_data:
        last_request, count = rate_limit_data[client_ip]
        if now - last_request < 1:
            if count > 10: # 10 requests per second
                raise HTTPException(status_code=429, detail="Too many requests - Slow down, predator!")
            rate_limit_data[client_ip] = (last_request, count + 1)
        else:
            rate_limit_data[client_ip] = (now, 1)
    else:
        rate_limit_data[client_ip] = (now, 1)

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

@app.get("/search/{query}", response_model=SearchResult, dependencies=[Depends(rate_limiter)])
async def search(query: str):
    logger.info(f"Absolute Deep hunting for: {query}")
    
    cached = await cache.get(query)
    if cached:
        return cached

    # Use deep_hunt for multi-quality and more results
    results = await hunter.deep_hunt(query)
    
    if not results:
        return JSONResponse(status_code=404, content={"found": False, "query": query, "count": 0, "links": []})

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
    logger.info(f"Monster streaming: {name}")
    
    results = await hunter.deep_hunt(name)
    if not results:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # Pass all links for failover
    links = [r['url'] for r in results]
    return await proxy.get_stream_response(links)

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

@app.get("/health")
async def health():
    return {"status": "healthy", "uptime": time.time(), "version": "5.0.0"}

@app.get("/export/{query}")
async def export_m3u(query: str):
    logger.info(f"Exporting M3U for: {query}")
    results = await hunter.deep_hunt(query)
    if not results:
        raise HTTPException(status_code=404, detail="No channels found for export")
    
    m3u_content = "#EXTM3U\n"
    for ch in results:
        logo = ch.get('logo', '')
        group = ch.get('group', 'General')
        name = ch.get('name', 'Unknown')
        # Use our proxy URL for failover
        proxy_url = f"https://hydra-iptv.onrender.com/channel/{name}"
        m3u_content += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}",{name}\n{proxy_url}\n'
    
    return Response(content=m3u_content, media_type="application/x-mpegurl", headers={"Content-Disposition": f"attachment; filename=hydra_{query}.m3u"})

@app.on_event("shutdown")
async def shutdown_event():
    if hunter._session:
        await hunter._session.close()

@app.get("/stats")
async def stats():
    return {
        "status": "online",
        "engine": "Absolute Sovereignty",
        "cache": cache.get_stats(),
        "total_countries": len(COUNTRY_CHANNELS),
        "total_categories": len(CATEGORIES),
        "version": "5.0.0",
        "turbo": True
    }

if __name__ == "__main__":
    # Force PORT 5000 as explicitly requested by Render's environment logs
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting Hydra IPTV on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
