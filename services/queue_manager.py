from collections import deque

class QueueManager:
    def __init__(self):
        self.queue = deque()

    def add_link(self, link, user, channel, timestamp):
        self.queue.append({
            "link": link,
            "user": f"{user.name}#{user.discriminator}",
            "user_id": user.id,
            "channel": channel.name,
            "channel_id": channel.id,
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M")
        })

    def pop_link(self):
        return self.queue.popleft()

    def is_empty(self):
        return len(self.queue) == 0
