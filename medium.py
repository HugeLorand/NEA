from item_draggable import Item


class Medium(Item):
    def __init__(self, pos, size, id, n):
        super().__init__(pos, size, id)
        self._pos = pos
        self._size = size
        self._id = id
        self._refractive_index = n

    def get_pos(self):
        return self._pos

    def get_size(self):
        return self._size

    def set_pos(self, pos):
        self._pos = pos

    def set_size(self, size):
        self._size = size

    def get_refractive_index(self):
        return self._refractive_index
    
    def set_refractive_index(self, n):
        self._refractive_index = n

    def get_id(self):
        return self._id