import os
import json
import requests
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Any

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MediaResult(BaseModel):
    url: str
    type: str
    quality: Optional[str] = None
    size: Optional[str] = None
    thumb: Optional[str] = None

class ItemResult(BaseModel):
    inputUrl: str
    platform: str
    result: List[Any]

class ResponseModel(BaseModel):
    success: bool
    url: str
    data: List[ItemResult]

@app.get("/")
async def home():
    return {
        "message": "Instagram Downloader API",
        "usage": "/api/insta?url=INSTAGRAM_URL"
    }

@app.get("/api/insta")
async def download_instagram(url: str = Query(..., description="Instagram URL")):
    # Validate Instagram URL
    if 'instagram.com' not in url:
        raise HTTPException(status_code=400, detail="Only Instagram URLs are supported")
    
    APIFY_TOKEN = os.environ.get('APIFY_TOKEN', 'apify_api_qt1Mqt4thz8KaXh0uQBkquhGNdUYPB0acxhY')
    
    if not APIFY_TOKEN:
        raise HTTPException(status_code=500, detail="APIFY_TOKEN not configured")
    
    try:
        # Call Apify API
        apify_response = requests.post(
            'https://api.apify.com/v2/acts/elis~instagram-downloader-api/runs?waitForFinish=120',
            headers={
                'Authorization': f'Bearer {APIFY_TOKEN}',
                'Content-Type': 'application/json'
            },
            json={'url': [url]},
            timeout=130
        )
        
        if apify_response.status_code != 200:
            raise HTTPException(
                status_code=apify_response.status_code,
                detail=f"Apify API error: {apify_response.text}"
            )
        
        data = apify_response.json()
        
        # Extract dataset ID and fetch results
        dataset_id = data.get('data', {}).get('defaultDatasetId')
        results = []
        
        if dataset_id:
            dataset_response = requests.get(
                f'https://api.apify.com/v2/datasets/{dataset_id}/items',
                headers={'Authorization': f'Bearer {APIFY_TOKEN}'},
                timeout=30
            )
            
            if dataset_response.status_code == 200:
                results = dataset_response.json()
        else:
            results = data.get('data', {}).get('datasetItems', [])
        
        # Format response
        formatted_results = []
        for item in results:
            formatted_results.append({
                'inputUrl': item.get('inputUrl', url),
                'platform': item.get('platform', 'instagram'),
                'result': item.get('result', item.get('media', []))
            })
        
        return {
            'success': True,
            'url': url,
            'data': formatted_results
        }
        
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Request timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# For Vercel serverless
app = app