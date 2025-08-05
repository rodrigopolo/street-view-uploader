# Google Street View 360 Image Uploader

Upload 360° equirectangular images to Google Street View using the Street View Publish API.

## Prerequisites

1. **Google Cloud Project** with Street View Publish API enabled
2. **OAuth2 Credentials** from Google Cloud Console
3. **Python 3.8+** installed
4. **ExifTool** installed (for adding Photo Sphere metadata)

## Setup Instructions

### 1. Install ExifTool

```bash
# macOS
brew install exiftool

# Ubuntu/Debian
sudo apt-get install exiftool

# Windows
# Download from https://exiftool.org/
```

### 2. Set Up Google Cloud Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the **Street View Publish API**:
   - Go to "APIs & Services" → "Library"
   - Search for "Street View Publish API"
   - Click and enable it
4. Create OAuth2 credentials:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Choose "Desktop app" as application type
   - Download the credentials JSON file
5. Save the credentials as `credentials.json` in this directory

### 3. Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Image Requirements

### Photo Specifications

- **Format**: JPEG (.jpg or .jpeg)
- **Type**: Equirectangular projection
- **Aspect Ratio**: 2:1 (width should be twice the height)
- **Recommended Resolution**: 
  - Minimum: 2048 x 1024 pixels
  - Optimal: 8192 x 4096 pixels or higher
- **Field of View**: 360° x 180° (full sphere)

### Required Metadata

Google Street View requires specific Photo Sphere XMP metadata. Use the provided script to add it:

```bash
./add_360_metadata.sh your-360-image.jpg
```

This adds the following essential metadata:
- `UsePanoramaViewer="True"` (enables panoramic viewing)
- `ProjectionType="equirectangular"`
- Image dimensions and crop information
- Initial viewing angle

## Usage

### Basic Upload

```bash
# Activate virtual environment
source venv/bin/activate

# Upload a single image (uses GPS from EXIF if available)
python streetview_uploader.py path/to/your-360-image.jpg
```

### Upload with Location

```bash
# Specify exact coordinates
python streetview_uploader.py image.jpg --lat 37.7749 --lng -122.4194

# Include altitude
python streetview_uploader.py image.jpg --lat 37.7749 --lng -122.4194 --alt 10.5

# Add compass heading (0-360 degrees, 0=North)
python streetview_uploader.py image.jpg --lat 37.7749 --lng -122.4194 --heading 45

# Associate with a specific place
python streetview_uploader.py image.jpg --place-id ChIJIQBpAG2ahYAR_6128GcTUEo
```

### Finding Google Place IDs

To avoid "Unknown place" in your uploads, you have several options:

#### Option 1: Google's Official Place ID Finder (Recommended)

1. Open Google's Place ID Finder: https://developers.google.com/maps/documentation/javascript/examples/places-placeid-finder
2. Search for your location in the search box
3. Click on the marker that appears on the map
4. Copy the Place ID from the info window
5. Use it with the uploader: `python streetview_uploader.py image.jpg --place-id YOUR_PLACE_ID`

#### Option 2: Using the Included Helper Script

```bash
# Search for a place (provides instructions)
python find_place_id.py "Golden Gate Bridge"

# With Google Maps API key (provides direct results)
python find_place_id.py "Eiffel Tower" --api-key YOUR_API_KEY
```

#### Option 3: Extract from Google Maps URL

```bash
# If you have a Google Maps URL
python extract_place_id.py "https://www.google.com/maps/place/..."
```

### First Time Authentication

On first run:
1. A browser window will open for Google authentication
2. Log in with your Google account
3. Grant permissions to the app
4. The authentication token will be saved in `token.json`

### Command Line Options

```bash
# Location options
--lat, --latitude     Latitude in decimal degrees
--lng, --longitude    Longitude in decimal degrees  
--alt, --altitude     Altitude in meters above sea level
--heading            Compass heading in degrees (0-360)
--place-id           Google Place ID to associate with photo

# File options
--credentials        Path to credentials.json file
--token             Path to token.json file
```

## Workflow Example

```bash
# 1. Prepare your 360° image
# Ensure it's equirectangular with 2:1 aspect ratio

# 2. Add Photo Sphere metadata
./add_360_metadata.sh my-360-photo.jpg

# 3. Upload to Street View
source venv/bin/activate
python streetview_uploader.py my-360-photo.jpg

# Output:
# ✓ Photo uploaded successfully!
#   Photo ID: CAoSK0FGMVFpcE5Y...
#   Share link: https://maps.google.com/maps/...
```

## Troubleshooting

### "The image is not a 360 photo" Error

This error occurs when the image lacks proper Photo Sphere metadata. Solution:
```bash
./add_360_metadata.sh your-image.jpg
```

### Authentication Issues

- Delete `token.json` and re-authenticate
- Ensure Street View Publish API is enabled in your Google Cloud project
- Check that your OAuth2 credentials are for a "Desktop app" type

### Module Not Found Errors

Ensure you've activated the virtual environment:
```bash
source venv/bin/activate
```

### Image Requirements Not Met

Verify your image:
```bash
# Check dimensions and format
exiftool -ImageWidth -ImageHeight -FileType your-image.jpg

# Check if metadata was added
exiftool -XMP-GPano:all your-image.jpg
```

## Files in This Project

- `streetview_uploader.py` - Main upload script with location support
- `add_360_metadata.sh` - Script to add Photo Sphere metadata
- `find_place_id.py` - Helper to find Google Place IDs
- `requirements.txt` - Python dependencies
- `credentials.json` - Google OAuth2 credentials (you create this)
- `token.json` - Authentication token (auto-generated)
- `venv/` - Python virtual environment (created during setup)

## Security Notes

- Keep `credentials.json` and `token.json` private
- Don't commit these files to version control
- Add them to `.gitignore` if using Git

## Additional Resources

- [Google Street View Publish API Documentation](https://developers.google.com/streetview/publish)
- [Photo Sphere XMP Metadata Specification](https://developers.google.com/streetview/spherical-metadata)
- [ExifTool Documentation](https://exiftool.org/)