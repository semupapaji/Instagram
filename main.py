# api/insta.py (Vercel Python serverless function)

import os
import json
import requests
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        # CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

        # Parse URL parameters
        parsed_url = urlparse(self.path)
        params = parse_qs(parsed_url.query)
        
        # Check if path is /api/insta
        if parsed_url.path != '/api/insta':
            self.send_response(404)
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())
            return

        # Get URL parameter
        url = params.get('url', [None])[0]
        
        if not url:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Missing url parameter'}).encode())
            return

        # Validate Instagram URL
        if 'instagram.com' not in url:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Only Instagram URLs are supported'}).encode())
            return

        # Use environment variable (better practice)
        APIFY_TOKEN = os.environ.get('APIFY_TOKEN', 'apify_api_qt1Mqt4thz8KaXh0uQBkquhGNdUYPB0acxhY')
        
        if not APIFY_TOKEN:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'APIFY_TOKEN not configured'}).encode())
            return

        try:
            # Call Apify API
            apify_response = requests.post(
                'https://api.apify.com/v2/acts/elis~instagram-downloader-api/runs?waitForFinish=120',
                headers={
                    'Authorization': f'Bearer {APIFY_TOKEN}',
                    'Content-Type': 'application/json'
                },
                json={
                    'url': [url]
                },
                timeout=130
            )

            if apify_response.status_code != 200:
                self.send_response(apify_response.status_code)
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': 'Apify API error',
                    'details': apify_response.text
                }).encode())
                return

            data = apify_response.json()
            
            # Extract dataset ID and fetch results
            dataset_id = data.get('data', {}).get('defaultDatasetId')
            results = []
            
            if dataset_id:
                dataset_response = requests.get(
                    f'https://api.apify.com/v2/datasets/{dataset_id}/items',
                    headers={
                        'Authorization': f'Bearer {APIFY_TOKEN}'
                    },
                    timeout=30
                )
                
                if dataset_response.status_code == 200:
                    results = dataset_response.json()
            else:
                # Direct results from run
                results = data.get('data', {}).get('datasetItems', [])

            # Format response
            formatted_results = []
            for item in results:
                formatted_results.append({
                    'inputUrl': item.get('inputUrl', url),
                    'platform': item.get('platform', 'instagram'),
                    'result': item.get('result', item.get('media', []))
                })

            response_data = {
                'success': True,
                'url': url,
                'data': formatted_results
            }

            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())

        except requests.exceptions.Timeout:
            self.send_response(504)
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Request timeout'}).encode())
        
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            }).encode())