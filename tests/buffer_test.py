from services.queue.queue_buffer import QueueBuffer  # Our new buffer
from services.queue.queue_manager import QueueManager       # Our new live queue manager
import sys
import os



buffer= QueueBuffer()


canciones = [("equipo1", "cancion1"), ("equipo1", "cancion2"), ("equipo1", "cancion3"),("equipo1", "cancion4"),
             ("equipo1", "cancion5"), ("equipo1", "cancion6"), ("equipo2", "cancion1"),("equipo2", "cancion2"),
             ("equipo3", "cancion1"),("equipo4", "cancion1"),("equipo1", "cancion6")]

for t, l in canciones: 
    buffer.add_song(t, l)

queue= QueueManager()


buffer.apply_to(queue)
buffer.apply_to(queue)
buffer.apply_to(queue)
buffer.apply_to(queue)
buffer.apply_to(queue)
buffer.apply_to(queue)
buffer.apply_to(queue)
buffer.apply_to(queue)


canciones = [("equipo1", "ncancion1"), ("equipo1", "ncancion2"), ("equipo1", "ncancion3"),("equipo1", "ncancion4"),
             ("equipo1", "ncancion5"), ("equipo1", "ncancion6"), ("equipo2", "ncancion1"),("equipo2", "ncancion2"),
             ("equipo3", "ncancion1"),("equipo4", "ncancion1"),("equipo1", "ncancion6")]

for t, l in canciones: 
    buffer.add_song(t, l)


buffer.apply_to(queue)
buffer.apply_to(queue)
