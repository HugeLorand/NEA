import item_draggable
class Source(item_draggable.ItemDraggable):
    def __init__(self,frequency,wavelength,amplitude,color,decay):
        super().__init__(self)
        self._freq = frequency
        self._wavelength = wavelength
        self._amp = amplitude
        self._color = color
        self._decay = decay
        self._zerot = 0


    def setfrequency(self, frequency, currenttime):
        self._freq = frequency
        self._zerot = currenttime
    def setcolour(self, color):
        self._col = color

