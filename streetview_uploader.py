#!/usr/bin/env python3
"""
Google Street View 360 Image Uploader
Uploads 360 equirectangular images to Google Street View using the Publish API
"""

import os
import sys
import json
import argparse
from pathlib import Path
import mimetypes

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import requests

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/streetviewpublish']

class StreetViewUploader:
    def __init__(self, credentials_file='credentials.json', token_file='token.json'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.creds = None
        
    def authenticate(self):
        """Handles OAuth2 authentication flow"""
        # Token file stores the user's access and refresh tokens
        if os.path.exists(self.token_file):
            self.creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        
        # If there are no (valid) credentials available, let the user log in
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                print("Refreshing authentication token...")
                self.creds.refresh(Request())
            else:
                print("Starting authentication flow...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(self.token_file, 'w') as token:
                token.write(self.creds.to_json())
                
        # Build the Street View Publish API service
        self.service = build('streetviewpublish', 'v1', credentials=self.creds)
        print("Authentication successful!")
        
    def get_exif_data(self, image_path):
        """Extract GPS and datetime data from image EXIF"""
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS, GPSTAGS
            
            image = Image.open(image_path)
            exifdata = image.getexif()
            
            # Get capture time from EXIF
            capture_time = None
            for tag_id, value in exifdata.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == "DateTime":
                    # Convert EXIF datetime to timestamp
                    from datetime import datetime
                    dt = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                    capture_time = int(dt.timestamp())
                    break
            
            # Get GPS data
            gps_data = {}
            for tag_id, value in exifdata.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == "GPSInfo":
                    for gps_tag_id, gps_value in value.items():
                        gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                        gps_data[gps_tag] = gps_value
            
            # Convert GPS coordinates to decimal degrees
            latitude = None
            longitude = None
            altitude = None
            
            if gps_data:
                # Latitude
                if 'GPSLatitude' in gps_data and 'GPSLatitudeRef' in gps_data:
                    lat = gps_data['GPSLatitude']
                    lat_ref = gps_data['GPSLatitudeRef']
                    latitude = (lat[0] + lat[1]/60 + lat[2]/3600) * (-1 if lat_ref == 'S' else 1)
                
                # Longitude
                if 'GPSLongitude' in gps_data and 'GPSLongitudeRef' in gps_data:
                    lon = gps_data['GPSLongitude']
                    lon_ref = gps_data['GPSLongitudeRef']
                    longitude = (lon[0] + lon[1]/60 + lon[2]/3600) * (-1 if lon_ref == 'W' else 1)
                
                # Altitude
                if 'GPSAltitude' in gps_data:
                    altitude = float(gps_data['GPSAltitude'])
            
            return {
                'capture_time': capture_time,
                'latitude': latitude,
                'longitude': longitude,
                'altitude': altitude
            }
            
        except Exception as e:
            print(f"Warning: Could not extract EXIF data: {e}")
            return {}
    
    def upload_photo(self, image_path, latitude=None, longitude=None, altitude=None, 
                     heading=None, place_id=None):
        """Uploads a 360 photo to Google Street View with location data"""
        # Validate file exists and is a JPG
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
            
        mime_type, _ = mimetypes.guess_type(image_path)
        if mime_type not in ['image/jpeg', 'image/jpg']:
            raise ValueError(f"File must be a JPEG image. Got: {mime_type}")
            
        file_size = os.path.getsize(image_path)
        print(f"Uploading image: {image_path} ({file_size:,} bytes)")
        
        # Extract EXIF data
        exif_data = self.get_exif_data(image_path)
        
        # Use provided coordinates or fall back to EXIF
        if latitude is None:
            latitude = exif_data.get('latitude')
        if longitude is None:
            longitude = exif_data.get('longitude')
        if altitude is None:
            altitude = exif_data.get('altitude')
            
        capture_time = exif_data.get('capture_time', int(os.path.getmtime(image_path)))
        
        try:
            # Step 1: Start upload to get an upload URL
            print("Requesting upload URL...")
            upload_ref = self.service.photo().startUpload(body={}).execute()
            upload_url = upload_ref['uploadUrl']
            
            # Step 2: Upload the photo bytes to the upload URL
            print("Uploading image data...")
            with open(image_path, 'rb') as photo_file:
                photo_bytes = photo_file.read()
                
            headers = {
                'Authorization': f'Bearer {self.creds.token}',
                'Content-Type': 'image/jpeg',
                'X-Goog-Upload-Protocol': 'raw',
                'X-Goog-Upload-Content-Length': str(len(photo_bytes))
            }
            
            response = requests.post(upload_url, data=photo_bytes, headers=headers)
            
            if response.status_code != 200:
                raise Exception(f"Upload failed with status {response.status_code}: {response.text}")
                
            # Step 3: Create the photo with metadata
            print("Creating photo entry...")
            photo_body = {
                'uploadReference': {
                    'uploadUrl': upload_url
                },
                'captureTime': {
                    'seconds': capture_time
                }
            }
            
            # Add pose (location) data if available
            if latitude is not None and longitude is not None:
                pose = {
                    'latLngPair': {
                        'latitude': latitude,
                        'longitude': longitude
                    }
                }
                if altitude is not None:
                    pose['altitude'] = altitude
                if heading is not None:
                    pose['heading'] = heading
                    
                photo_body['pose'] = pose
                print(f"  Location: {latitude:.6f}, {longitude:.6f}")
                if altitude:
                    print(f"  Altitude: {altitude:.1f}m")
                if heading:
                    print(f"  Heading: {heading:.1f}°")
            
            # Add place association if provided
            if place_id:
                photo_body['places'] = [{
                    'placeId': place_id
                }]
                print(f"  Place ID: {place_id}")
            
            created_photo = self.service.photo().create(body=photo_body).execute()
            
            print(f"✓ Photo uploaded successfully!")
            print(f"  Photo ID: {created_photo.get('photoId', {}).get('id', 'N/A')}")
            print(f"  Share link: {created_photo.get('shareLink', 'N/A')}")
            print(f"  View count: {created_photo.get('viewCount', 0)}")
            
            return created_photo
            
        except HttpError as error:
            print(f"✗ An HTTP error occurred: {error}")
            raise
        except Exception as error:
            print(f"✗ An error occurred: {error}")
            raise

def main():
    parser = argparse.ArgumentParser(
        description='Upload 360 equirectangular images to Google Street View',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Basic upload (uses GPS from EXIF if available)
  %(prog)s image.jpg
  
  # Upload with specific coordinates
  %(prog)s image.jpg --lat 37.7749 --lng -122.4194
  
  # Upload with coordinates and altitude
  %(prog)s image.jpg --lat 37.7749 --lng -122.4194 --alt 10.5
  
  # Upload with heading (compass direction)
  %(prog)s image.jpg --lat 37.7749 --lng -122.4194 --heading 45
  
  # Upload with Google Place ID
  %(prog)s image.jpg --place-id ChIJIQBpAG2ahYAR_6128GcTUEo
        ''')
    parser.add_argument('image', help='Path to the JPG image to upload')
    parser.add_argument('--credentials', default='credentials.json',
                        help='Path to credentials.json file (default: credentials.json)')
    parser.add_argument('--token', default='token.json',
                        help='Path to token.json file (default: token.json)')
    parser.add_argument('--lat', '--latitude', type=float, dest='latitude',
                        help='Latitude in decimal degrees (e.g., 37.7749)')
    parser.add_argument('--lng', '--longitude', type=float, dest='longitude',
                        help='Longitude in decimal degrees (e.g., -122.4194)')
    parser.add_argument('--alt', '--altitude', type=float, dest='altitude',
                        help='Altitude in meters above sea level')
    parser.add_argument('--heading', type=float,
                        help='Compass heading in degrees (0-360, 0=North)')
    parser.add_argument('--place-id', dest='place_id',
                        help='Google Place ID to associate with the photo')
    
    args = parser.parse_args()
    
    # Validate coordinate pairs
    if (args.latitude is None) != (args.longitude is None):
        parser.error("Both --lat and --lng must be provided together")
    
    # Initialize uploader
    uploader = StreetViewUploader(
        credentials_file=args.credentials,
        token_file=args.token
    )
    
    try:
        # Authenticate
        uploader.authenticate()
        
        # Upload the photo
        result = uploader.upload_photo(
            args.image,
            latitude=args.latitude,
            longitude=args.longitude,
            altitude=args.altitude,
            heading=args.heading,
            place_id=args.place_id
        )
        
        print("\n✓ Upload completed successfully!")
        
    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()