import pygame
import numpy as np


class Hitbox:
    def __init__(self, pos, size, id):
        self.pos = pos
        self.size = size
        self.id = id

    def get_id(self):
        return self.id

    def collide(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

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

    def set_pos(self, pos):
        self._pos = pos

    def set_size(self, size):
        self._size = size

    def get_centre(self):
        centre = self.get_pos()
        half = [x / 2 for x in self.get_size()]
        centre[0] += half[0]
        centre[1] -= half[1]
        return centre


class Medium:
    def __init__(self, hitbox, rot, n):
        self.hitbox = hitbox
        self.refractive_index = n
        self.rotation = rot

    def get_rotated(self):
        p = self.hitbox.get_pos()
        s = self.hitbox.get_size()
        r = self.get_rot()
        c = self.hitbox.get_centre()
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
        return self.hitbox.get_id()

    def get_rect(self):
        return pygame.Rect(self.hitbox.get_pos(), self.hitbox.get_size())

    def get_rot(self):
        return self.rotation


class Source:
    def __init__(self, hitbox, frequency, amplitude):
        self.hitbox = hitbox
        self.freq = frequency
        self.amp = amplitude
        self.zerot = 0

    def get_amp(self):
        return self.amp

    def get_freq(self):
        return self.freq

    def get_zerot(self):
        return self.zerot

    def set_amp(self, amp):
        self.amp = amp

    def set_freq(self, freq):
        self.freq = freq

    def set_zerot(self, time):
        self.zerot = time

    def get_disp(self, time):
        z = self.get_zerot()
        f = self.get_freq()
        a = self.get_amp()
        disp = np.sin((time - z) * f) * a
        return disp


class Slider:
    def __init__(self, name, min, max, value=0):
        self.name = name
        self.value = value
        self.min = min
        self.max = max

    def get_value(self):
        val = self.value / (self.max - self.min) * 240 + 30
        return val

    def get_min(self):
        return self.min

    def get_max(self):
        return self.max

    def get_name(self):
        return
