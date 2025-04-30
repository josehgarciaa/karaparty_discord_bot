from collections import deque
from datetime import datetime
from typing import Optional, Dict, Deque

# Project‑wide logger helper
from utils.logger import get_logger

logger = get_logger(__name__)


class QueueManager:
    """Round‑robin song queue organised per Discord team/channel."""

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self) -> None:
        # Map «team» ➜ deque([song‑entry, …])
        self.queues: Dict[str, Deque[dict]] = {}
        # Ordered list of teams that currently have at least one pending song
        self.team_order: Deque[str] = deque()
        # Set of (team, link) tuples already dispatched (immutability guard)
        self._dispatched: set[tuple[str, str]] = set()

        logger.info("QueueManager initialised")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_link(
        self,
        link: str,
        team: str,
        *,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Enqueue *link* under *team*, ensuring the team is in the rotation."""

        logger.info("[add_link] Attempting to add %s for team '%s'", link, team)

        # Lazily create queue for brand‑new team
        if team not in self.queues:
            self.queues[team] = deque()
            logger.info("[add_link] Team '%s' initialised", team)

        # Guarantee team participates in the round‑robin exactly once
        if team not in self.team_order:
            self.team_order.append(team)
            logger.info("[add_link] Team '%s' added to rotation → %s", team, list(self.team_order))

        entry = {
            "team": team,
            "link": link,
            "timestamp": (timestamp or datetime.utcnow()).strftime("%Y-%m-%d %H:%M"),
        }
        self.queues[team].append(entry)
        logger.info("[add_link] Enqueued %s", entry)
        logger.debug("[add_link] Current queue for '%s': %s", team, list(self.queues[team]))

    # ------------------------------------------------------------------

    def get_link(self) -> Optional[dict]:
        """Pop and return the next song obeying round‑robin order."""

        logger.info("[get_link] Starting retrieval. team_order=%s", list(self.team_order))

        # Defensive rebuild: rotation empty but pending songs exist
        if not self.team_order:
            for t, q in self.queues.items():
                if q:
                    self.team_order.append(t)
            if self.team_order:
                logger.warning(
                    "[get_link] team_order was empty; rebuilt → %s", list(self.team_order)
                )

        while self.team_order:
            team = self.team_order[0]
            logger.debug("[get_link] Checking team '%s'", team)

            if self.queues[team]:
                song = self.queues[team].popleft()
                self.team_order.rotate(-1)
                logger.info(
                    "[get_link] Dispatching %s | new rotation=%s", song, list(self.team_order)
                )
                return song
            else:
                self.team_order.popleft()
                logger.info("[get_link] Team '%s' empty; removed from rotation", team)

        logger.info("[get_link] No songs left in any team")
        return None

    # ------------------------------------------------------------------
    # Helpers / Introspection
    # ------------------------------------------------------------------

    def is_empty(self) -> bool:
        """Return *True* if all team queues are empty."""
        return all(len(q) == 0 for q in self.queues.values())

    def is_dispatched(self, link: str, team: str) -> bool:
        """Return *True* if (*team*, *link*) has already been dispatched."""
        return (team, link) in self._dispatched

    def mark_dispatched(self, link: str, team: str) -> None:
        """Mark (*team*, *link*) as dispatched (immutability guard)."""
        self._dispatched.add((team, link))
