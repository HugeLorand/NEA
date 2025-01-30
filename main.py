import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GL.shaders import compileShader
import item_draggable
import conversion
from source import Source
from wall import Wall
import math
import time
import numpy as np

SQUARE_EDGES = [(0, 1), (0, 2), (1, 3), (2, 3)]


class App:
    def __init__(self, title):
        self._running = True  # This is the main loop flag
        self._display_surf = None  # This is the display surface for PyGame
        self._size = self.weight, self.height = 1080, 1080  # This is the window size
        self._caption = title  # This is the window title
        self._dragitems = []  # This is a list of all draggable items
        self._sources = []  # This is a list of all sources
        self._walls = []  # This is a list of all walls
        self._selected = (
            None  # This is the index of the item selected by the user using the mouse
        )
        self._offset = [
            0,
            0,
        ]  # This is the offset of the mouse from the top left corner of the selected item
        self._clock = pygame.time.Clock()  # This is the PyGame clock
        self.start_time = (
            time.time()
        )  # This is the time the simulation started (can change in order to prevent issues when items are added or moved)
        self._wavelength = 10  # This is the simulation wavelength
        self._wave_texture = None  # This is the OpenGL texture for the wave simulation
        self._colour_scheme = []  # This is the colour scheme for the simulation

    def on_init(self):
        pygame.init()
        # Set up the display
        self._display_surf = pygame.display.set_mode(
            self._size, pygame.DOUBLEBUF | pygame.OPENGL
        )
        # Set up the OpenGL context
        self._caption = pygame.display.set_caption(self._caption)
        gluPerspective(45, (self.weight / self.height), 0.1, 50.0)
        glTranslatef(0.0, 0.0, -5)
        self._running = True

        # initialise shaders
        shaderProgramMain = self.create_shader(
            "shaders/display-fs.glsl", "shaders/vs.glsl"
        )
        shaderProgramMain.brightnessUniform = glGetUniformLocation(
            shaderProgramMain.get_id(), "brightness"
        )
        shaderProgramMain.coloursUniform = glGetUniformLocation(
            shaderProgramMain.get_id(), "colours"
        )

        shaderProgramStatic = self.create_shader(
            "shaders/simulate-stat-fs.glsl", "shaders/vs.glsl"
        )
        shaderProgramStatic.stepSizeXUniform = glGetUniformLocation(
            shaderProgramStatic.get_id(), "stepSizeX"
        )
        shaderProgramStatic.stepSizeYUniform = glGetUniformLocation(
            shaderProgramStatic.get_id(), "stepSizeY"
        )

        shaderProgramProgressive = self.create_shader(
            "shaders/simulate-prog-fs.glsl", "shaders/vs.glsl"
        )
        shaderProgramProgressive.stepSizeXUniform = glGetUniformLocation(
            shaderProgramProgressive.get_id(), "stepSizeX"
        )
        shaderProgramProgressive.stepSizeYUniform = glGetUniformLocation(
            shaderProgramProgressive.get_id(), "stepSizeY"
        )

        shaderProgramDraw = self.create_shader(
            "shaders/draw-fs.glsl", "shaders/draw-vs.glsl"
        )
        shaderProgramDrawLine = self.create_shader(
            "shaders/draw-line-fs.glsl", "shaders/draw-vs.glsl"
        )

    def on_event(self, event):

        if event.type == pygame.QUIT:
            self._running = False
            # exit the program

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # goes through _dragitems and selects an item that collides with the mouse, if available
                for index, item in enumerate(self._dragitems):
                    if item[0].collidepoint(event.pos):
                        # selects item
                        self._selected = index
                        mouse_x, mouse_y = event.pos
                        self._offset[0] = item[0].x - mouse_x
                        self._offset[1] = item[0].y - mouse_y

        elif event.type == pygame.MOUSEBUTTONUP:
            # deselects item
            if event.button == 1:
                self._selected = None

        elif event.type == pygame.MOUSEMOTION:
            # moves selected item
            if (
                self._selected is not None
            ):  # selected can be `0` so `is not None` is required, which is more efficient than "!="
                self._dragitems[self._selected][0].x = event.pos[0] + self._offset[0]
                self._dragitems[self._selected][0].y = event.pos[1] + self._offset[1]

    def on_loop(self):
        # update the simulation at a framerate of 144 fps
        self._clock.tick(144)

    def on_render(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.draw_items()
        # insert here shader that renders waves to screen by taking previous frame and running calculations on each pixel to decode r g and b channels (displacement, velocity, refractive index at position)
        pygame.display.flip()

    def on_cleanup(self):
        pygame.quit()

    def on_execute(self):
        if self.on_init() == False:
            self._running = False

        # Add sources and walls
        self.add_source(
            [self.weight / 2, self.height / 2], 5, 100, 50, (255, 0, 0), False
        )
        self.add_source(
            [(self.weight / 2) + 200, (self.height / 2) + 200],
            2,
            200,
            30,
            (0, 0, 255),
            False,
        )
        self.add_wall([300, 300], [100, 300], (0, 255, 0))

        # Run the main loop
        while self._running:
            for event in pygame.event.get():
                self.on_event(event)
            self.on_loop()
            self.on_render()

        self.on_cleanup()

    def add_drag(self, pos, size, colour):
        # adds a draggable object at position [x,y], of size [width,height]
        item = item_draggable.Item(pos, size, colour)
        self._dragitems.append(item.shape())

    def add_source(self, pos, frequency, wavelength, amplitude, colour, decay):
        source = Source(pos, [10, 10], frequency, wavelength, amplitude, colour, decay)
        self._sources.append(source)
        self.add_drag(pos, [10, 10], colour)

    def add_wall(self, start_pos, end_pos, colour):
        wall = Wall(start_pos, end_pos, colour)
        self._walls.append(wall)

    def draw_items(self):
        for item in self._dragitems:
            # Convert Pygame rectangle to OpenGL vertices
            draw = conversion.derectify(item[0], (self.weight, self.height))
            glBegin(GL_LINES)
            for edge in SQUARE_EDGES:
                for vertex in edge:
                    glVertex3fv(draw[vertex])  # Use normalized coordinates
            glEnd()

    def load_shader(self, shader_file):
        with open(shader_file, "r") as f:
            shader_source = f.read()
        if shader_source:

            if "fs" in shader_file:
                shader = compileShader(shader_source, GL_FRAGMENT_SHADER)
            elif "vs" in shader_file:
                shader = compileShader(shader_source, GL_VERTEX_SHADER)
            else:
                return None

            glCompileShader(shader)
            return shader

        else:
            print("Shader not found")
            return None
            # error handling

    def create_shader(self, fs, vs):

        try:
            frag_shader = self.load_shader(fs)
        except:
            print("Fragment shader not found")
            return None
        try:
            vert_shader = self.load_shader(vs)
        except:
            print("Vertex shader not found")
            return None

        match fs:
            case "shaders/display-fs.glsl":
                shader = ShaderMain(glCreateProgram())
            case "shaders/simulate-stat-fs.glsl":
                shader = ShaderSimulate(glCreateProgram())
            case "shaders/simulate-prog-fs.glsl":
                shader = ShaderSimulate(glCreateProgram())
            case other:
                shader = Shader(glCreateProgram())

        glAttachShader(shader.get_id(), vert_shader)
        glAttachShader(shader.get_id(), frag_shader)
        glLinkProgram(shader.get_id())
        glUseProgram(shader.get_id())

        shader.vertexPositionAttribute = glGetAttribLocation(shader.get_id(), "aVPos")
        shader.textureCoordAttribute = glGetAttribLocation(shader.get_id(), "aTexCoord")
        shader.dampingAttribute = glGetAttribLocation(shader.get_id(), "aDamping")
        shader.colourAttribute = glGetAttribLocation(shader.get_id(), "aColour")

        shader.pMatrixUniform = glGetUniformLocation(shader.get_id(), "uPMatrix")
        shader.mvMatrixUniform = glGetUniformLocation(shader.get_id(), "uMVMatrix")
        shader.samplerUniform = glGetUniformLocation(shader.get_id(), "uSampler")

        return shader


# Classes used for shader setup


class Shader:
    def __init__(self, id):
        self.id = id
        self.vertexPositionAttribute = None
        self.textureCoordAttribute = None
        self.dampingAttribute = None
        self.colourAttribute = None

        self.pMatrixUniform = None
        self.mvMatrixUniform = None
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


if __name__ == "__main__":
    WaveSim = App(title="WaveSim")
    WaveSim.on_execute()
