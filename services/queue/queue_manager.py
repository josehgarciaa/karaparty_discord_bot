from collections import deque
from datetime import datetime
from typing import Optional

class QueueManager:
    """
    Manages the live song queue on a per-team basis. Songs are added, removed,
    or replaced based on the team (typically, the channel name). Once a song is
    dispatched, it is marked as immutable.
    """

    def __init__(self) -> None:
        # Each team (channel name) maps to a deque (FIFO) of song entries.
        self.queues: dict[str, deque] = {}
        # Maintains round-robin order for teams with pending songs.
        self.team_order: deque[str] = deque()
        # Tracks dispatched songs to prevent further changes.
        self._dispatched: set[tuple[str, str]] = set()  # (team, link)

    def add_link(self, link: str, team: str, timestamp: Optional[datetime] = None) -> None:
        """
        Adds a song link to the queue for the specified team.
        
        Args:
            link (str): The YouTube link to be added.
            team (str): The team name (or channel name) that the song is associated with.
            timestamp (datetime, optional): The time the song was submitted. Defaults to UTC time.
        """
        print(f"[add_link] Attempting to add: {link} for team: {team}")
        if team not in self.queues:
            print(f"[add_link] Team '{team}' not in queues. Initializing.")
            self.queues[team] = deque()
            self.team_order.append(team)
            print(f"[add_link] Updated team_order: {self.team_order}")
        
        entry = {
            "team": team,
            "link": link,
            "timestamp": (timestamp or datetime.utcnow()).strftime("%Y-%m-%d %H:%M")
        }
        self.queues[team].append(entry)
        print(f"[add_link] Added entry to team '{team}': {entry}")
        print(f"[add_link] Current queue for team '{team}': {list(self.queues[team])}")


    def get_link(self) -> Optional[dict]:
        """
        Retrieves and removes the next song from the queue using round-robin ordering.
        
        Returns:
            Optional[dict]: The next song entry, or None if no songs are pending.
        """
        print(f"[get_link] Starting retrieval. Current team_order: {self.team_order}")
        while self.team_order:
            team = self.team_order[0]
            print(f"[get_link] Checking team '{team}'")
            
            if self.queues[team]:
                song = self.queues[team].popleft()
                print(f"[get_link] Returning song from team '{team}': {song}")
                self.team_order.rotate(-1)
                print(f"[get_link] Rotated team_order: {self.team_order}")
                return song
            else:
                print(f"[get_link] No songs left in team '{team}'. Removing team from rotation.")
                self.team_order.popleft()
        print("[get_link] No songs left in any team.")
        return None


    def is_empty(self) -> bool:
        """
        Checks if all team queues are empty.
        
        Returns:
            bool: True if no team has pending songs; False otherwise.
        """
        return all(len(q) == 0 for q in self.queues.values())


    def is_dispatched(self, link: str, team: str) -> bool:
        """
        Checks whether the specified song has already been dispatched.
        
        Args:
            link (str): The YouTube link.
            team (str): The team name.
        
        Returns:
            bool: True if the song is marked as dispatched; otherwise False.
        """
        return (team, link) in self._dispatched

    def mark_dispatched(self, link: str, team: str) -> None:
        """
        Marks the specified song as dispatched, making it immutable for further changes.
        
        Args:
            link (str): The YouTube link.
            team (str): The team name.
        """
        self._dispatched.add((team, link))
