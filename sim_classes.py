import pygame
import numpy as np


class Hitbox:
    """
    A class representing a hitbox, used to detect collisions and manage position/size.

    Attributes:
        pos (tuple): Position of the hitbox (x, y).
        size (tuple): Size of the hitbox (width, height).
        id (int): Unique identifier for the hitbox.
    """

    def __init__(self, pos, size, id):
        """
        Initializes the Hitbox object.

        Args:
            pos (tuple): Position of the hitbox (x, y).
            size (tuple): Size of the hitbox (width, height).
            id (int): Unique identifier for the hitbox.
        """
        self.pos = pos
        self.size = size
        self.id = id

    def get_id(self):
        # Returns the ID of the hitbox.
        return self.id

    def collide(self):
        """
        Returns a pygame Rect object representing the hitbox's bounds.

        This can be used for collision detection with other objects.
        """
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def get_pos(self, option=None):
        """
        Gets the position of the hitbox.

        Args:
            option (str, optional): If "x" or "y", returns the respective coordinate. Defaults to None.

        Returns:
            tuple or float: The position of the hitbox as a tuple (x, y) or a specific coordinate if specified.
        """
        if option == "x":
            return self.pos[0]
        elif option == "y":
            return self.pos[1]
        else:
            return self.pos

    def get_size(self, option=None):
        """
        Gets the size of the hitbox.

        Args:
            option (str, optional): If "x" or "y", returns the respective dimension. Defaults to None.

        Returns:
            tuple or float: The size of the hitbox as a tuple (width, height) or a specific dimension if specified.
        """
        if option == "x":
            return self.size[0]
        elif option == "y":
            return self.size[1]
        else:
            return self.size

    def set_pos(self, pos):
        # Sets the position of the hitbox.
        self.pos = pos

    def set_size(self, size):
        # Sets the size of the hitbox.
        self.size = size

    def get_centre(self):
        """
        Calculates and returns the center of the hitbox.

        Returns:
            tuple: The center coordinates (x, y) of the hitbox.
        """
        centre = self.get_pos()
        half = [x / 2 for x in self.get_size()]
        centre[0] += half[0]
        centre[1] -= half[1]
        return centre


class Medium:
    """
    A class representing a medium, with a refractive index and rotation.

    Attributes:
        hitbox (Hitbox): The hitbox associated with this medium.
        refractive_index (float): The refractive index of the medium.
        rotation (float): The rotation angle of the medium in degrees.
    """

    def __init__(self, hitbox, rot, n):
        """
        Initializes the Medium object.

        Args:
            hitbox (Hitbox): The hitbox associated with the medium.
            rot (float): The rotation angle of the medium in degrees.
            n (float): The refractive index of the medium.
        """
        self.hitbox = hitbox
        self.refractive_index = n
        self.rotation = rot

    def get_rotated(self):
        """
        Returns the vertices of the hitbox after rotation.

        This method applies the rotation to the corners of the hitbox.

        Returns:
            list: List of the rotated vertices of the hitbox.
        """
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

        # Convert the rotated coordinates back to the original position
        v = []
        for coord in verts:
            coord = coord.A1
            v.append(coord)

        v = [(x + c[0], y + c[1]) for (x, y) in v]
        return [v[0], v[2], v[3], v[1]]

    def set_rot(self, rot):
        # Sets the rotation angle of the medium.
        self.rotation = rot

    def set_pos(self, pos):
        # Sets the position of the hitbox associated with the medium.
        self.pos = pos

    def set_size(self, size):
        # Sets the size of the hitbox associated with the medium.
        self.size = size

    def get_refractive_index(self):
        # Returns the refractive index of the medium.
        return self.refractive_index

    def set_refractive_index(self, n):
        # Sets the refractive index of the medium.
        self.refractive_index = n

    def get_id(self):
        # Returns the ID of the hitbox associated with the medium.
        return self.hitbox.get_id()

    def get_rect(self):
        # Returns the pygame Rect for the hitbox of the medium.
        return pygame.Rect(self.hitbox.get_pos(), self.hitbox.get_size())

    def get_rot(self):
        # Returns the rotation angle of the medium.
        return self.rotation


class Source:
    """
    A class representing a source, which can oscillate and interact with mediums.

    Attributes:
        hitbox (Hitbox): The hitbox associated with the source.
        frequency (float): The frequency of oscillation.
        amplitude (float): The amplitude of the oscillation.
        zerot (float): The time at which the source starts oscillating.
    """

    def __init__(self, hitbox, frequency, amplitude):
        """
        Initializes the Source object.

        Args:
            hitbox (Hitbox): The hitbox associated with the source.
            frequency (float): The frequency of oscillation.
            amplitude (float): The amplitude of the oscillation.
        """
        self.hitbox = hitbox
        self.freq = frequency
        self.amp = amplitude
        self.zerot = 0

    def get_amp(self):
        # Returns the amplitude of the source.
        return self.amp

    def get_freq(self):
        # Returns the frequency of the source.
        return self.freq

    def get_zerot(self):
        # Returns the time at which the source starts oscillating.
        return self.zerot

    def set_amp(self, amp):
        # Sets the amplitude of the source.
        self.amp = amp

    def set_freq(self, freq):
        # Sets the frequency of the source.
        self.freq = freq

    def set_zerot(self, time):
        # Sets the time at which the source starts oscillating.
        self.zerot = time

    def get_disp(self, time):
        """
        Calculates and returns the displacement of the source at a given time.

        Args:
            time (float): The time at which to calculate the displacement.

        Returns:
            float: The displacement of the source at the specified time.
        """
        z = self.get_zerot()
        f = self.get_freq()
        a = self.get_amp()
        disp = np.sin((time - z) * f) * a
        return disp
