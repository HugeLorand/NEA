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
