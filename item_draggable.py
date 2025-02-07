import pygame


class Item:
    def __init__(self, pos, size, id):
        self._pos = pos
        self._size = size
        self._id = id

    def hitbox(self):
        return pygame.Rect(self._pos[0], self._pos[1], self._size[0], self._size[1])
