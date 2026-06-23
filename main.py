import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/api/insta', methods=['GET', 'OPTIONS'])
def download_instagram():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    # Get URL parameter
    url = request.args.get('url')
    
    if not url:
        return jsonify({'error': 'Missing url parameter'}), 400
    
    # Validate Instagram URL
    if 'instagram.com' not in url:
        return jsonify({'error': 'Only Instagram URLs are supported'}), 400
    
    APIFY_TOKEN = os.environ.get('APIFY_TOKEN', 'apify_api_qt1Mqt4thz8KaXh0uQBkquhGNdUYPB0acxhY')
    
    if not APIFY_TOKEN:
        return jsonify({'error': 'APIFY_TOKEN not configured'}), 500
    
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
            return jsonify({
                'error': 'Apify API error',
                'details': apify_response.text
            }), apify_response.status_code
        
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
        
        return jsonify({
            'success': True,
            'url': url,
            'data': formatted_results
        })
        
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Request timeout'}), 504
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'Instagram Downloader API',
        'usage': '/api/insta?url=INSTAGRAM_URL'
    })

# For Vercel serverless
app = app