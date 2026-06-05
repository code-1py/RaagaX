from yt_dlp import YoutubeDL
from backend.logger import logger
from yt_dlp.utils import DownloadError , ExtractorError , GeoRestrictedError , UnavailableVideoError , UserNotLive
from urllib.error import URLError
from http.client import RemoteDisconnected
import traceback

def get_playlist_info(url)-> dict:
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

        entries = info.get("entries") # Check if it's a playlist

        if entries:
            return {
                "is_playlist": True,
                "count": len(entries),
                "title": info.get("title")
            }

        return {
            "is_playlist": False,
            "count": 1,
            "title": info.get("title")
        }
    
def get_songs_info(url)-> dict[bool, str | list[dict[str, str | bool]]]:
    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
     
            entries = info.get("entries", [info])  # playlist = multiple, single = wrap in list
     
            return True , [
                {
                    "url": entry["url"],
                    "title": entry["title"],
                    "thumbnail": entry["thumbnail"],
                    "acodec": entry.get("acodec"),
                    "vcodec": entry.get("vcodec"),
                    "has_audio": entry.get("acodec") != "none",
                    "has_video": entry.get("vcodec") != "none",
                    "protocol": entry.get("protocol"),
                }
                for entry in entries
            ]
    except (DownloadError, ExtractorError, GeoRestrictedError, UnavailableVideoError, UserNotLive) as e:
        logger.error(f"Error extracting info for URL {url}: {e}")
        
        error_message = str(e)
        if "This video is unavailable" in error_message:
            return False , "Video is unavailable"
        elif "This video is private" in error_message:
            return False , "Audio is private"
        elif "This video is age restricted" in error_message:
            return False , "Audio is age restricted"
        elif "This video is not available in your country" in error_message:
            return False , "Audio is not available in your country"
        elif "This live stream recording is not available" in error_message:
            return False , "This is a live stream recording and is not available"
        else:
            return False , "An error occurred while processing the audio"
    except (URLError, RemoteDisconnected) as e:
        logger.error(f"Network error while extracting info for URL {url}: {traceback.format_exc()}")
        return False , "A network error occurred while processing the audio"
    except Exception as e:
        logger.error(f"Unexpected error while extracting info for URL {url}: {traceback.format_exc()}")
        return False , "An unexpected error occurred while processing the audio"