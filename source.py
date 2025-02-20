from item_draggable import Item


class Source(Item):
    def __init__(self, pos, id, frequency, amplitude, size=8):
        super().__init__(pos, size, id)
        self._position = pos
        self._freq = frequency
        self._amp = amplitude
        self._zerot = 0

    def get_pos(self):
        return self._position

    def get_amp(self):
        return self._amp

    def get_freq(self):
        return self._freq

    def set_pos(self, pos):
        self._position = pos

    def set_amp(self, amp):
        self._amp = amp

    def set_freq(self, freq):
        self._freq = freq

    def set_zerot(self, time):
        self._zerot = time
