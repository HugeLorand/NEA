class Shader:
    """
    A class representing a basic shader program. It holds information about the shader's
    program ID, vertex shader ID, and fragment shader ID, along with various attributes.

    Attributes:
        pid (int): The program ID of the shader.
        fid (int): The fragment shader ID.
        vid (int): The vertex shader ID.
        vertexPositionAttribute (int or None): The attribute for the vertex position.
        textureCoordAttribute (int or None): The attribute for the texture coordinates.
        dampingAttribute (int or None): The attribute for damping.
        colourAttribute (int or None): The attribute for colour information.
        pMatrixUniform (int or None): The uniform for the projection matrix.
        mvMatrixUniform (int or None): The uniform for the model-view matrix.
        samplerUniform (int or None): The uniform for the texture sampler.
    """

    def __init__(self, p_id: int, f_id: int = 0, v_id: int = 0):
        """
        Initializes the Shader object with given shader IDs.

        Args:
            p_id (int): Program ID.
            f_id (int, optional): Fragment shader ID. Defaults to 0.
            v_id (int, optional): Vertex shader ID. Defaults to 0.
        """
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
    def get_fid(self) -> int:
        return self.fid

    def get_vid(self) -> int:
        return self.vid

    def get_pid(self) -> int:
        return self.pid

    def get_vertexPositionAttribute(self) -> int:
        return self.vertexPositionAttribute

    def get_textureCoordAttribute(self) -> int:
        return self.textureCoordAttribute

    def get_dampingAttribute(self) -> int:
        return self.dampingAttribute

    def get_colourAttribute(self) -> int:
        return self.colourAttribute

    def get_pMatrixUniform(self) -> int:
        return self.pMatrixUniform

    def get_mvMatrixUniform(self) -> int:
        return self.mvMatrixUniform

    def get_samplerUniform(self) -> int:
        return self.samplerUniform

    # Setters
    def set_fid(self, f_id: int):
        self.fid = f_id

    def set_vid(self, v_id: int):
        self.vid = v_id

    def set_pid(self, p_id: int):
        self.pid = p_id

    def set_vertexPositionAttribute(self, vertexPositionAttribute: int):
        self.vertexPositionAttribute = vertexPositionAttribute

    def set_textureCoordAttribute(self, textureCoordAttribute: int):
        self.textureCoordAttribute = textureCoordAttribute

    def set_dampingAttribute(self, dampingAttribute: int):
        self.dampingAttribute = dampingAttribute

    def set_colourAttribute(self, colourAttribute: int):
        self.colourAttribute = colourAttribute

    def set_pMatrixUniform(self, pMatrixUniform: int):
        self.pMatrixUniform = pMatrixUniform

    def set_mvMatrixUniform(self, mvMatrixUniform: int):
        self.mvMatrixUniform = mvMatrixUniform

    def set_samplerUniform(self, samplerUniform: int):
        self.samplerUniform = samplerUniform


class ShaderMain(Shader):
    """
    A subclass of Shader that adds specific attributes for controlling brightness
    and colour in the shader.

    Attributes:
        brightnessUniform (int or None): The uniform for controlling brightness.
        coloursUniform (int or None): The uniform for controlling colour.
    """

    def __init__(self, p_id: int, f_id: int = 0, v_id: int = 0):
        """
        Initializes the ShaderMain object, extending from the base Shader class.

        Args:
            p_id (int): Program ID.
            f_id (int, optional): Fragment shader ID. Defaults to 0.
            v_id (int, optional): Vertex shader ID. Defaults to 0.
        """
        super().__init__(p_id, f_id, v_id)
        self.brightnessUniform = None
        self.coloursUniform = None


class ShaderSimulate(Shader):
    """
    A subclass of Shader that adds specific attributes for controlling simulation parameters
    such as step sizes in the X and Y directions.

    Attributes:
        stepSizeXUniform (int or None): The uniform for controlling the step size in the X direction.
        stepSizeYUniform (int or None): The uniform for controlling the step size in the Y direction.
    """

    def __init__(self, p_id: int, f_id: int = 0, v_id: int = 0):
        """
        Initializes the ShaderSimulate object, extending from the base Shader class.

        Args:
            p_id (int): Program ID.
            f_id (int, optional): Fragment shader ID. Defaults to 0.
            v_id (int, optional): Vertex shader ID. Defaults to 0.
        """
        super().__init__(p_id, f_id, v_id)
        self.stepSizeXUniform = None
        self.stepSizeYUniform = None


# Classes used for buffer setup


class Buffer:
    """
    A class representing a buffer, typically used in OpenGL for storing data like vertex positions
    or texture coordinates.

    Attributes:
        id (int): The ID of the buffer.
        itemSize (int or None): The size of each item in the buffer.
        numItems (int or None): The number of items in the buffer.
    """

    def __init__(self, id: int):
        """
        Initializes the Buffer object with a given ID.

        Args:
            id (int): The ID of the buffer.
        """
        self.id = id
        self.itemSize = None
        self.numItems = None

    # Getters
    def get_id(self) -> int:
        return self.id

    def get_itemSize(self) -> int:
        return self.itemSize

    def get_numItems(self) -> int:
        return self.numItems

    # Setters
    def set_id(self, id: int):
        self.id = id

    def set_itemSize(self, itemSize: int):
        self.itemSize = itemSize

    def set_numItems(self, numItems: int):
        self.numItems = numItems


class Texture:
    """
    A class representing a texture, which can be applied to a surface in OpenGL.

    Attributes:
        id (int): The ID of the texture.
        framebuffer (Framebuffer or None): The framebuffer associated with the texture.
        width (int): The width of the texture.
        height (int): The height of the texture.
    """

    def __init__(self, id: int, framebuffer=None):
        """
        Initializes the Texture object with a given ID and optional framebuffer.

        Args:
            id (int): The ID of the texture.
            framebuffer (Framebuffer, optional): The framebuffer associated with the texture. Defaults to None.
        """
        self.id = id
        self.framebuffer = framebuffer
        self.width = 0
        self.height = 0
        if framebuffer:
            self.width = framebuffer.get_width()
            self.height = framebuffer.get_height()

    # Getters
    def get_id(self) -> int:
        return self.id

    def get_width(self) -> int:
        return self.width

    def get_height(self) -> int:
        return self.height

    # Setters
    def set_id(self, id: int):
        self.id = id

    def set_width(self, width: int):
        self.width = width

    def set_height(self, height: int):
        self.height = height


class Framebuffer:
    """
    A class representing a framebuffer in OpenGL, which holds textures that can be rendered to.

    Attributes:
        id (int): The ID of the framebuffer.
        width (int): The width of the framebuffer.
        height (int): The height of the framebuffer.
    """

    def __init__(self, id: int, width: int = 0, height: int = 0):
        """
        Initializes the Framebuffer object with a given ID, width, and height.

        Args:
            id (int): The ID of the framebuffer.
            width (int, optional): The width of the framebuffer. Defaults to 0.
            height (int, optional): The height of the framebuffer. Defaults to 0.
        """
        self.id = id
        self.width = width
        self.height = height

    # Getters
    def get_id(self) -> int:
        return self.id

    def get_width(self) -> int:
        return self.width

    def get_height(self) -> int:
        return self.height

    # Setters
    def set_id(self, id: int):
        self.id = id

    def set_width(self, width: int):
        self.width = width

    def set_height(self, height: int):
        self.height = height
