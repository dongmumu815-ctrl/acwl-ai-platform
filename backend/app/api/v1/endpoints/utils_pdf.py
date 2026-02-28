from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import Response
import httpx

router = APIRouter()

@router.get("/pdf-proxy")
async def pdf_proxy(url: str = Query(...)):
    if not (url.startswith("http://") or url.startswith("https://")):
        raise HTTPException(status_code=400, detail="invalid url")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="fetch failed")
            data = resp.content
            headers = {
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "no-cache"
            }
            return Response(content=data, media_type="application/pdf", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"proxy error: {e}")
