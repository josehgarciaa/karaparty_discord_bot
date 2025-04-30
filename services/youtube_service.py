import json
import time
import re
from pathlib import Path
from typing import Optional

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# ──────────────────────────────────────────────────────────
# 🌟  bring in YOUR logger helper
#     (assuming it lives next to this file; adjust the import if not)
# ──────────────────────────────────────────────────────────
from utils.logger import get_logger
logger = get_logger(__name__)                        # one logger for this whole file


class YouTubeService:
    """
    Thin wrapper around the YouTube Data API v3 that
    handles OAuth, token refresh and playlist insertion.

    All high-level operations emit INFO-level messages so you
    get a running commentary of what’s happening; recoverable
    problems are WARN, hard failures are ERROR.
    """

    SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
    API_SERVICE_NAME = "youtube"
    API_VERSION = "v3"
    TOKEN_FILE = Path("configs/token.json")

    # ───────────────────────────────────────────────
    #  constructor
    # ───────────────────────────────────────────────
    def __init__(
        self,
        client_secret_file: str,
        credentials_file: str,
        playlist_id: str,
    ) -> None:

        self.client_secret_file = client_secret_file
        self.credentials_file = credentials_file
        self.playlist_id = playlist_id

        logger.info("🎬  Initialising YouTubeService for playlist %s", playlist_id)
        self.youtube = self._get_authenticated_service()
        logger.info("✅  YouTube client ready")

    # ───────────────────────────────────────────────
    #  (private) authentication helper
    # ───────────────────────────────────────────────
    def _get_authenticated_service(self):
        credentials: Optional[Credentials] = None

        # 1. Try cached token
        if self.TOKEN_FILE.exists():
            logger.debug("Attempting to read cached credentials from %s", self.TOKEN_FILE)
            try:
                with self.TOKEN_FILE.open("r", encoding="utf-8") as fh:
                    credentials = Credentials.from_authorized_user_info(json.load(fh))
            except Exception as exc:
                logger.warning(
                    "Cached token found but could not be loaded (%s). "
                    "Will trigger OAuth flow.", exc
                )

        # 2. Trigger OAuth flow if needed
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                logger.info("🔄  Refreshing expired credentials…")
                try:
                    credentials.refresh(Request())
                except Exception as exc:
                    logger.error("Token refresh failed, falling back to full auth: %s", exc)
                    credentials = None   # force a new flow

            if not credentials:
                # a short print so you instantly notice that a browser is about to open
                print("\n=== Launching Google OAuth flow in your browser… ===\n")
                logger.info("Starting InstalledAppFlow using %s", self.client_secret_file)
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secret_file,
                    self.SCOPES,
                )
                credentials = flow.run_local_server(port=0)

                # persist for next time
                self.TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
                with self.TOKEN_FILE.open("w", encoding="utf-8") as fh:
                    fh.write(credentials.to_json())
                logger.info("New credentials saved to %s", self.TOKEN_FILE)

        # 3. Build API client
        logger.debug("Building YouTube discovery client")
        return build(self.API_SERVICE_NAME, self.API_VERSION, credentials=credentials)

    # ───────────────────────────────────────────────
    #  public API
    # ───────────────────────────────────────────────
    def add_video_to_playlist(self, youtube_video_url: str):
        """
        Append a video to the end of the playlist (FIFO order).

        Parameters
        ----------
        youtube_video_url : str
            Full YouTube URL, e.g. https://youtu.be/dQw4w9WgXcQ

        Returns
        -------
        dict
            Raw API response from playlistItems.insert
        """
        video_id = self._extract_video_id(youtube_video_url)
        logger.info("📥  Queuing video %s (%s) for playlist %s",
                    video_id, youtube_video_url, self.playlist_id)

        request = self.youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": self.playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id,
                    },
                },
            },
        )

        try:
            response = request.execute()
            logger.info("✅  Video %s successfully added (playlistItems id=%s)",
                        video_id, response.get("id"))
        except Exception as exc:
            logger.error("❌  Failed to add video %s to playlist: %s", video_id, exc)
            raise

        # be kind to the API quotas
        time.sleep(1)
        return response

    # ───────────────────────────────────────────────
    #  helpers
    # ───────────────────────────────────────────────
    @staticmethod
    def _extract_video_id(url: str) -> str:
        """
        Robust extractor that works for both full URLs and short youtu.be links.
        """
        match = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", url)
        if match:
            return match.group(1)
        logger.error("Invalid YouTube URL supplied: %s", url)
        raise ValueError(f"Invalid YouTube URL: {url}")
