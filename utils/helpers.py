def is_song_in_team(self, team: str, link: str) -> bool:
    return team in self.queues and any(song["link"] == link for song in self.queues[team])

def remove_song_from_team(self, team: str, link: str) -> bool:
    if team in self.queues:
        for i, song in enumerate(self.queues[team]):
            if song["link"] == link:
                del self.queues[team][i]
                return True
    return False

def replace_song_in_team(self, team: str, old_link: str, new_link: str) -> bool:
    if team in self.queues:
        for song in self.queues[team]:
            if song["link"] == old_link:
                song["link"] = new_link
                return True
    return False

# Track dispatched links to lock them
def is_dispatched(self, link: str, team: str) -> bool:
    return getattr(self, "_dispatched", {}).get((team, link), False)

def mark_dispatched(self, link: str, team: str) -> None:
    if not hasattr(self, "_dispatched"):
        self._dispatched = {}
    self._dispatched[(team, link)] = True
