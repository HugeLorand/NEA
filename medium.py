from item_draggable import Item
import pygame
import numpy as np


class Medium(Item):
    def __init__(self, pos, size, id, rot, n):
        super().__init__(pos, size, id)
        self.pos = pos
        self.size = size
        self.id = id
        self.refractive_index = n
        self.rotation = rot

    def get_pos(self, option=None):
        if option == "x":
            return self.pos[0]
        elif option == "y":
            return self.pos[1]
        else:
            return self.pos

    def get_size(self, option=None):
        if option == "x":
            return self.size[0]
        elif option == "y":
            return self.size[1]
        else:
            return self.size

    def get_centre(self):
        centre = self.get_pos()
        offset = [x / 2 for x in self.get_size()]
        c1 = centre[0]
        c2 = centre[1]
        c1 += offset[0]
        c2 -= offset[0]
        return centre

    def get_rotated(self):
        p = self.get_pos()
        s = self.get_size()
        r = self.get_rot()
        c = self.get_centre()
        verts = [
            (p[0], p[1]),
            (p[0] + s[0], p[1]),
            (p[0], p[1] + s[1]),
            (p[0] + s[0], p[1] + s[1]),
        ]
        verts = [(x - c[0], y - c[1]) for (x, y) in verts]
        r = np.pi * r / 180
        mat = np.matrix([[np.cos(r), -np.sin(r)], [np.sin(r), np.cos(r)]])
        verts = [coord * mat for coord in verts]

        print(verts)
        v = []
        for coord in verts:
            coord = coord.A1
            v.append(coord)
        print(v)
        v = [(x + c[0], y + c[1]) for (x, y) in v]
        return [v[0], v[2], v[3], v[1]]

    def set_rot(self, rot):
        self.rotation = rot

    def set_pos(self, pos):
        self.pos = pos

    def set_size(self, size):
        self.size = size

    def get_refractive_index(self):
        return self.refractive_index

    def set_refractive_index(self, n):
        self.refractive_index = n

    def get_id(self):
        return self.id

    def get_rect(self):
        return pygame.Rect(self.get_pos(), self.get_size())

    def get_rot(self):
        return self.rotation
