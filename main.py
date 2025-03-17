import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GL.shaders import compileShader
from conversion import *
from gl_classes import *
from sim_classes import *
import numpy as np

TITLE = "Wave Sim"


class App:
    def __init__(self, title):
        self.running = True  # Flag for main loop
        self.size = self.width, self.height = 1024, 1024  # Window size
        self.windowOffset = 0.04  # Offset of the window from the edge of the screen
        self.caption = TITLE  # Window title
        self.dragItems = []  # List of all draggable items
        self.sources = []  # List of all sources
        self.mediums = []  # List of all walls
        self.numDragItems = 0

        self.inputsSurface = None
        self.dataSurface = None
        self.simDisplaySurface = None
        self.masterSurface = None

        self._offset = [0, 0]
        self._clock = pygame.time.Clock()
        self.sliders = []
        self.actionstack = []
        self.actionstackpointer = 0
        self.text = None
        self.active = 0
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
        self.mainShaderAbs = None  # What gets calculated - walls damp
        self.mainShaderRef = None  # What gets calculated - walls reflect
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

        self.reflective = False  # Flag for simulation running

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
        self.masterSurface = pygame.display.set_mode(
            (self.width + 300, self.height + 200)
        )
        self.simDisplaySurface = pygame.Surface(self.size)
        self.dataSurface = pygame.Surface((self.width + 300, 200))
        self.inputsSurface = pygame.Surface((300, self.height))
        self.masterSurface.blits(
            [
                (self.simDisplaySurface, (0, 0)),
                (self.dataSurface, (0, self.height)),
                (self.inputsSurface, (self.width, 0)),
            ]
        )
        self.running = True
        pygame.font.init()
        self.text = pygame.font.SysFont("calibri", 15)

        # initialise shaders

        # display shader
        self.displayShader = self.create_shader(
            "shaders/display-fs.glsl", "shaders/vs.glsl"
        )
        self.displayShader.brightnessUniform = glGetUniformLocation(
            self.displayShader.get_pid(), "brightness"
        )
        self.displayShader.coloursUniform = glGetUniformLocation(
            self.displayShader.get_pid(), "colours"
        )

        # rendering shader, handling walls without reflections
        self.mainShaderAbs = self.create_shader(
            "shaders/simulate-absorb-fs.glsl", "shaders/vs.glsl"
        )
        self.mainShaderAbs.stepSizeXUniform = glGetUniformLocation(
            self.mainShaderAbs.get_pid(), "stepSizeX"
        )
        self.mainShaderAbs.stepSizeYUniform = glGetUniformLocation(
            self.mainShaderAbs.get_pid(), "stepSizeY"
        )

        # rendering shader, handling walls with reflections
        self.mainShaderRef = self.create_shader(
            "shaders/simulate-reflect-fs.glsl", "shaders/vs.glsl"
        )
        self.mainShaderRef.stepSizeXUniform = glGetUniformLocation(
            self.mainShaderRef.get_pid(), "stepSizeX"
        )
        self.mainShaderRef.stepSizeYUniform = glGetUniformLocation(
            self.mainShaderRef.get_pid(), "stepSizeY"
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
        self.set_area(
            self.windowOffset,
            self.windowOffset,
            1 - self.windowOffset,
            1 - self.windowOffset,
        )

        # sides
        self.set_area(
            1,
            self.windowOffset,
            self.windowOffset,
            1 - self.windowOffset,
        )
        self.set_area(
            1 - self.windowOffset,
            self.windowOffset,
            -1,
            1 - self.windowOffset,
        )
        self.set_area(
            self.windowOffset,
            1,
            1 - self.windowOffset,
            self.windowOffset,
        )
        self.set_area(
            self.windowOffset,
            1 - self.windowOffset,
            1 - self.windowOffset,
            -1,
        )

        # corners
        self.set_area(1, 1, self.windowOffset, self.windowOffset)
        self.set_area(1 - self.windowOffset, 1, 1 - 2, self.windowOffset)
        self.set_area(1, 1 - self.windowOffset, self.windowOffset, -1)
        self.set_area(
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
        self.renderTexture1 = self.create_texture()
        self.renderTexture2 = self.create_texture()

    def on_event(self, event):

        # close game
        if event.type == pygame.QUIT:
            self.running = False
            # exit the program

        # on click, use collision detection to determine which, if any, object from dragItems is selected
        elif event.type == pygame.MOUSEBUTTONDOWN:
            for index, item in enumerate(self.dragItems):
                try:
                    if item.collidepoint(event.pos):
                        for source in self.sources:
                            if source.get_id() == index:
                                self.sliders = self.get_sliders(source)
                        for wall in self.walls:
                            if wall.get_id() == index:
                                self.sliders = self.get_sliders(wall)

                        if event.button == 1:
                            # if left clicked, select item and get its initial coordinates
                            self.selected = index
                            self.active = index
                            self.add_action(
                                ["m", (item.x, item.y), (0, 0), self.selected]
                            )

                            mouse_x, mouse_y = event.pos
                            self._offset[0] = item.x - mouse_x
                            self._offset[1] = item.y - mouse_y
                except:
                    pass

        # on click stop, deselect item
        elif event.type == pygame.MOUSEBUTTONUP:
            # deselects item
            if event.button == 1:
                self.selected = None
                try:
                    self.actionstack[self.actionstackpointer - 1][2] = tuple(
                        [x + y for x, y in zip(event.pos, self._offset)]
                    )
                except:
                    pass

        # while mouse moving, if an item from dragItems is selected, move it along with the mouse
        elif event.type == pygame.MOUSEMOTION:

            # moves selected item
            if (
                self.selected is not None
            ):  # selected can be `0` so `is not None` is required, which is more efficient than "!="
                # moves selected item
                position = (
                    min(max(0, event.pos[0] + self._offset[0]), self.width - 8),
                    min(max(0, event.pos[1] + self._offset[1]), self.height - 8),
                )
                self.move_item(self.selected, position)
            else:
                self._offset = list(event.pos)

        elif event.type == pygame.KEYDOWN:
            match event.key:
                case pygame.K_s:
                    self.add_source(self._offset, 10, 1)
                    self.add_action(
                        ["c", [self._offset], "s", self.sources[-1:][0].get_id()]
                    )
                case pygame.K_z:
                    self.undo()
                case pygame.K_x:
                    self.redo()
                case pygame.K_w:
                    self.add_wall(self._offset, (100, 50), 0)
                    self.add_action(
                        ["c", [self._offset], "w", self.walls[-1:][0].get_id()]
                    )
                case _:
                    pass

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

        # set the render-to-texture target to texture1 and its framebuffer to texture1's framebuffer
        rttFramebuffer = self.renderTexture1.framebuffer
        self.rtt = self.renderTexture1
        glBindFramebuffer(GL_FRAMEBUFFER, rttFramebuffer.get_id())

        # determine how to handle walls
        if self.reflective:
            prog = self.mainShaderRef
        else:
            prog = self.mainShaderAbs

        # use appropiate compute shader and clear display for shader to render to
        glUseProgram(prog.get_pid())
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
        self.set_u_matrices(prog)
        glDrawArrays(GL_TRIANGLES, 0, int(self.simPosVBO.numItems))
        glDisableVertexAttribArray(prog.dampingAttribute)
        glDisableVertexAttribArray(prog.vertexPositionAttribute)
        glDisableVertexAttribArray(prog.textureCoordAttribute)

        # draw sources
        for source in self.sources:
            source.set_zerot(self.startTime)
            srcCoords = []
            # ready screen for drawing
            self.prep_draw(False)
            # d is used to represent the displacement of the wave at any point
            d = source.get_disp(self.time)
            glUseProgram(self.drawShader.get_pid())
            glVertexAttrib4f(self.drawShader.colourAttribute, d, 0.0, 1.0, 1.0)
            glBindBuffer(GL_ARRAY_BUFFER, self.sourceVBO.get_id())

            # determine position of source
            srcCoords = derectify(source.hitbox.get_centre(), self.size)
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
            self.set_u_matrices(self.drawShader)
            glDrawArrays(GL_LINES, 0, 4)
            glDisableVertexAttribArray(self.drawShader.vertexPositionAttribute)

        # draw walls

        for wall in self.mediums:
            self.prep_draw(True)
            glBindBuffer(GL_ARRAY_BUFFER, self.sourceVBO.get_id())
            # draw line back on itself, or else one endpoint won't be drawn
            WallCoords = derectify(wall.hitbox.collide(), self.size)
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

            self.set_u_matrices(self.drawShader)
            glEnableVertexAttribArray(self.drawShader.vertexPositionAttribute)
            glDrawArrays(GL_LINE_STRIP, 0, 6)
            glDisableVertexAttribArray(self.drawShader.vertexPositionAttribute)

            glColorMask(True, True, True, True)
            glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def on_render(self):
        glUseProgram(self.displayShader.get_pid())
        # set render target to main context (visible window)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # draw result by using shader to decode colour channels

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, 0)
        glUniform1i(self.displayShader.samplerUniform, 0)
        glUniform1f(self.displayShader.brightnessUniform, 1)
        glUniform3fv(
            self.displayShader.coloursUniform,
            len(self.colourScheme),
            self.colourScheme,
        )

        self.set_u_matrices(self.displayShader)
        glEnableVertexAttribArray(self.displayShader.vertexPositionAttribute)
        glEnableVertexAttribArray(self.displayShader.textureCoordAttribute)
        glDrawArrays(GL_TRIANGLE_STRIP, 0, self.vertexPositionBuffer.numItems)
        glDisableVertexAttribArray(self.displayShader.vertexPositionAttribute)
        glDisableVertexAttribArray(self.displayShader.textureCoordAttribute)

        self.masterSurface.blit(self._display_surf, (0, 0))
        self.inputsSurface.fill(Color(220, 220, 220))
        self.draw_sliders()
        self.masterSurface.blit(self.inputsSurface, (self.width, 0))

        pygame.display.flip()

    def on_cleanup(self):
        pygame.quit()

    def on_execute(self):
        if self.on_init() == False:
            self.running = False
        # adds a source in the centre of the screen with placeholder values
        self.add_source([self.width / 2, self.height / 2], 10, 1)
        self.add_source([(self.width / 2) + 50, (self.height / 2) + 50], 10, 1)
        self.add_wall([250, 550], [300, 10], 180)

        while self.running:
            for event in pygame.event.get():
                self.on_event(event)
            self.on_loop()
            self.on_render()

        self.on_cleanup()

    def add_drag(self, item):
        # adds a draggable object at position [x,y], of size [width,height]
        self.dragItems.append(item)

    def add_source(self, pos, id, frequency, amplitude):
        # adds a wave source
        hitbox = Hitbox(pos, [8, 8], id)
        source = Source(hitbox, frequency, amplitude)
        self.sources.append(source)
        self.add_drag(source.hitbox.collide())

    def add_wall(self, pos, size, id):
        # adds a wall
        hitbox = Hitbox(pos, size, id)
        wall = Medium(hitbox, 0)
        self.mediums.append(wall)
        self.add_drag(wall.hitbox.collide())

    def add_medium(self, pos, size, id, n):
        # adds a wall
        hitbox = Hitbox(pos, size, id)
        med = Medium(hitbox, n)
        self.mediums.append(med)
        self.add_drag(med.hitbox.collide())

    def prep_draw(self, wall):
        rttFramebuffer = self.renderTexture1.framebuffer
        glBindFramebuffer(GL_FRAMEBUFFER, rttFramebuffer.get_id())
        glViewport(0, 0, rttFramebuffer.get_width(), rttFramebuffer.get_height())
        glUseProgram(self.drawShader.get_pid())
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
                shader = ShaderMain(glCreateProgram(), frag_shader, vert_shader)
            case "shaders/simulate-stat-fs.glsl":
                shader = ShaderSimulate(glCreateProgram(), frag_shader, vert_shader)
            case "shaders/simulate-prog-fs.glsl":
                shader = ShaderSimulate(glCreateProgram(), frag_shader, vert_shader)
            case _:
                shader = Shader(glCreateProgram(), frag_shader, vert_shader)

        program = shader.get_pid()

        # attaches fragment and vertex shaders to shader object
        glAttachShader(program, vert_shader)
        glAttachShader(program, frag_shader)
        glLinkProgram(program)
        glUseProgram(program)

        # sets memory locations for each attribute and uniform of shader object
        shader.vertexPositionAttribute = glGetAttribLocation(program, "aPos")
        shader.textureCoordAttribute = glGetAttribLocation(program, "aTexCoord")
        shader.dampingAttribute = glGetAttribLocation(program, "aDamping")
        shader.colourAttribute = glGetAttribLocation(program, "aCol")

        shader.pMatrixUniform = glGetUniformLocation(program, "pMatrix")
        shader.mvMatrixUniform = glGetUniformLocation(program, "mvMatrix")
        shader.samplerUniform = glGetUniformLocation(program, "sampler")

        return shader

    def set_area(self, x1, y1, x2, y2):
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

    def set_u_matrices(self, shader):
        glUniformMatrix4fv(shader.pMatrixUniform, 1, False, self.pMatrix)
        glUniformMatrix4fv(shader.mvMatrixUniform, 1, False, self.mvMatrix)

    def create_texture(self):
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

    def draw_sliders(self):

        totalcount = len(self.sliders)
        for count in range(totalcount):
            slider = self.sliders[count]
            name = slider[0]
            min = slider[1]
            max = slider[2]
            val = slider[3]
            tall = ((self.height / totalcount) * 0.5 * (count + 1)) + self.height / 4
            pygame.draw.circle(
                self.inputsSurface,
                Color(120, 120, 120),
                (val / (max - min) * 220 + 40, tall),
                5,
            )
            pygame.draw.line(
                self.inputsSurface,
                Color(120, 120, 120),
                (
                    40,
                    tall,
                ),
                (260, tall),
                3,
            )
            box = [x / 2 for x in self.text.size(name)]
            pos = [150 - box[0], tall - box[1] + 15]
            text = self.text.render(name, False, Color(0, 0, 0))
            self.inputsSurface.blit(text, pos)

            min = str(min)
            max = str(max)
            box = [x / 2 for x in self.text.size(min)]
            pos = [40 - box[0], tall - box[1] + 15]
            text = self.text.render(min, True, Color(0, 0, 0))
            self.inputsSurface.blit(text, pos)
            box = [x / 2 for x in self.text.size(max)]
            pos = [260 - box[0], tall - box[1] + 15]
            text = self.text.render(max, True, Color(0, 0, 0))
            self.inputsSurface.blit(text, pos)

    def get_sliders(self, item):
        if isinstance(item, Source):
            sliderA = ["Amplitude", 0, 1, item.get_amp()]
            sliderF = ["Frequency", 1, 100, item.get_freq()]
            return [sliderA, sliderF]
        if isinstance(item, Medium):
            sliderW = ["Width", 1, 300, item.get_size()[0]]
            sliderH = ["Height", 1, 300, item.get_size()[1]]
            sliderN = ["Refractive Index", 0, 1, item.get_refractive_index()]
            sliderR = ["Rotation", 0, 360, item.get_rot()]
            return [sliderW, sliderH, sliderN, sliderR]
        else:
            return

    def undo(self):
        if self.actionstackpointer < 1:
            return
        else:
            try:
                action = self.actionstack[self.actionstackpointer - 1]
            except:
                return
            match action[0]:
                case "m":
                    self.move_item(action[3], action[1])
                case "c":
                    self.dragItems[action[3]] = None
                    match action[2]:
                        case "s":
                            for source in self.sources:
                                if source.get_id() == action[3]:
                                    self.sources.remove(source)
                                    del source
                        case "w":
                            for wall in self.walls:
                                if wall.get_id() == action[3]:
                                    self.walls.remove(wall)
                                    del wall

                case "d":
                    # create item
                    pass
                case _:
                    pass
            self.actionstackpointer -= 1

    def redo(self):
        if self.actionstackpointer == len(self.actionstack):
            return
        else:
            try:
                action = self.actionstack[self.actionstackpointer]
            except:
                return
            match action[0]:
                case "m":
                    self.move_item(action[3], action[2])
                case "c":
                    # create item
                    pass
                case "d":
                    self.dragItems[action[3]] = None
                    for source in self.sources:
                        if source.get_id() == action[3]:
                            self.sources.remove(source)
                            del source
                    pass
                case _:
                    pass
            self.actionstackpointer += 1

    def add_action(self, action):
        if self.actionstackpointer == len(self.actionstack):
            self.actionstack.append(action)
        else:
            self.actionstack[self.actionstackpointer] = action
            self.actionstack = self.actionstack[: self.actionstackpointer + 1]
        self.actionstackpointer += 1

    def move_item(self, item, position):
        self.dragItems[item].x, self.dragItems[item].y = position
        for source in self.sources:
            if source.get_id() == item:
                source.set_pos(position)

        for wall in self.walls:
            if wall.get_id() == item:
                wall.set_pos(position)


if __name__ == "__main__":
    WaveSim = App(title="WaveSim")
    WaveSim.on_execute()
