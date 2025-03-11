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
import numpy as np


class App:
    def __init__(self, title):
        self.running = True  # Flag for main loop
        self.simDisplaySurface = None  # Display surface for PyGame
        self.size = self.width, self.height = 1024, 1024  # Window size
        self.windowOffset = 0.04  # Offset of the window from the edge of the screen
        self.caption = title  # Window title
        self.dragItems = []  # List of all draggable items
        self.sources = []  # List of all sources
        self.walls = []  # List of all walls

        self.selected = None  # Index of the item selected by the user using the mouse
        self.offset = [
            0,
            0,
        ]  # Offset of the mouse from the top left corner of the selected item
        self.actionstack = (
            []
        )  # stack used to keep track of the latest 10 actions for undoing/redoing
        self.actionstackpointer = 0  # pointer used to keep track of where we are in the action history when undoing/redoing

        self.clock = pygame.time.Clock()  # PyGame clock
        self.startTime = 0  # Time the simulation started (can change in order to prevent issues when items are added or moved)
        self.time = 0
        self.wavelength = 10  # Simulation wavelength
        self.damping = 1.0  # Damping factor for the simulation

        self.displayShader = None  # What gets displayed
        self.mainShaderStat = None  # What gets calculated - walls reflect
        self.mainShaderProg = None  # What gets calculated - walls damp
        self.drawShader = None  # Draws to screen

        self.posVBO = None  # VBO for position used in displaying
        self.texCoordVBO = None  # VBO for display texture coordinates
        self.sourceVBO = None  # VBO for item drawing

        self.simPosVBO = None  # VBO for position used in calculation
        self.simPos = []
        self.simTexCoordVBO = None  # VBO for calculation texture coordinates
        self.simTexCoord = []
        self.simDampingVBO = None  # VBO for damping at vertex
        self.simDamping = []

        self.progressive = False  # Flag for simulation running

        self.mvMatrix = np.matrix(np.identity(4), np.float32)  # Model-View matrix
        self.pMatrix = np.matrix(np.identity(4), np.float32)  # Projection matrix

        self.renderTexture1 = None  # the two textures which we swap between each frame, diplaying one and rendering to the other
        self.renderTexture2 = None
        self.rtt = None  # keeps track of which texture is being rendered to

        self.colourScheme = [
            1,
            0,
            0,
            0,
            0.75,
            0,
            0,
            0,
            1,
            0,
            0,
            0,
            0.75,
            0.75,
            0,
            0,
            0.75,
            0.75,
            1,
            0,
            1,
            1,
            0.5,
            0,
        ]  # Display colours of walls followed by positive, negative, and neutral displacements both in the "air" and in a medium, mediums and sources (normalised RGB)

    def on_init(self):
        pygame.init()
        # set up the display
        self.simDisplaySurface = pygame.display.set_mode(
            self.size, pygame.DOUBLEBUF | pygame.OPENGL
        )
        # version check
        pygame.display.gl_set_attribute(GL_CONTEXT_MAJOR_VERSION, 4)
        pygame.display.gl_set_attribute(GL_CONTEXT_MINOR_VERSION, 0)
        pygame.display.gl_set_attribute(
            pygame.GL_CONTEXT_PROFILE_MASK, GL_CONTEXT_PROFILE_CORE
        )
        # Set up the OpenGL context and gives the window a title
        self.caption = pygame.display.set_caption(self.caption)
        gluPerspective(45, (self.width / self.height), 0.1, 50.0)
        self.running = True

        # initialise shaders

        # display shader
        self.displayShader = self.create_shader(
            "shaders/display-fs.glsl", "shaders/vs.glsl"
        )
        self.displayShader.brightnessUniform = glGetUniformLocation(
            self.displayShader.get_id(), "brightness"
        )
        self.displayShader.coloursUniform = glGetUniformLocation(
            self.displayShader.get_id(), "colours"
        )

        # rendering shader, handling walls differently
        self.mainShaderStat = self.create_shader(
            "shaders/simulate-stat-fs.glsl", "shaders/vs.glsl"
        )
        self.mainShaderStat.stepSizeXUniform = glGetUniformLocation(
            self.mainShaderStat.get_id(), "stepSizeX"
        )
        self.mainShaderStat.stepSizeYUniform = glGetUniformLocation(
            self.mainShaderStat.get_id(), "stepSizeY"
        )

        # rendering shader, handling wall reflections well
        self.mainShaderProg = self.create_shader(
            "shaders/simulate-prog-fs.glsl", "shaders/vs.glsl"
        )
        self.mainShaderProg.stepSizeXUniform = glGetUniformLocation(
            self.mainShaderProg.get_id(), "stepSizeX"
        )
        self.mainShaderProg.stepSizeYUniform = glGetUniformLocation(
            self.mainShaderProg.get_id(), "stepSizeY"
        )

        # shaders used for drawing lines to screen
        self.drawShader = self.create_shader(
            "shaders/draw-fs.glsl", "shaders/draw-vs.glsl"
        )

        # set up buffers

        # vertex buffer object for position is set to the top-left, top-right, bottom-left, and bottom-right corners respectively
        self.vertexPositionBuffer = Buffer(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, self.vertexPositionBuffer.get_id())
        glBufferData(
            GL_ARRAY_BUFFER,
            np.array([-1, +1, +1, +1, -1, -1, +1, -1], dtype=np.float32),
            GL_STATIC_DRAW,
        )
        # coordinates use two values each
        self.vertexPositionBuffer.itemSize = 2
        # four corners of the display
        self.vertexPositionBuffer.numItems = 4

        # vertex buffer object for texture coordinates is set to the corners of the simulation
        self.texCoordVBO = Buffer(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, self.texCoordVBO.id)
        glBufferData(
            GL_ARRAY_BUFFER,
            np.array(
                [
                    self.windowOffset,
                    1 - self.windowOffset,
                    1 - self.windowOffset,
                    1 - self.windowOffset,
                    self.windowOffset,
                    self.windowOffset,
                    1 - self.windowOffset,
                    self.windowOffset,
                ],
                dtype=np.float32,
            ),
            GL_STATIC_DRAW,
        )
        # coordinates use two values each
        self.texCoordVBO.itemSize = 2
        # four corners of texture corners
        self.texCoordVBO.numItems = 4

        # set up shape of sourceVBO
        self.sourceVBO = Buffer(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, self.sourceVBO.id)
        self.sourceVBO.itemSize = 2
        self.sourceVBO.numItems = 2

        # visible area
        self.setPosRect(
            self.windowOffset,
            self.windowOffset,
            1 - self.windowOffset,
            1 - self.windowOffset,
        )

        # sides
        self.setPosRect(
            1,
            self.windowOffset,
            self.windowOffset,
            1 - self.windowOffset,
        )
        self.setPosRect(
            1 - self.windowOffset,
            self.windowOffset,
            -1,
            1 - self.windowOffset,
        )
        self.setPosRect(
            self.windowOffset,
            1,
            1 - self.windowOffset,
            self.windowOffset,
        )
        self.setPosRect(
            self.windowOffset,
            1 - self.windowOffset,
            1 - self.windowOffset,
            -1,
        )

        # corners
        self.setPosRect(1, 1, self.windowOffset, self.windowOffset)
        self.setPosRect(1 - self.windowOffset, 1, 1 - 2, self.windowOffset)
        self.setPosRect(1, 1 - self.windowOffset, self.windowOffset, -1)
        self.setPosRect(
            1 - self.windowOffset,
            1 - self.windowOffset,
            -1,
            -1,
        )

        # these buffers are for exchanging data between shaders
        self.simPosVBO = Buffer(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, self.simPosVBO.id)
        glBufferData(
            GL_ARRAY_BUFFER,
            np.array(self.simPos, dtype=np.float32),
            GL_STATIC_DRAW,
        )
        self.simPosVBO.itemSize = 2
        self.simPosVBO.numItems = len(self.simPos) / 2

        self.simTexCoordVBO = Buffer(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, self.simTexCoordVBO.id)
        glBufferData(
            GL_ARRAY_BUFFER,
            np.array(self.simTexCoord, dtype=np.float32),
            GL_STATIC_DRAW,
        )
        self.simTexCoordVBO.itemSize = 2
        self.simTexCoordVBO.numItems = len(self.simPos) / 2

        self.simDampingVBO = Buffer(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, self.simDampingVBO.id)
        glBufferData(
            GL_ARRAY_BUFFER, np.array(self.simDamping, dtype=np.float32), GL_STATIC_DRAW
        )
        self.simDampingVBO.itemSize = 1
        self.simDampingVBO.numItems = len(self.simDamping)

        # set up textures
        self.renderTexture1 = self.initTextureFramebuffer()
        self.renderTexture2 = self.initTextureFramebuffer()

    def on_event(self, event):

        # close game
        if event.type == pygame.QUIT:
            self.running = False
            # exit the program

        # on click, use collision detection to determine which, if any, object from dragItems is selected
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                for index, item in enumerate(self.dragItems):
                    if item.collidepoint(event.pos):
                        # selects item
                        self.selected = index
                        mouse_x, mouse_y = event.pos
                        self.offset[0] = item.x - mouse_x
                        self.offset[1] = item.y - mouse_y

        # on click stop, deselect item
        elif event.type == pygame.MOUSEBUTTONUP:
            # deselects item
            if event.button == 1:
                self.selected = None

        # while mouse moving, if an item from dragItems is selected, move it along with the mouse
        elif event.type == pygame.MOUSEMOTION:
            # moves selected item
            if (
                self.selected is not None
            ):  # selected can be `0` so `is not None` is required, which is more efficient than "!="
                self.dragItems[self.selected][0] = event.pos[0] + self.offset[0]
                self.dragItems[self.selected][1] = event.pos[1] + self.offset[1]

    def on_loop(self):
        # update the simulation at an uncapped framerate
        self.clock.tick_busy_loop()
        self.time += self.clock.get_time()
        # check if items are being changed

        # simulate wave behaviour from one frame to the next

        # swap textures so you can display what was rendered and overwrite the already displayed frame
        rt = self.renderTexture1
        self.renderTexture1 = self.renderTexture2
        self.renderTexture2 = rt

        # set the rendertotexture target to texture1 and its framebuffer to texture1's framebuffer
        rttFramebuffer = self.renderTexture1.framebuffer
        self.rtt = self.renderTexture1
        glBindFramebuffer(GL_FRAMEBUFFER, rttFramebuffer.get_id())

        # determine how to handle walls
        if self.progressive:
            prog = self.mainShaderProg
        else:
            prog = self.mainShaderStat

        # use appropiate compute shader and clear display for sahader to render to
        glUseProgram(prog.get_id())
        glViewport(0, 0, rttFramebuffer.get_width(), rttFramebuffer.get_height())
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # vbos send data to shaders
        glBindBuffer(GL_ARRAY_BUFFER, self.simPosVBO.get_id())
        glVertexAttribPointer(
            prog.vertexPositionAttribute,
            self.simPosVBO.itemSize,
            GL_FLOAT,
            True,
            0,
            0,
        )

        glBindBuffer(GL_ARRAY_BUFFER, self.simTexCoordVBO.get_id())
        glVertexAttribPointer(
            prog.textureCoordAttribute,
            self.simTexCoordVBO.itemSize,
            GL_FLOAT,
            True,
            0,
            0,
        )

        glEnableVertexAttribArray(prog.dampingAttribute)
        glEnableVertexAttribArray(prog.vertexPositionAttribute)
        glEnableVertexAttribArray(prog.textureCoordAttribute)

        glBindBuffer(GL_ARRAY_BUFFER, self.simDampingVBO.get_id())
        glVertexAttribPointer(
            prog.dampingAttribute,
            self.simDampingVBO.itemSize,
            GL_FLOAT,
            True,
            0,
            0,
        )

        # samples pixels from previous frame to use when rendering new frame
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.renderTexture2.get_id())
        glUniform1i(prog.samplerUniform, 0)
        glUniform1f(prog.stepSizeXUniform, 1 / self.width)
        glUniform1f(prog.stepSizeYUniform, 1 / self.height)

        #
        self.setMatrixUniforms(prog)
        glDrawArrays(GL_TRIANGLES, 0, int(self.simPosVBO.numItems))
        glDisableVertexAttribArray(prog.dampingAttribute)
        glDisableVertexAttribArray(prog.vertexPositionAttribute)
        glDisableVertexAttribArray(prog.textureCoordAttribute)

        # draw sources
        for source in self.sources:
            srcCoords = []
            # ready screen for drawing
            self.prep_draw(False)
            # d is used to represent the displacement of the wave at any point
            d = (
                np.sin((self.time - self.startTime) * source.get_freq())
                * source.get_amp()
            )
            glUseProgram(self.drawShader.get_id())
            glVertexAttrib4f(self.drawShader.colourAttribute, d, 0.0, 1.0, 1.0)
            glBindBuffer(GL_ARRAY_BUFFER, self.sourceVBO.get_id())

            # determine position of source
            srcCoords = derectify(source.get_centre(), self.size)
            srcCoords.append(srcCoords[0])
            srcCoords.append((srcCoords[1]) + 1 / self.height)
            srcCoords = np.array(srcCoords, dtype=np.float32)
            glBufferData(GL_ARRAY_BUFFER, srcCoords, GL_STATIC_DRAW)
            glVertexAttribPointer(
                self.drawShader.vertexPositionAttribute,
                self.sourceVBO.itemSize,
                GL_FLOAT,
                True,
                0,
                0,
            )
            glEnableVertexAttribArray(self.drawShader.vertexPositionAttribute)
            self.setMatrixUniforms(self.drawShader)
            glDrawArrays(GL_LINES, 0, 4)
            glDisableVertexAttribArray(self.drawShader.vertexPositionAttribute)

        # draw walls

        for wall in self.walls:
            self.prep_draw(True)
            glBindBuffer(GL_ARRAY_BUFFER, self.sourceVBO.get_id())
            # draw line back on itself, or else one endpoint won't be drawn
            WallCoords = derectify(wall.get_rect(), self.size)
            glLineWidth(1.5)
            glBufferData(
                GL_ARRAY_BUFFER, np.array(WallCoords, dtype=np.float32), GL_STATIC_DRAW
            )
            glVertexAttribPointer(
                self.drawShader.vertexPositionAttribute,
                self.sourceVBO.itemSize,
                GL_FLOAT,
                GL_FALSE,
                0,
                True,
            )

            self.setMatrixUniforms(self.drawShader)
            glEnableVertexAttribArray(self.drawShader.vertexPositionAttribute)
            glDrawArrays(GL_LINE_STRIP, 0, 6)
            glDisableVertexAttribArray(self.drawShader.vertexPositionAttribute)

            glColorMask(True, True, True, True)
            glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def on_render(self):
        glUseProgram(self.displayShader.get_id())
        # set render target to main context (visible window)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # draw result by using shader to decode colour channels

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.renderTexture1.get_id())
        glUniform1i(self.displayShader.samplerUniform, 0)
        glUniform1f(self.displayShader.brightnessUniform, 1)
        glUniform3fv(
            self.displayShader.coloursUniform,
            len(self.colourScheme),
            self.colourScheme,
        )

        self.setMatrixUniforms(self.displayShader)
        glEnableVertexAttribArray(self.displayShader.vertexPositionAttribute)
        glEnableVertexAttribArray(self.displayShader.textureCoordAttribute)
        glDrawArrays(GL_TRIANGLE_STRIP, 0, self.vertexPositionBuffer.numItems)
        glDisableVertexAttribArray(self.displayShader.vertexPositionAttribute)
        glDisableVertexAttribArray(self.displayShader.textureCoordAttribute)

        pygame.display.flip()

    def on_cleanup(self):
        pygame.quit()

    def on_execute(self):
        if self.on_init() == False:
            self.running = False

        # Add starter source and wall
        self.add_source([self.width / 2, self.height / 2], 1, 10, 1)
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
        # adds a wave source
        source = Source(pos, id, frequency, amplitude)
        self.sources.append(source)
        self.add_drag(pos, [8, 8], id)

    def add_wall(self, pos, size, id):
        # adds a wall
        wall = Medium(pos, size, id, 0)
        self.walls.append(wall)
        self.add_drag(pos, size, id)

    def prep_draw(self, wall):
        rttFramebuffer = self.renderTexture1.framebuffer
        glBindFramebuffer(GL_FRAMEBUFFER, rttFramebuffer.get_id())
        glViewport(0, 0, rttFramebuffer.get_width(), rttFramebuffer.get_height())
        glUseProgram(self.drawShader.get_id())
        if wall:
            # blue channel used for walls and media
            glColorMask(False, False, True, False)
            glVertexAttrib4f(self.drawShader.colourAttribute, 0.0, 0.0, 1.0, 1.0)
        else:
            glColorMask(True, True, True, False)

    def load_shader(self, shader_file):
        # opens shader as a text file and compiles it using the compile_shader function
        with open(shader_file, "r") as file:
            shader_source = file.read()
            if shader_source:
                if "fs" in shader_file:
                    shader = compileShader(shader_source, GL_FRAGMENT_SHADER)
                elif "vs" in shader_file:
                    shader = compileShader(shader_source, GL_VERTEX_SHADER)
                else:
                    return None

                glCompileShader(shader)
                if not glGetShaderiv(shader, GL_COMPILE_STATUS):
                    print(
                        f"Shader compile error in {shader_file}: {glGetShaderInfoLog(shader)}"
                    )
                return shader
            else:
                print("Shader not found")
                return None
                # error handling

    def create_shader(self, fs, vs):
        # loads a pair of corresponding shaders using the load_shader function
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

        # attaches fragment and vertex shaders to shader object
        glAttachShader(shader.get_id(), vert_shader)
        glAttachShader(shader.get_id(), frag_shader)
        glLinkProgram(shader.get_id())
        glUseProgram(shader.get_id())

        # sets memory locations for each attribute and uniform of shader object
        shader.vertexPositionAttribute = glGetAttribLocation(shader.get_id(), "aVPos")
        shader.textureCoordAttribute = glGetAttribLocation(shader.get_id(), "aTexCoord")
        shader.dampingAttribute = glGetAttribLocation(shader.get_id(), "aDamping")
        shader.colourAttribute = glGetAttribLocation(shader.get_id(), "aColour")

        shader.pMatrixUniform = glGetUniformLocation(shader.get_id(), "uPMatrix")
        shader.mvMatrixUniform = glGetUniformLocation(shader.get_id(), "uMVMatrix")
        shader.samplerUniform = glGetUniformLocation(shader.get_id(), "uSampler")

        return shader

    def setPosRect(self, x1, y1, x2, y2):
        # sets a rectangular set of coordinates in a format that can be used by shaders effectively
        points = derectify([x2, y1, x1, y1, x2, y2, x1, y1, x2, y2, x1, y2], self.size)
        for i in range(5):
            xi = points[i * 2]
            yi = points[i * 2 + 1]
            self.simPos.append(-1 + (2 * xi / self.width))
            self.simPos.append(-1 + (2 * yi / self.height))
            self.simTexCoord.append(xi / self.width)
            self.simTexCoord.append(1 - yi / self.height)
            damp = self.damping
            # if past the edge of the simulation, set the damping to lower than inside the simulation
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

        rtt = np.empty(1, dtype=np.uint32)
        glCreateTextures(GL_TEXTURE_2D, 1, rtt)
        self.rtt = Texture(int(rtt[0]), fb)
        glBindTexture(GL_TEXTURE_2D, self.rtt.get_id())
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexStorage2D(
            GL_TEXTURE_2D, 1, GL_RGBA8, self.rtt.get_width(), self.rtt.get_height()
        )

        renderbuffer = np.empty(1, dtype=np.uint32)
        glCreateRenderbuffers(1, renderbuffer)
        glBindRenderbuffer(GL_RENDERBUFFER, renderbuffer[0])
        glFramebufferTexture2D(
            GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.rtt.get_id(), 0
        )

        status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        if status != GL_FRAMEBUFFER_COMPLETE:
            print(f"Framebuffer error: {status}")
            return None
        else:
            pixels = np.zeros(4, dtype=float)
            glReadPixels(0, 0, 1, 1, GL_RGBA, GL_FLOAT, pixels)
            if glGetError() != GL_NO_ERROR:
                print("readPixels failed")

        glBindTexture(GL_TEXTURE_2D, 0)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        return self.rtt


if __name__ == "__main__":
    WaveSim = App(title="WaveSim")
    WaveSim.on_execute()
