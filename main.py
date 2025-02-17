import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GL.shaders import compileShader
import item_draggable
from conversion import *
from gl_classes import *
from source import Source
from medium import Medium
import math
import time
import numpy as np


class App:
    def __init__(self, title):
        self.running = True  # This is the main loop flag
        self.displaySurface = None  # This is the display surface for PyGame
        self.size = self.width, self.height = 1080, 1080  # This is the window size
        self.windowOffset = (
            10  # This is the offset of the window from the edge of the screen
        )
        self.caption = title  # This is the window title
        self.dragItems = []  # This is a list of all draggable items
        self.sources = []  # This is a list of all sources
        self.walls = []  # This is a list of all walls
        self.selected = (
            None  # This is the index of the item selected by the user using the mouse
        )
        self.offset = [
            0,
            0,
        ]  # This is the offset of the mouse from the top left corner of the selected item
        self.clock = pygame.time.Clock()  # This is the PyGame clock
        self.startTime = (
            time.time()
        )  # This is the time the simulation started (can change in order to prevent issues when items are added or moved)
        self.wavelength = 10  # This is the simulation wavelength
        self.waveTexture = None  # This is the OpenGL texture for the wave simulation
        self.damping = 1.0  # This is the damping factor for the simulation

        self.shaderProgramMain = None
        self.shaderProgramStatic = None
        self.shaderProgramProgressive = None
        self.shaderProgramDraw = None
        self.shaderProgramDrawLine = None

        self.vertexpPositionBuffer = None
        self.vertexTextureCoordBuffer = None
        self.sourceBuffer = None
        self.colorBuffer = None
        self.simVertexPositionBuffer = None
        self.simVertexTextureCoordBuffer = None
        self.simVertexDampingBuffer = None

        self.simPosition = []
        self.simDamping = []
        self.simTextureCoord = []

        self.progressive = False

        self.mvMatrix = np.matrix(np.identity(4), np.float32)
        self.pMatrix = np.matrix(np.identity(4), np.float32)
        self.mvMatrixStack = []

        self.renderTexture1 = None
        self.renderTexture2 = None

        self.colourScheme = [1, 1, 1, 1, 1, 1, 1, 1]

    def on_init(self):
        pygame.init()
        # Set up the display
        self.displaySurface = pygame.display.set_mode(
            self.size, pygame.DOUBLEBUF | pygame.OPENGL
        )
        # Set up the OpenGL context
        self.caption = pygame.display.set_caption(self.caption)
        gluPerspective(45, (self.width / self.height), 0.1, 50.0)
        glTranslatef(0.0, 0.0, -5)
        self.running = True

        # initialise shaders
        self.shaderProgramMain = self.create_shader(
            "shaders/display-fs.glsl", "shaders/vs.glsl"
        )
        self.shaderProgramMain.brightnessUniform = glGetUniformLocation(
            self.shaderProgramMain.get_id(), "brightness"
        )
        self.shaderProgramMain.coloursUniform = glGetUniformLocation(
            self.shaderProgramMain.get_id(), "colours"
        )

        self.shaderProgramStatic = self.create_shader(
            "shaders/simulate-stat-fs.glsl", "shaders/vs.glsl"
        )
        self.shaderProgramStatic.stepSizeXUniform = glGetUniformLocation(
            self.shaderProgramStatic.get_id(), "stepSizeX"
        )
        self.shaderProgramStatic.stepSizeYUniform = glGetUniformLocation(
            self.shaderProgramStatic.get_id(), "stepSizeY"
        )

        self.shaderProgramProgressive = self.create_shader(
            "shaders/simulate-prog-fs.glsl", "shaders/vs.glsl"
        )
        self.shaderProgramProgressive.stepSizeXUniform = glGetUniformLocation(
            self.shaderProgramProgressive.get_id(), "stepSizeX"
        )
        self.shaderProgramProgressive.stepSizeYUniform = glGetUniformLocation(
            self.shaderProgramProgressive.get_id(), "stepSizeY"
        )

        self.shaderProgramDraw = self.create_shader(
            "shaders/draw-fs.glsl", "shaders/draw-vs.glsl"
        )
        self.shaderProgramDrawLine = self.create_shader(
            "shaders/draw-line-fs.glsl", "shaders/draw-vs.glsl"
        )

        # setup buffers

        self.vertexPositionBuffer = Buffer(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, self.vertexPositionBuffer.id)
        glBufferData(
            GL_ARRAY_BUFFER,
            np.array([-1, +1, +1, +1, -1, -1, +1, -1], dtype=np.float32),
            GL_STATIC_DRAW,
        )
        self.vertexPositionBuffer.itemSize = 2
        self.vertexPositionBuffer.numItems = 4

        self.vertexTextureCoordBuffer = Buffer(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, self.vertexTextureCoordBuffer.id)
        glBufferData(
            GL_ARRAY_BUFFER,
            np.array(
                [
                    self.windowOffset / self.width,
                    1 - self.windowOffset / self.height,
                    1 - self.windowOffset / self.width,
                    1 - self.windowOffset / self.height,
                    self.windowOffset / self.width,
                    self.windowOffset / self.height,
                    1 - self.windowOffset / self.width,
                    self.windowOffset / self.height,
                ],
                dtype=np.float32,
            ),
            GL_STATIC_DRAW,
        )
        self.vertexTextureCoordBuffer.itemSize = 2
        self.vertexTextureCoordBuffer.numItems = 4

        self.sourceBuffer = Buffer(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, self.sourceBuffer.id)
        self.sourceBuffer.itemSize = 2
        self.sourceBuffer.numItems = 2

        self.colorBuffer = Buffer(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, self.colorBuffer.id)
        self.colorBuffer.itemSize = 4
        self.colorBuffer.numItems = 2

        # visible area
        self.setPosRect(
            self.windowOffset,
            self.windowOffset,
            self.width - self.windowOffset,
            self.height - self.windowOffset,
        )

        # sides
        self.setPosRect(
            1,
            self.windowOffset,
            self.windowOffset,
            self.height - self.windowOffset,
        )
        self.setPosRect(
            self.width - self.windowOffset,
            self.windowOffset,
            self.width - 2,
            self.height - self.windowOffset,
        )
        self.setPosRect(
            self.windowOffset,
            1,
            self.width - self.windowOffset,
            self.windowOffset,
        )
        self.setPosRect(
            self.windowOffset,
            self.height - self.windowOffset,
            self.width - self.windowOffset,
            self.height - 2,
        )

        # corners
        self.setPosRect(1, 1, self.windowOffset, self.windowOffset)
        self.setPosRect(
            self.width - self.windowOffset, 1, self.width - 2, self.windowOffset
        )
        self.setPosRect(
            1, self.height - self.windowOffset, self.windowOffset, self.height - 2
        )
        self.setPosRect(
            self.width - self.windowOffset,
            self.height - self.windowOffset,
            self.width - 2,
            self.height - 2,
        )

        self.simVertexPositionBuffer = Buffer(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, self.simVertexPositionBuffer.id)
        glBufferData(
            GL_ARRAY_BUFFER,
            np.array(self.simPosition, dtype=np.float32),
            GL_STATIC_DRAW,
        )
        self.simVertexPositionBuffer.itemSize = 2
        self.simVertexPositionBuffer.numItems = len(self.simPosition) / 2

        self.simVertexTextureCoordBuffer = Buffer(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, self.simVertexTextureCoordBuffer.id)
        glBufferData(
            GL_ARRAY_BUFFER,
            np.array(self.simTextureCoord, dtype=np.float32),
            GL_STATIC_DRAW,
        )
        self.simVertexTextureCoordBuffer.itemSize = 2
        self.simVertexTextureCoordBuffer.numItems = len(self.simPosition) / 2

        self.simVertexDampingBuffer = Buffer(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, self.simVertexDampingBuffer.id)
        glBufferData(
            GL_ARRAY_BUFFER, np.array(self.simDamping, dtype=np.float32), GL_STATIC_DRAW
        )
        self.simVertexDampingBuffer.itemSize = 1
        self.simVertexDampingBuffer.numItems = len(self.simDamping)

        # setup texture framebuffers
        self.renderTexture1 = self.initTextureFramebuffer()
        self.renderTexture2 = self.initTextureFramebuffer()

    def on_event(self, event):

        if event.type == pygame.QUIT:
            self.running = False
            # exit the program

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # goes through dragItems and selects an item that collides with the mouse, if available
                for index, item in enumerate(self.dragItems):
                    if item.collidepoint(event.pos):
                        # selects item
                        self.selected = index
                        mouse_x, mouse_y = event.pos
                        self.offset[0] = item.x - mouse_x
                        self.offset[1] = item.y - mouse_y

        elif event.type == pygame.MOUSEBUTTONUP:
            # deselects item
            if event.button == 1:
                self.selected = None

        elif event.type == pygame.MOUSEMOTION:
            # moves selected item
            if (
                self.selected is not None
            ):  # selected can be `0` so `is not None` is required, which is more efficient than "!="
                self.dragItems[self.selected][0].x = event.pos[0] + self.offset[0]
                self.dragItems[self.selected][0].y = event.pos[1] + self.offset[1]

    def on_loop(self):
        # update the simulation at a framerate of 144 fps
        self.clock.tick(144)
        # check if items are being changed

        # simulate
        rt = self.renderTexture1
        self.renderTexture1 = self.renderTexture2
        self.renderTexture2 = rt

        rttFramebuffer = self.renderTexture1.framebuffer
        glBindFramebuffer(GL_FRAMEBUFFER, rttFramebuffer.id)

        if self.progressive:
            prog = self.shaderProgramProgressive
        else:
            prog = self.shaderProgramStatic
        glUseProgram(prog.id)
        rttFramebuffer = self.renderTexture1.framebuffer
        glViewport(0, 0, rttFramebuffer.width, rttFramebuffer.height)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glBindBuffer(GL_ARRAY_BUFFER, self.simVertexPositionBuffer.get_id())
        glVertexAttribPointer(
            prog.vertexPositionAttribute,
            self.simVertexPositionBuffer.itemSize,
            GL_FLOAT,
            False,
            0,
            0,
        )

        glBindBuffer(GL_ARRAY_BUFFER, self.simVertexTextureCoordBuffer.get_id())
        glVertexAttribPointer(
            prog.textureCoordAttribute,
            self.simVertexTextureCoordBuffer.itemSize,
            GL_FLOAT,
            False,
            0,
            0,
        )

        glEnableVertexAttribArray(prog.dampingAttribute)
        glEnableVertexAttribArray(prog.vertexPositionAttribute)
        glEnableVertexAttribArray(prog.textureCoordAttribute)

        glBindBuffer(GL_ARRAY_BUFFER, self.simVertexDampingBuffer.get_id())
        glVertexAttribPointer(
            prog.dampingAttribute,
            self.simVertexDampingBuffer.itemSize,
            GL_FLOAT,
            False,
            0,
            0,
        )

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.renderTexture2.get_id())
        glUniform1i(prog.samplerUniform, 0)
        glUniform1f(prog.stepSizeXUniform, 1 / self.width)
        glUniform1f(prog.stepSizeYUniform, 1 / self.height)

        self.setMatrixUniforms(prog)
        glDrawArrays(GL_TRIANGLES, 0, int(self.simVertexPositionBuffer.numItems))
        glDisableVertexAttribArray(prog.dampingAttribute)
        glDisableVertexAttribArray(prog.vertexPositionAttribute)
        glDisableVertexAttribArray(prog.textureCoordAttribute)

        # draw sources
        for source in self.sources:
            f = math.sin(time.time() * source.get_freq()) * source.get_amp()
            glUseProgram(self.shaderProgramDraw.get_id())
            glVertexAttrib4f(self.shaderProgramDraw.colourAttribute, f, 0, 1, 1)

            glBindBuffer(GL_ARRAY_BUFFER, self.sourceBuffer.get_id())
            srcCoords = list(derectify(source.get_pos(), self.size))
            srcCoords.append(srcCoords[0])
            srcCoords.append(srcCoords[1] + 1)
            srcCoords = np.array(srcCoords, dtype=np.float32)
            glBufferData(GL_ARRAY_BUFFER, srcCoords, GL_STATIC_DRAW)
            glVertexAttribPointer(
                self.shaderProgramDraw.vertexPositionAttribute,
                self.sourceBuffer.itemSize,
                GL_FLOAT,
                False,
                0,
                0,
            )

            glEnableVertexAttribArray(self.shaderProgramDraw.vertexPositionAttribute)
            self.setMatrixUniforms(self.shaderProgramDraw)
            glDrawArrays(GL_LINES, 0, 4)
            glDisableVertexAttribArray(self.shaderProgramDraw.vertexPositionAttribute)

        # draw walls

    def on_render(self):
        # draw_scene
        glUseProgram(self.shaderProgramMain.get_id())
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glViewport(0, 0, self.width, self.height)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.pMatrix = np.matrix(np.identity(4), np.float32)
        self.mvMatrix = np.matrix(np.identity(4), np.float32)
        self.mvMatrixStack.append(self.mvMatrix)

        # draw result
        glBindBuffer(GL_ARRAY_BUFFER, self.vertexPositionBuffer.get_id())
        glVertexAttribPointer(
            self.shaderProgramMain.vertexPositionAttribute,
            self.vertexPositionBuffer.itemSize,
            GL_FLOAT,
            False,
            0,
            0,
        )

        glBindBuffer(GL_ARRAY_BUFFER, self.vertexTextureCoordBuffer.get_id())
        glVertexAttribPointer(
            self.shaderProgramMain.textureCoordAttribute,
            self.vertexTextureCoordBuffer.itemSize,
            GL_FLOAT,
            False,
            0,
            0,
        )

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.renderTexture1.get_id())
        glUniform1i(self.shaderProgramMain.samplerUniform, 0)
        glUniform1f(self.shaderProgramMain.brightnessUniform, 1)
        glUniform3fv(
            self.shaderProgramMain.coloursUniform,
            len(self.colourScheme),
            self.colourScheme,
        )

        self.setMatrixUniforms(self.shaderProgramMain)
        glEnableVertexAttribArray(self.shaderProgramMain.vertexPositionAttribute)
        glEnableVertexAttribArray(self.shaderProgramMain.textureCoordAttribute)
        glDrawArrays(GL_TRIANGLE_STRIP, 0, self.vertexPositionBuffer.numItems)
        glDisableVertexAttribArray(self.shaderProgramMain.vertexPositionAttribute)
        glDisableVertexAttribArray(self.shaderProgramMain.textureCoordAttribute)

        self.mvMatrixStack.pop()
        pygame.display.flip()

    def on_cleanup(self):
        pygame.quit()

    def on_execute(self):
        if self.on_init() == False:
            self.running = False

        # Add sources and walls
        self.add_source([self.width / 2, self.height / 2], 1, 10, 50)
        self.add_source([(self.width / 2) + 200, (self.height / 2) + 200], 2, 10, 50)
        self.add_wall([300, 300], [10, 100], 3)

        # Run the main loop
        while self.running:
            for event in pygame.event.get():
                self.on_event(event)
            self.on_loop()
            self.on_render()

        self.on_cleanup()

    def add_drag(self, pos, size, id):
        # adds a draggable object at position [x,y], of size [width,height]
        item = item_draggable.Item(pos, size, id)
        self.dragItems.append(item.hitbox())

    def add_source(self, pos, id, frequency, amplitude):
        source = Source(pos, id, frequency, amplitude)
        self.sources.append(source)
        self.add_drag(pos, [8, 8], id)

    def add_wall(self, pos, size, id):
        wall = Medium(pos, size, id, 0)
        self.walls.append(wall)
        self.add_drag(pos, size, id)

    def draw_items(self):
        for item in self.dragItems:
            # Convert Pygame rectangle to OpenGL vertices
            draw = derectify(item, (self.width, self.height))
            glBegin(GL_LINES)
            for edge in SQUARE_EDGES:
                for vertex in edge:
                    glVertex3fv(draw[vertex])  # Use normalized coordinates
            glEnd()

    def load_shader(self, shader_file):
        f = open(shader_file, "r")
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
            case _:
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

    def setPosRect(self, x1, y1, x2, y2):
        points = [x2, y1, x1, y1, x2, y2, x1, y1, x2, y2, x1, y2]
        for i in range(5):
            xi = points[i * 2]
            yi = points[i * 2 + 1]
            self.simPosition.append(-1 + (2 * xi / self.width))
            self.simPosition.append(-1 + (2 * yi / self.height))
            self.simTextureCoord.append(xi / self.width)
            self.simTextureCoord.append(1 - yi / self.height)
            damp = self.damping
            if xi == 1 or yi == 1 or xi == self.width - 1 or yi == self.height - 1:
                damp = damp * 0.91
            self.simDamping.append(damp)

    def setMatrixUniforms(self, shader):
        glUniformMatrix4fv(shader.pMatrixUniform, 1, False, self.pMatrix)
        glUniformMatrix4fv(shader.mvMatrixUniform, 1, False, self.mvMatrix)

    def initTextureFramebuffer(self):
        framebuffer = np.empty(1, dtype=np.uint32)
        glCreateFramebuffers(1, framebuffer)
        fb = Framebuffer(framebuffer[0])
        glBindFramebuffer(GL_FRAMEBUFFER, fb.get_id())
        fb.set_width(self.width)
        fb.set_height(self.height)

        texture = np.empty(1, dtype=np.uint32)
        glCreateTextures(GL_TEXTURE_2D, 1, texture)
        tx = Texture(int(texture[0]), fb)
        glBindTexture(GL_TEXTURE_2D, tx.get_id())
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, tx.get_width(), tx.get_height())

        glFramebufferTexture2D(
            GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, tx.get_id(), 0
        )

        status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        if status != GL_FRAMEBUFFER_COMPLETE:
            print(status)
            return None

        glBindTexture(GL_TEXTURE_2D, 0)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        return tx


if __name__ == "__main__":
    WaveSim = App(title="WaveSim")
    WaveSim.on_execute()
