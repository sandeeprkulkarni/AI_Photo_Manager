# modules/metadata_extractor.py
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

def get_geotagging(exif):
    if not exif:
        return None
    geotagging = {}
    for (idx, tag) in TAGS.items():
        if tag == 'GPSInfo':
            if idx not in exif:
                return None
            for (key, val) in GPSTAGS.items():
                if key in exif[idx]:
                    geotagging[val] = exif[idx][key]
    return geotagging

def get_decimal_from_dms(dms, ref):
    degrees = dms[0]
    minutes = dms[1] / 60.0
    seconds = dms[2] / 3600.0
    if ref in ['S', 'W']:
        degrees = -degrees
        minutes = -minutes
        seconds = -seconds
    return degrees + minutes + seconds

def extract_gps(path):
    """Extracts Latitude and Longitude from photo path"""
    try:
        with Image.open(path) as img:
            exif = img._getexif()
            geotags = get_geotagging(exif)
            if geotags:
                lat = get_decimal_from_dms(geotags['GPSLatitude'], geotags['GPSLatitudeRef'])
                lon = get_decimal_from_dms(geotags['GPSLongitude'], geotags['GPSLongitudeRef'])
                return lat, lon
    except:
        pass
    return None, None