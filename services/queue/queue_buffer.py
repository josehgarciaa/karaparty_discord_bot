# services/queue_buffer.py

from datetime import datetime
from typing import List, Dict, Any

class QueueBuffer:
    """
    A buffer layer that stages pending song operations in a single list.
    
    Each pending song is identified by a combination of a team (e.g., channel name)
    and a song link. This buffer supports three operations:
      - add_song: Schedules a new song to be added.
      - delete_song: Removes a pending song.
      - replace_song: Replaces a pending song's link.
    
    Each method returns a status object with:
      - "success": (bool) True if the operation was accepted.
      - "warning_type": (str) A code indicating the reason for rejection (empty string if successful).
    
    The apply_to method applies all pending songs to a live QueueManager,
    dispatching up to 3 songs for further processing, and then clears the buffer.
    """

    def __init__(self) -> None:
        # List of pending song operations; each is a dict with "team" and "link".
        self.pending: List[Dict[str, str]] = []
        self.dispatch_number = 3
        
    def set_dispatch_number(self, _dispatch_number):
        if _dispatch_number > 0 :
           self.dispatch_number = _dispatch_number
        

    def add_song(self, team: str, link: str) -> Dict[str, Any]:
        """
        Schedules a song to be added for the specified team.
        
        Args:
            team (str): The team (channel) identifier.
            link (str): The YouTube link to be added.
        
        Returns:
            dict: A status object with:
                  - "success" (bool): True if the song was successfully scheduled.
                  - "warning_type" (str): A code indicating the issue if not successful.
                  In this case, "duplicate_song" indicates the same addition is already scheduled.
        """
        # Check if the song is already pending.
        for entry in self.pending:
            if entry["team"] == team and entry["link"] == link:
                return {"success": False, "warning_type": "repeated_song"}
        self.pending.append({"team": team, "link": link})
        return {"success": True, "warning_type": ""}

    def delete_song(self, team: str, link: str) -> Dict[str, Any]:
        """
        Schedules deletion of a pending song.
        
        This operation removes the song from the pending list if present.
        
        Args:
            team (str): The team identifier.
            link (str): The YouTube link to be deleted.
        
        Returns:
            dict: A status object. If the song is not found in the pending list,
                  "warning_type" is set to "song_not_found".
        """
        for i, entry in enumerate(self.pending):
            if entry["team"] == team and entry["link"] == link:
                del self.pending[i]
                return {"success": True, "warning_type": ""}
        return {"success": False, "warning_type": "delete_dispatched_song"}

    def replace_song(self, team: str, old_link: str, new_link: str) -> Dict[str, Any]:
        """
        Schedules a replacement: changes an existing pending song's link to a new link.
        
        Args:
            team (str): The team identifier.
            old_link (str): The YouTube link to be replaced.
            new_link (str): The new YouTube link.
        
        Returns:
            dict: A status object. If the pending song is found, it is updated.
                  If not found, "warning_type" is set to "song_not_found".
        """
        for entry in self.pending:
            if entry["team"] == team and entry["link"] == old_link:
                entry["link"] = new_link
                return {"success": True, "warning_type": ""}
        return {"success": False, "warning_type": "edit_dispatched_song"}

    def apply_to(self, queue: Any) -> List[dict]:
        """
        Applies all pending song additions to the live queue, then dispatches up to 3 songs.
        
        The live queue (an instance of QueueManager) is expected to handle the round-robin 
        organization, dispatch operations, and marking of dispatched songs.
        
        Process:
          1. For each pending song, if it isn't already present in the live queue, add it.
          2. Dispatch up to 3 songs from the live queue.
          3. Clear the pending list.
        
        Args:
            queue: The live QueueManager instance.
        
        Returns:
            List[dict]: A list of song entries that were dispatched.
        """
        dispatched_songs: List[dict] = []

        # Add each pending song to the live queue (if not already added).
        for entry in self.pending:
            team = entry["team"]
            link = entry["link"]
            queue.add_link(link=link, team=team, timestamp=datetime.utcnow())

        # Dispatch up to 3 songs from the live queue.
        print("Dispatching ", self.dispatch_number, "songs")
        for _ in range(self.dispatch_number):
            song = queue.get_link()
            if song:
                dispatched_songs.append(song)
                queue.mark_dispatched(song["link"], song["team"])
            else:
                break

        # Clear the buffer after applying operations.
        self.pending.clear()

        return dispatched_songs
