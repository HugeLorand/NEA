class Shader:
    def __init__(self, p_id, f_id=0, v_id=0):
        self.pid = p_id
        self.fid = f_id
        self.vid = v_id
        self.vertexPositionAttribute = None
        self.textureCoordAttribute = None
        self.dampingAttribute = None
        self.colourAttribute = None

        self.pMatrixUniform = None
        self.mvMatrixUniform = None
        self.samplerUniform = None

    # Getters
    def get_fid(self):
        return self.fid

    def get_vid(self):
        return self.vid

    def get_pid(self):
        return self.pid

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
    def set_fid(self, f_id):
        self.fid = f_id

    def set_vid(self, v_id):
        self.vid = v_id

    def set_pid(self, p_id):
        self.pid = p_id

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

    def __init__(self, p_id, f_id=0, v_id=0):
        super().__init__(p_id, f_id, v_id)
        self.brightnessUniform = None
        self.coloursUniform = None


class ShaderSimulate(Shader):

    def __init__(self, p_id, f_id=0, v_id=0):
        super().__init__(p_id, f_id, v_id)
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
        # Technically, the size of the framebuffer should depend on the size of the texutre. However, due to the order in which they are initialised, this has to be done to achieve the same outcome
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
