from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from  google.auth.transport.requests import Request
import json

class YouTubeService:
    def __init__(self, client_secret_file, credentials_file, playlist_id):
        self.scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
        self.api_service_name = "youtube"
        self.api_version = "v3"
        self.client_secret_file = client_secret_file
        self.credentials_file = credentials_file
        self.playlist_id = playlist_id
        self.TOKEN_FILE="configs/token.json"
        self.youtube = self.get_authenticated_service()

    def get_authenticated_service(self):
        credentials = None
        try:
            with open(self.TOKEN_FILE, "r") as token:
                credentials = Credentials.from_authorized_user_info(json.load(token))
        except:
            try:
                print("self.client_secret_file")
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.scopes)
                credentials = flow.run_local_server(port=0)
                with open(self.TOKEN_FILE, "w") as token:
                    token.write(credentials.to_json())
            except:
                print("Unaible to initialize youtube")
                raise  
        return build(self.api_service_name, self.api_version, credentials=credentials)


    def add_video_to_playlist(self, youtube_video_url):
        """
        Adds a video to the YouTube playlist in FIFO order.

        Parameters:
        -----------
        youtube_video_url : str
            The full URL of the YouTube video to be added.

        Returns:
        --------
        dict
            The response from the YouTube Data API after inserting the video.

        Behavior:
        ---------
        This function extracts the video ID from the provided URL and appends it to 
        the playlist associated with `self.playlist_id`. The video is added at the 
        end of the playlist, which ensures a FIFO order of playback (i.e., videos 
        will play in the same order they were added). No manual position is set, 
        relying on YouTube's default behavior to append at the end.
        """
        video_id = self.extract_video_id(youtube_video_url)
        print(self.playlist_id)

        request = self.youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": self.playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id
                    }
                }
            }
        )
        response = request.execute()
        return response

    @staticmethod
    def extract_video_id(url):
        import re
        match = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", url)
        if match:
            return match.group(1)
        raise ValueError(f"Invalid YouTube URL: {url}")
