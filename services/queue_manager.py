from collections import deque

class QueueManager:
    def __init__(self):
        self.queues = {}
        self.team_order = deque()

    def add_link(self, link, user, channel, timestamp):
        team = channel.name
        if team not in self.queues:
            self.queues[team] = deque()
            self.team_order.append(team)
        self.queues[team].append({
            "link": link,
            "user": f"{user.name}#{user.discriminator}",
            "user_id": user.id,
            "channel": channel.name,
            "channel_id": channel.id,
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M")
        })

    def get_link(self):
        while self.team_order:
            team = self.team_order[0]  # Get the next team to serve
            if self.queues[team]:
                song = self.queues[team].popleft()
                # Move this team to the end of the order to ensure fairness
                self.team_order.rotate(-1)
                return song
            else:
                # If the team queue is empty, remove it from the round
                self.team_order.popleft()
        return None

    def is_empty(self):
        return all(len(queue) == 0 for queue in self.queues.values())
