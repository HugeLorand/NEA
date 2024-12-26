import item_draggable
class Source(item_draggable.ItemDraggable):
    def __init__(self,frequency,wavelength,amplitude,colour,decay):
        super().__init__(self)
        self._freq = frequency
        self._wavelength = wavelength
        self._amp = amplitude
        self._colour = colour
        self._decay = decay
        self._zerot = 0


    def setfrequency(self, frequency, currenttime):
        self._freq = frequency
        self._zerot = currenttime
    def setcolour(self, colour):
        self._col = colour
