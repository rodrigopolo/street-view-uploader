#!/bin/bash

# Script to add complete Google Photo Sphere XMP metadata to 360 images

if [ $# -eq 0 ]; then
    echo "Usage: $0 <image.jpg>"
    exit 1
fi

IMAGE="$1"

# Get image dimensions
WIDTH=$(exiftool -s -s -s -ImageWidth "$IMAGE")
HEIGHT=$(exiftool -s -s -s -ImageHeight "$IMAGE")

echo "Adding Photo Sphere metadata to: $IMAGE"
echo "Image dimensions: ${WIDTH}x${HEIGHT}"

# Add all required GPano metadata
exiftool \
-overwrite_original \
-XMP-GPano:UsePanoramaViewer="True" \
-XMP-GPano:ProjectionType="equirectangular" \
-XMP-GPano:CroppedAreaImageWidthPixels="$WIDTH" \
-XMP-GPano:CroppedAreaImageHeightPixels="$HEIGHT" \
-XMP-GPano:FullPanoWidthPixels="$WIDTH" \
-XMP-GPano:FullPanoHeightPixels="$HEIGHT" \
-XMP-GPano:CroppedAreaLeftPixels="0" \
-XMP-GPano:CroppedAreaTopPixels="0" \
-XMP-GPano:PoseHeadingDegrees="0" \
-XMP-GPano:InitialViewHeadingDegrees="0" \
-XMP-GPano:StitchingSoftware="Custom" \
"$IMAGE"

echo "✓ Photo Sphere metadata added successfully!"