class Shader:
    def __init__(self, id):
        self.id = id
        self.vertexPositionAttribute = None
        self.textureCoordAttribute = None
        self.dampingAttribute = None
        self.colourAttribute = None

        self.pMatrixUniform = None
        self.mvMatrixUniform = None
        self.nMatrixUniform = None
        self.samplerUniform = None

    # Getters
    def get_id(self):
        return self.id

    def get_vertexPositionAttribute(self):
        return self.vertexPositionAttribute

    def get_textureCoordAttribute(self):
        return self.textureCoordAttribute

    def get_dampingAttribute(self):
        return self.dampingAttribute

    def get_colourAttribute(self):
        return self.colourAttribute

    def get_pMatrixUniform(self):
        return self.pMatrixUniform

    def get_mvMatrixUniform(self):
        return self.mvMatrixUniform

    def get_samplerUniform(self):
        return self.samplerUniform

    # Setters
    def set_id(self, id):
        self.id = id

    def set_vertexPositionAttribute(self, vertexPositionAttribute):
        self.vertexPositionAttribute = vertexPositionAttribute

    def set_textureCoordAttribute(self, textureCoordAttribute):
        self.textureCoordAttribute = textureCoordAttribute

    def set_dampingAttribute(self, dampingAttribute):
        self.dampingAttribute = dampingAttribute

    def set_colourAttribute(self, colourAttribute):
        self.colourAttribute = colourAttribute

    def set_pMatrixUniform(self, pMatrixUniform):
        self.pMatrixUniform = pMatrixUniform

    def set_mvMatrixUniform(self, mvMatrixUniform):
        self.mvMatrixUniform = mvMatrixUniform

    def set_samplerUniform(self, samplerUniform):
        self.samplerUniform = samplerUniform


class ShaderMain(Shader):
    def __init__(self, id):
        super().__init__(id)
        self.brightnessUniform = None
        self.coloursUniform = None


class ShaderSimulate(Shader):
    def __init__(self, id):
        super().__init__(id)
        self.stepSizeXUniform = None
        self.stepSizeYUniform = None


# classes used for buffer setup


class Buffer:
    def __init__(self, id):
        self.id = id
        self.itemSize = None
        self.numItems = None

    # Getters
    def get_id(self):
        return self.id

    def get_itemSize(self):
        return self.itemSize

    def get_numItems(self):
        return self.numItems

    # Setters
    def set_id(self, id):
        self.id = id

    def set_itemSize(self, itemSize):
        self.itemSize = itemSize

    def set_numItems(self, numItems):
        self.numItems = numItems


class Texture:
    def __init__(self, id, framebuffer=None):
        self.id = id
        self.framebuffer = framebuffer
        self.width = 0
        self.height = 0
        if framebuffer:
            self.width = framebuffer.get_width()
            self.height = framebuffer.get_height()

    # Getters
    def get_id(self):
        return self.id

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    # Setters
    def set_id(self, id):
        self.id = id

    def set_width(self, width):
        self.width = width

    def set_height(self, height):
        self.height = height


class Framebuffer:
    def __init__(self, id, width=0, height=0):
        self.id = id
        self.width = width
        self.height = height

    # Getters
    def get_id(self):
        return self.id

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    # Setters
    def set_id(self, id):
        self.id = id

    def set_width(self, width):
        self.width = width

    def set_height(self, height):
        self.height = height
