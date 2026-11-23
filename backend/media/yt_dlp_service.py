from yt_dlp import YoutubeDL
from backend.logger import logger
from yt_dlp.utils import DownloadError , ExtractorError , GeoRestrictedError , UnavailableVideoError , UserNotLive
from urllib.error import URLError
from http.client import RemoteDisconnected
import traceback
from urllib.parse import urlparse
from collections.abc import Iterator
from dataclasses import dataclass


class SongInfoError(Exception):
    pass


@dataclass(frozen=True)
class SongInfoFailure:
    title: str
    message: str


def _friendly_error_message(error: Exception) -> str:
    error_message = str(error)
    if "This video is unavailable" in error_message:
        return "Video is unavailable"
    if "This video is private" in error_message:
        return "Audio is private"
    if "This video is age restricted" in error_message:
        return "Audio is age restricted"
    if "This video is not available in your country" in error_message:
        return "Audio is not available in your country"
    if "This live stream recording is not available" in error_message:
        return "This is a live stream recording and is not available"
    return "An error occurred while processing the audio"


def normalize_input(text: str) -> str:
    try:
        parsed = urlparse(text)

        if parsed.scheme and parsed.netloc:
            return text

        return f"ytsearch1:{text}"

    except Exception:
        return f"ytsearch1:{text}"

def get_playlist_info(query: str) -> dict:
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        query = normalize_input(query)
        info = ydl.extract_info(query, download=False)

        entries = info.get("entries")

        # Real playlist has multiple entries
        if info.get("_type") == "playlist" and len(entries) > 1:
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
    
def iter_songs_info(
    url: str,
) -> Iterator[dict[str, str | bool | None] | SongInfoFailure]:
    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
        }

        with YoutubeDL(ydl_opts) as ydl:
            query = normalize_input(url)
            info = ydl.extract_info(query, download=False, process=False)
            if not info:
                return

            if "entries" in info:
                entries = info.get("entries") or ()
            else:
                entries = (info,)

            for entry in entries:
                if not entry:
                    continue
                title = str(entry.get("title") or "track")
                try:
                    resolved = ydl.process_ie_result(entry, download=False)
                    if not resolved:
                        yield SongInfoFailure(title, "No playable track information was returned")
                        continue
                    song = {
                        "url": resolved["url"],
                        "title": resolved["title"],
                        "thumbnail": resolved.get("thumbnail"),
                        "acodec": resolved.get("acodec"),
                        "vcodec": resolved.get("vcodec"),
                        "has_audio": resolved.get("acodec") != "none",
                        "has_video": resolved.get("vcodec") != "none",
                        "protocol": resolved.get("protocol"),
                    }
                except (DownloadError, ExtractorError, GeoRestrictedError, UnavailableVideoError, UserNotLive) as e:
                    logger.error(f"Error extracting playlist entry {title} for URL {url}: {e}")
                    yield SongInfoFailure(title, _friendly_error_message(e))
                    continue
                except (URLError, RemoteDisconnected) as e:
                    logger.error(f"Network error extracting playlist entry {title}: {traceback.format_exc()}")
                    yield SongInfoFailure(title, "A network error occurred while processing the audio")
                    continue
                except Exception:
                    logger.error(f"Unexpected error extracting playlist entry {title}: {traceback.format_exc()}")
                    yield SongInfoFailure(title, "An unexpected error occurred while processing the audio")
                    continue
                yield song
    except (DownloadError, ExtractorError, GeoRestrictedError, UnavailableVideoError, UserNotLive) as e:
        logger.error(f"Error extracting info for URL {url}: {e}")
        raise SongInfoError(_friendly_error_message(e)) from e
    except (URLError, RemoteDisconnected) as e:
        logger.error(f"Network error while extracting info for URL {url}: {traceback.format_exc()}")
        raise SongInfoError("A network error occurred while processing the audio") from e
    except Exception as e:
        logger.error(f"Unexpected error while extracting info for URL {url}: {traceback.format_exc()}")
        raise SongInfoError("An unexpected error occurred while processing the audio") from e


def get_songs_info(url: str) -> tuple[bool, str | list[dict[str, str | bool | None]]]:
    try:
        songs = []
        for item in iter_songs_info(url):
            if isinstance(item, SongInfoFailure):
                raise SongInfoError(item.message)
            songs.append(item)
        return True, songs
    except SongInfoError as e:
        return False, str(e)