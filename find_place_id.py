#!/usr/bin/env python3
"""
Find Google Place ID for a location
This helps you find the Place ID to use with the Street View uploader

RECOMMENDED: Use Google's official Place ID Finder instead:
https://developers.google.com/maps/documentation/javascript/examples/places-placeid-finder

This script is provided as an alternative method when the official tool isn't available.
"""

import sys
import json
import argparse
import requests
from urllib.parse import quote

def search_place(query, api_key=None):
    """Search for a place and return potential matches with Place IDs"""
    
    if not api_key:
        print("Note: For better results, you can use a Google Maps API key")
        print("Without an API key, using alternative method...\n")
        
        # Alternative: Use Google Maps search URL
        search_url = f"https://www.google.com/maps/search/{quote(query)}"
        print(f"Open this URL in your browser to find the place:")
        print(f"{search_url}")
        print("\nOnce you find the place on Google Maps:")
        print("1. Click on the place to select it")
        print("2. Click the 'Share' button")
        print("3. Click 'Embed a map' tab")
        print("4. Look in the iframe src URL for 'place_id=ChIJ...'")
        print("5. That's your Place ID!")
        return []
    
    # Try the new Places API first
    print("Attempting to use Places API (New)...")
    base_url = "https://places.googleapis.com/v1/places:searchText"
    
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': api_key,
        'X-Goog-FieldMask': 'places.id,places.displayName,places.formattedAddress,places.types'
    }
    
    data = {
        'textQuery': query
    }
    
    try:
        response = requests.post(base_url, headers=headers, json=data)
        result = response.json()
        
        if 'error' in result:
            print(f"Places API (New) Error: {result['error'].get('message', 'Unknown error')}")
            print("\nTrying legacy API...")
            
            # Fall back to legacy API
            legacy_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
            params = {
                'input': query,
                'inputtype': 'textquery',
                'fields': 'place_id,name,formatted_address,types',
                'key': api_key
            }
            
            response = requests.get(legacy_url, params=params)
            data = response.json()
            
            if data.get('status') != 'OK':
                print(f"Error: {data.get('status')}")
                if data.get('error_message'):
                    print(f"Message: {data.get('error_message')}")
                    print("\nTo fix this error:")
                    print("1. Go to https://console.cloud.google.com/")
                    print("2. Select your project")
                    print("3. Go to 'APIs & Services' → 'Library'")
                    print("4. Search for 'Places API' and enable it")
                    print("5. Also enable 'Places API (New)' if available")
                return []
            
            results = []
            for place in data.get('candidates', []):
                results.append({
                    'name': place.get('name', 'Unknown'),
                    'address': place.get('formatted_address', 'No address'),
                    'place_id': place.get('place_id', 'No ID'),
                    'types': place.get('types', [])
                })
            return results
        
        # Process new API results
        results = []
        for place in result.get('places', [])[:5]:
            place_id = place.get('id', '').replace('places/', '')  # Remove prefix
            results.append({
                'name': place.get('displayName', {}).get('text', 'Unknown'),
                'address': place.get('formattedAddress', 'No address'),
                'place_id': place_id,
                'types': place.get('types', [])
            })
        
        return results
        
    except Exception as e:
        print(f"Error searching for place: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(
        description='Find Google Place IDs for use with Street View uploads',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Search without API key (provides instructions)
  %(prog)s "Golden Gate Bridge"
  
  # Search with API key (provides direct results)
  %(prog)s "Eiffel Tower Paris" --api-key YOUR_API_KEY
  
  # Search for specific address
  %(prog)s "123 Main Street, San Francisco, CA"
        ''')
    
    parser.add_argument('query', help='Place name or address to search for')
    parser.add_argument('--api-key', help='Google Maps API key (optional)')
    
    args = parser.parse_args()
    
    print(f"Searching for: {args.query}\n")
    
    results = search_place(args.query, args.api_key)
    
    if results:
        print("Found places:\n")
        for i, place in enumerate(results, 1):
            print(f"{i}. {place['name']}")
            print(f"   Address: {place['address']}")
            print(f"   Place ID: {place['place_id']}")
            print(f"   Types: {', '.join(place['types'][:3])}")
            print()
        
        print("\nTo use a Place ID with the uploader:")
        print("python streetview_uploader.py image.jpg --place-id PLACE_ID_HERE")

if __name__ == '__main__':
    main()