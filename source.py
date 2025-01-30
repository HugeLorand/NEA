from item_draggable import Item


class Source(Item):
    def __init__(self, pos, size, frequency, wavelength, amplitude, color, decay):
        super().__init__(pos, size, color)
        self._freq = frequency
        self._wavelength = wavelength
        self._amp = amplitude
        self._decay = decay
        self._zerot = 0

    def getpos(self):
        return self._position

    def getamp(self):
        return self._amp

    def set_freq(self, frequency, current_time):
        self._freq = frequency
        self._zerot = current_time
