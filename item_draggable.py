import pygame


class Item:
    def __init__(self, pos, size):
        self._position = pos
        self._size = size
        self._rect = pygame.Rect(pos[0], pos[1], size[0], size[1])

    def shape(self):
        return [self._rect]
