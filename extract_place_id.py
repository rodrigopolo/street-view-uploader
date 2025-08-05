#!/usr/bin/env python3
"""
Extract Google Place ID from a Google Maps URL

EASIER METHOD: Use Google's official Place ID Finder:
https://developers.google.com/maps/documentation/javascript/examples/places-placeid-finder

This script helps extract place information from existing Google Maps URLs
when you already have a location URL but need the proper Place ID format.
"""

import sys
import re
from urllib.parse import unquote

def extract_place_id_from_url(url):
    """Extract Place ID from various Google Maps URL formats"""
    
    # Decode URL
    url = unquote(url)
    
    # Method 1: Look for place ID in data parameter (format: !1s{place_id})
    match = re.search(r'!1s(0x[a-fA-F0-9]+:[a-fA-F0-9x]+)', url)
    if match:
        hex_id = match.group(1)
        print(f"Found hex Place ID: {hex_id}")
        
        # Note: Google's internal hex format needs to be converted to the standard format
        # This is complex and requires Google's API to properly convert
        print("\nTo get the proper Place ID:")
        print("1. Open the URL in your browser")
        print("2. Click on the place name/title")
        print("3. Click 'Share' button")
        print("4. Click 'Embed a map' tab")
        print("5. The Place ID will be in the iframe src URL")
        return None
    
    # Method 2: Look for place ID in newer URL format
    match = re.search(r'/place/[^/]+/[^/]+/data=[^/]*place_id:([^&]+)', url)
    if match:
        return match.group(1)
    
    # Method 3: Look for standard Place ID format (ChIJ...)
    match = re.search(r'(ChIJ[a-zA-Z0-9_-]{22})', url)
    if match:
        return match.group(1)
    
    return None

def get_place_details_from_url(url):
    """Extract place name and coordinates from URL"""
    details = {}
    
    # Extract place name
    match = re.search(r'/place/([^/@]+)', url)
    if match:
        place_name = unquote(match.group(1).replace('+', ' '))
        details['name'] = place_name
    
    # Extract coordinates
    match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
    if match:
        details['latitude'] = float(match.group(1))
        details['longitude'] = float(match.group(2))
    
    return details

def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_place_id.py <google-maps-url>")
        print("\nExample:")
        print('python extract_place_id.py "https://www.google.com/maps/place/..."')
        sys.exit(1)
    
    url = sys.argv[1]
    print(f"Analyzing URL...\n")
    
    # Extract place details
    details = get_place_details_from_url(url)
    if details.get('name'):
        print(f"Place Name: {details['name']}")
    if details.get('latitude') and details.get('longitude'):
        print(f"Coordinates: {details['latitude']}, {details['longitude']}")
    
    # Try to extract Place ID
    place_id = extract_place_id_from_url(url)
    if place_id:
        print(f"\nPlace ID: {place_id}")
        print(f"\nUse with uploader:")
        print(f"python streetview_uploader.py image.jpg --place-id {place_id}")
    else:
        print("\n⚠️  Could not extract Place ID from this URL format.")
        print("\nAlternative: Use coordinates instead:")
        if details.get('latitude') and details.get('longitude'):
            print(f"python streetview_uploader.py image.jpg --lat {details['latitude']} --lng {details['longitude']}")
        else:
            print("Please try the find_place_id.py script with the place name instead.")

if __name__ == '__main__':
    main()