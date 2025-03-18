import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GL.shaders import compileShader
from conversion import *
from gl_classes import *
from sim_classes import *
import numpy as np

# Constants
TITLE = "Wave Sim"  # Window title
KEYBINDS = {
    "addSource": pygame.K_s,  # Keybind for adding a source
    "addWall": pygame.K_w,  # Keybind for adding a wall
    "undo": pygame.K_z,  # Keybind for undoing the last action
    "redo": pygame.K_x,  # Keybind for redoing the last undone action
    "delete": pygame.K_d,  # Keybind for deleting selected items
}


class App:
    def __init__(self, title):
        # Application state variables
        self.running = (
            True  # Flag to indicate whether the main loop should continue running
        )
        self.size = self.width, self.height = (
            1024,
            1024,
        )  # Dimensions of the application window
        self.windowOffset = 0.04  # Offset of the window from the screen edge
        self.caption = TITLE  # Title of the window
        self.dragItems = []  # List of items that can be dragged around in the UI
        self.sources = []  # List of all sources (wave generators)
        self.mediums = []  # List of all walls or materials that interact with the wave
        self.numDragItems = 0  # Counter for draggable items

        # Surfaces for various parts of the application
        self.inputsSurface = None  # Surface for displaying sliders or input elements
        self.simDisplaySurface = None  # Surface for displaying the simulation itself
        self.masterSurface = None  # Main surface for the window

        # UI elements
        self.sliders = (
            []
        )  # List of sliders for user input (e.g., adjusting wave properties)
        self.actionstack = []  # Stack of actions for undo/redo functionality
        self.actionstackpointer = 0  # Pointer to separate undone and done actions
        self.text = None  # Font information for rendering text using pygame

        # Active/selected item tracking
        self.active = 0  # Index of the most recently interacted with item (default is the first source)
        self.selected = (
            None  # Index of the currently selected item, updated via mouse interaction
        )
        self.offset = [
            0,
            0,
        ]  # Offset of the mouse position relative to the top-left corner of the selected item

        # Undo/Redo action tracking
        self.actionstack = []  # Stack of actions to support undo/redo functionality
        self.actionstackpointer = (
            0  # Pointer indicating current position in the action history
        )

        # Time and simulation settings
        self.clock = pygame.time.Clock()  # Pygame clock for frame rate control
        self.startTime = (
            0  # Timestamp marking when the simulation started (may be adjusted)
        )
        self.time = 0  # Current time in the simulation
        self.wavelength = 10  # Wavelength used in the wave simulation
        self.damping = (
            1.0  # Damping factor to simulate energy loss over time in the wave
        )

        # Shaders for rendering the simulation
        self.displayShader = (
            None  # Shader responsible for displaying the simulation on screen
        )
        self.mainShaderAbs = (
            None  # Shader for calculating wave propagation with absorption by walls
        )
        self.mainShaderRef = None  # Shader for calculating wave reflection off walls
        self.drawShader = None  # Shader for drawing objects onto the screen

        # Vertex Buffer Objects (VBOs) used for rendering and simulation calculations
        self.posVBO = None  # VBO containing positions of objects to be displayed
        self.texCoordVBO = None  # VBO containing texture coordinates for the display
        self.sourceVBO = None  # VBO used for drawing the sources (wave generators)

        # Simulation VBOs (used for wave propagation calculations)
        self.simPosVBO = (
            None  # VBO containing positions used in simulation calculations
        )
        self.simPos = []  # List of positions for the simulation calculation
        self.simTexCoordVBO = (
            None  # VBO containing texture coordinates for the simulation
        )
        self.simTexCoord = []  # List of texture coordinates used in the simulation
        self.simDampingVBO = (
            None  # VBO containing damping values at each vertex in the simulation
        )
        self.simDamping = []  # List of damping values for each vertex in the simulation

        # Simulation state
        self.reflective = False  # Flag indicating if the simulation includes reflective behavior (e.g., walls reflecting waves)

        # Matrices for 3D transformations (though the simulation operates in 2D, OpenGL conventions are followed)
        self.mvMatrix = np.matrix(
            np.identity(4), np.float32
        )  # Model-View matrix for transformations
        self.pMatrix = np.matrix(
            np.identity(4), np.float32
        )  # Projection matrix (identity for 2D)

        # Texture management for offscreen rendering
        self.renderTexture1 = None  # First texture used for rendering
        self.renderTexture2 = None  # Second texture used for rendering
        self.rtt = (
            None  # Render-to-texture flag, tracks which texture is being written to
        )

        # Color scheme for the simulation display
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
        ]  # Normalized RGB values representing colors for walls, sources, mediums and various displacements (positive, negative, neutral)
        # This color scheme is decoded by the main display shader to visualize wave interactions

    def on_init(self):
        """
        Initializes the simulation environment, setting up the necessary pygame window, shaders,
        buffers, and textures for the simulation.

        Attributes used:
             - masterSurface: The surface representing the entire window.
             - simDisplaySurface: The surface representing the simulation display section of the window.
             - inputsSurface: The surface for the input section of the window.
             - displayShader, mainShaderAbs, mainShaderRef, drawShader: Various shaders used in rendering and simulation.
             - vertexPositionBuffer, texCoordVBO, sourceVBO, simPosVBO, simTexCoordVBO, simDampingVBO: Buffers for storing vertex positions, texture coordinates, and simulation data.
             - renderTexture1, renderTexture2: Textures used for rendering the simulation frame by frame.
        """
        # Initialize the Pygame library
        pygame.init()

        # Set up the main window with OpenGL, dividing the window into two sections:
        # The main simulation display and a section for inputs
        self.masterSurface = pygame.display.set_mode(
            (self.width + 300, self.height + 200), pygame.OPENGL
        )
        pygame.display.set_caption(TITLE)  # Set the window title
        self.simDisplaySurface = pygame.Surface(
            self.size
        )  # Surface for simulation display
        self.inputsSurface = pygame.Surface(
            (300, self.height)
        )  # Surface for input controls

        # Blit (copy) the simulation display and input controls onto the master surface
        self.masterSurface.blits(
            [
                (self.simDisplaySurface, (0, 0)),  # Position simulation on the left
                (self.inputsSurface, (self.width, 0)),  # Position inputs on the right
            ]
        )

        # Set up text rendering using Pygame fonts (used for displaying slider values and other text)
        pygame.font.init()
        self.text = pygame.font.SysFont(
            "calibri", 15
        )  # Font for drawing text on the screen

        # Initialize shaders used in the simulation process

        # Shader used for displaying the simulation (display the final result)
        self.displayShader = self.create_shader(
            "shaders/display-fs.glsl", "shaders/vs.glsl"
        )
        # Get the uniform location for controlling brightness in the display shader
        self.displayShader.brightnessUniform = glGetUniformLocation(
            self.displayShader.get_pid(), "brightness"
        )
        # Get the uniform location for setting colors in the display shader
        self.displayShader.coloursUniform = glGetUniformLocation(
            self.displayShader.get_pid(), "colours"
        )

        # Shader for rendering simulation with absorption (walls absorb waves)
        self.mainShaderAbs = self.create_shader(
            "shaders/simulate-absorb-fs.glsl", "shaders/vs.glsl"
        )
        # Get uniform locations for the step size in both x and y directions for the absorption shader
        self.mainShaderAbs.stepSizeXUniform = glGetUniformLocation(
            self.mainShaderAbs.get_pid(), "stepSizeX"
        )
        self.mainShaderAbs.stepSizeYUniform = glGetUniformLocation(
            self.mainShaderAbs.get_pid(), "stepSizeY"
        )

        # Shader for rendering simulation with reflection (walls reflect waves)
        self.mainShaderRef = self.create_shader(
            "shaders/simulate-reflect-fs.glsl", "shaders/vs.glsl"
        )
        # Get uniform locations for the step size in both x and y directions for the reflection shader
        self.mainShaderRef.stepSizeXUniform = glGetUniformLocation(
            self.mainShaderRef.get_pid(), "stepSizeX"
        )
        self.mainShaderRef.stepSizeYUniform = glGetUniformLocation(
            self.mainShaderRef.get_pid(), "stepSizeY"
        )

        # Shader used for drawing lines (used to render lines to the screen)
        self.drawShader = self.create_shader(
            "shaders/draw-fs.glsl", "shaders/draw-vs.glsl"
        )

        # Set up vertex buffer objects (VBOs) for exchanging data between shaders

        # Vertex buffer for storing positions of the corners of the display window
        self.vertexPositionBuffer = Buffer(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, self.vertexPositionBuffer.get_id())
        glBufferData(
            GL_ARRAY_BUFFER,
            np.array([-1, +1, +1, +1, -1, -1, +1, -1], dtype=np.float32),
            GL_STATIC_DRAW,
        )
        # Two values per coordinate (x, y)
        self.vertexPositionBuffer.itemSize = 2
        # Four corners of the display (top-left, top-right, bottom-left, bottom-right)
        self.vertexPositionBuffer.numItems = 4

        # Vertex buffer for storing texture coordinates for the simulation (adjusted for window offset)
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
        # Two values per coordinate (u, v) for texture mapping
        self.texCoordVBO.itemSize = 2
        # Four corners of the texture (top-left, top-right, bottom-left, bottom-right)
        self.texCoordVBO.numItems = 4

        # Set up source VBO (used to represent sources in the simulation)
        self.sourceVBO = Buffer(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, self.sourceVBO.id)
        self.sourceVBO.itemSize = 2  # Two values for the source's position
        self.sourceVBO.numItems = 2  # Only two items (one source)

        # Set the visible area of the simulation based on window offset
        self.set_area(
            self.windowOffset,
            self.windowOffset,
            1 - self.windowOffset,
            1 - self.windowOffset,
        )

        # Define areas representing the sides of the simulation window
        self.set_area(1, self.windowOffset, self.windowOffset, 1 - self.windowOffset)
        self.set_area(
            1 - self.windowOffset,
            self.windowOffset,
            -1,
            1 - self.windowOffset,
        )
        self.set_area(self.windowOffset, 1, 1 - self.windowOffset, self.windowOffset)
        self.set_area(
            self.windowOffset,
            1 - self.windowOffset,
            1 - self.windowOffset,
            -1,
        )

        # Define areas representing the four corners of the simulation window
        self.set_area(1, 1, self.windowOffset, self.windowOffset)
        self.set_area(1 - self.windowOffset, 1, 1 - 2, self.windowOffset)
        self.set_area(1, 1 - self.windowOffset, self.windowOffset, -1)
        self.set_area(
            1 - self.windowOffset,
            1 - self.windowOffset,
            -1,
            -1,
        )

        # Set up buffers for exchanging simulation data between shaders
        self.simPosVBO = Buffer(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, self.simPosVBO.id)
        glBufferData(
            GL_ARRAY_BUFFER,
            np.array(self.simPos, dtype=np.float32),
            GL_STATIC_DRAW,
        )
        self.simPosVBO.itemSize = 2  # Two values per position (x, y)
        self.simPosVBO.numItems = len(self.simPos) / 2  # Number of positions (vertices)

        self.simTexCoordVBO = Buffer(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, self.simTexCoordVBO.id)
        glBufferData(
            GL_ARRAY_BUFFER,
            np.array(self.simTexCoord, dtype=np.float32),
            GL_STATIC_DRAW,
        )
        self.simTexCoordVBO.itemSize = 2  # Two values per texture coordinate (u, v)
        self.simTexCoordVBO.numItems = (
            len(self.simPos) / 2
        )  # Number of texture coordinates

        # Set up the damping VBO to control wave damping at each vertex
        self.simDampingVBO = Buffer(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, self.simDampingVBO.id)
        glBufferData(
            GL_ARRAY_BUFFER, np.array(self.simDamping, dtype=np.float32), GL_STATIC_DRAW
        )
        self.simDampingVBO.itemSize = 1  # One damping value per vertex
        self.simDampingVBO.numItems = len(self.simDamping)  # Number of damping values

        # Set up textures for use in the simulation process (render-to-texture)
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
                            if source.hitbox.get_id() == index:
                                self.sliders = self.get_sliders(source)
                        for wall in self.walls:
                            if wall.hitbox.get_id() == index:
                                self.sliders = self.get_sliders(wall)

                        if event.button == 1:
                            # if left clicked, select item and get its initial coordinates
                            self.selected = index
                            self.active = index
                            self.add_action(
                                ["m", (item.x, item.y), (0, 0), self.selected]
                            )

                            mouse_x, mouse_y = event.pos
                            self.offset[0] = item.x - mouse_x
                            self.offset[1] = item.y - mouse_y
                except:
                    pass

        # on click stop, deselect item
        elif event.type == pygame.MOUSEBUTTONUP:
            # deselects item
            if event.button == 1:
                self.selected = None
                try:
                    self.actionstack[self.actionstackpointer - 1][2] = tuple(
                        [x + y for x, y in zip(event.pos, self.offset)]
                    )
                except:
                    pass

        # while mouse moving, if an item from dragItems is selected, move it along with the mouse
        elif event.type == pygame.MOUSEMOTION:
            self.set_slider()
            # moves selected item
            if (
                self.selected is not None
            ):  # selected can be `0` so `is not None` is required, which is more efficient than "!="
                # moves selected item
                position = (
                    min(max(0, event.pos[0] + self.offset[0]), self.width - 8),
                    min(max(0, event.pos[1] + self.offset[1]), self.height - 8),
                )
                self.move_item(self.selected, position)

            else:
                self.offset = list(event.pos)

        elif event.type == pygame.KEYDOWN:
            if event.key == KEYBINDS["addSource"]:
                self.add_source(self.offset, len(self.dragItems), 10, 1)
                self.add_action(
                    ["c", [self.offset], "s", self.sources[-1:][0].hitbox.get_id()]
                )
            elif event.key == KEYBINDS["undo"]:
                self.undo()
            elif event.key == KEYBINDS["redo"]:
                self.redo()
            elif event.key == KEYBINDS["addWall"]:
                self.add_wall(self.offset, (100, 50), 0, len(self.dragItems))
                self.add_action(
                    ["c", [self.offset], "w", self.mediums[-1:][0].hitbox.get_id()]
                )
            elif event.key == KEYBINDS["delete"]:
                self.dragItems[self.active] = None
                typing = ""
                pos = [0, 0]
                for id, source in enumerate(self.sources):
                    if source.hitbox.get_id() == self.active:
                        pos = source.hitbox.get_pos()
                        self.sources.pop(id)
                        typing = "s"

                for id, med in enumerate(self.mediums):
                    if med.hitbox.get_id() == self.active:
                        pos = med.hitbox.get_pos()
                        self.mediums.pop(id)
                        typing = "w"
                self.add_action(["d", typing, pos])

            else:
                pass

    def on_loop(self):
        """
        Executes the main simulation loop. Updates the simulation at an uncapped framerate, processes wave behavior,
        swaps textures for display, and renders sources and walls to the screen.

        Attributes used:
            clock: The clock used to control the frame rate of the simulation.
            time: The current time in the simulation, used to calculate wave displacement.
            renderTexture1, renderTexture2: The textures used for rendering the simulation.
            sources: A list of wave sources that emit waves in the simulation.
            mediums: A list of walls or objects that interact with waves.
            reflective: A boolean flag indicating whether the simulation should reflect waves off walls.
        """
        # Update the simulation at an uncapped framerate
        self.clock.tick_busy_loop()  # Ensure the loop runs at the maximum speed possible
        self.time += self.clock.get_time()  # Update the time elapsed in the simulation

        # Swap textures to display the current frame while overwriting the previous frame for the next step
        rt = self.renderTexture1  # Temporary swap variable
        self.renderTexture1 = self.renderTexture2  # Swap texture1 with texture2
        self.renderTexture2 = rt  # Swap texture2 with texture1

        # Set the render-to-texture target to texture1 and its framebuffer
        rttFramebuffer = (
            self.renderTexture1.framebuffer
        )  # Get the framebuffer of texture1
        self.rtt = self.renderTexture1  # Set the render target to texture1
        glBindFramebuffer(
            GL_FRAMEBUFFER, rttFramebuffer.get_id()
        )  # Bind the framebuffer for rendering

        # Determine the shader to use based on the reflection setting (reflective or absorbent walls)
        if self.reflective:
            prog = self.mainShaderRef  # Use reflective shader if the wall is reflective
        else:
            prog = (
                self.mainShaderAbs
            )  # Use absorbing shader if the wall absorbs the waves

        # Use the appropriate shader and clear the display to prepare for the next frame
        glUseProgram(prog.get_pid())  # Activate the shader program
        glViewport(
            0, 0, rttFramebuffer.get_width(), rttFramebuffer.get_height()
        )  # Set the viewport
        glClearColor(0.0, 0.0, 0.0, 1.0)  # Set the clear color (black)
        glClear(
            GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT
        )  # Clear the color and depth buffers

        # Send data to the shaders using the vertex buffer objects (VBOs)
        glBindBuffer(
            GL_ARRAY_BUFFER, self.simPosVBO.get_id()
        )  # Bind the simulation positions VBO
        glVertexAttribPointer(
            prog.vertexPositionAttribute,  # Vertex position attribute in the shader
            self.simPosVBO.itemSize,  # Number of items (coordinates per vertex)
            GL_FLOAT,  # Data type
            True,  # Normalize the data
            0,  # Stride (0 means tightly packed)
            0,  # Offset (start at the beginning of the buffer)
        )

        glBindBuffer(
            GL_ARRAY_BUFFER, self.simTexCoordVBO.get_id()
        )  # Bind the texture coordinates VBO
        glVertexAttribPointer(
            prog.textureCoordAttribute,  # Texture coordinate attribute in the shader
            self.simTexCoordVBO.itemSize,  # Number of items (coordinates per vertex)
            GL_FLOAT,  # Data type
            True,  # Normalize the data
            0,  # Stride
            0,  # Offset
        )

        # Enable attributes for damping, position, and texture coordinates
        glEnableVertexAttribArray(
            prog.dampingAttribute
        )  # Enable damping attribute in the shader
        glEnableVertexAttribArray(
            prog.vertexPositionAttribute
        )  # Enable position attribute
        glEnableVertexAttribArray(
            prog.textureCoordAttribute
        )  # Enable texture coordinates attribute

        # Bind the damping VBO and send damping data to the shader
        glBindBuffer(GL_ARRAY_BUFFER, self.simDampingVBO.get_id())
        glVertexAttribPointer(
            prog.dampingAttribute,  # Damping attribute in the shader
            self.simDampingVBO.itemSize,  # Number of items (damping values per vertex)
            GL_FLOAT,  # Data type
            True,  # Normalize
            0,  # Stride
            0,  # Offset
        )

        # Sample pixels from the previous frame to use as input for rendering the new frame
        glActiveTexture(GL_TEXTURE0)  # Activate texture unit 0
        glBindTexture(
            GL_TEXTURE_2D, self.renderTexture2.get_id()
        )  # Bind texture2 as the sampler input
        glUniform1i(
            prog.samplerUniform, 0
        )  # Set the texture unit for the sampler in the shader
        glUniform1f(
            prog.stepSizeXUniform, 1 / self.width
        )  # Pass the step size in the X direction
        glUniform1f(
            prog.stepSizeYUniform, 1 / self.height
        )  # Pass the step size in the Y direction

        # Set up the uniform matrices for the shader
        self.set_u_matrices(prog)

        # Draw the simulation with the provided shader program
        glDrawArrays(
            GL_TRIANGLES, 0, int(self.simPosVBO.numItems)
        )  # Draw the simulation as triangles

        # Disable vertex attribute arrays once done
        glDisableVertexAttribArray(prog.dampingAttribute)
        glDisableVertexAttribArray(prog.vertexPositionAttribute)
        glDisableVertexAttribArray(prog.textureCoordAttribute)

        # Now draw the sources (points emitting waves)
        for source in self.sources:
            source.set_zerot(self.startTime)  # Reset the time for the source
            srcCoords = []  # List to store source coordinates
            self.prep_draw(False)  # Prepare the screen for drawing

            # Calculate the displacement (d) of the wave from the source
            d = source.get_disp(self.time)  # Get the displacement at the current time

            # Use the drawing shader to draw the source
            glUseProgram(self.drawShader.get_pid())
            glVertexAttrib4f(
                self.drawShader.colourAttribute, d, 0.0, 1.0, 1.0
            )  # Set color based on displacement
            glBindBuffer(
                GL_ARRAY_BUFFER, self.sourceVBO.get_id()
            )  # Bind the source VBO

            # Determine the position of the source and adjust for the screen resolution
            srcCoords = derectify(source.hitbox.get_centre(), self.size)
            srcCoords.append(
                srcCoords[0]
            )  # Close the loop for the line (first and last point same)
            srcCoords.append(
                (srcCoords[1]) + 1 / self.height
            )  # Adjust for vertical positioning
            srcCoords = np.array(
                srcCoords, dtype=np.float32
            )  # Convert to numpy array for VBO

            # Update the VBO with the new source coordinates
            glBufferData(GL_ARRAY_BUFFER, srcCoords, GL_STATIC_DRAW)
            glVertexAttribPointer(
                self.drawShader.vertexPositionAttribute,  # Position attribute in the drawing shader
                self.sourceVBO.itemSize,  # Number of items per vertex (2 for x, y)
                GL_FLOAT,  # Data type
                True,  # Normalize
                0,  # Stride
                0,  # Offset
            )
            glEnableVertexAttribArray(
                self.drawShader.vertexPositionAttribute
            )  # Enable vertex position attribute

            # Set the uniform matrices for the drawing shader
            self.set_u_matrices(self.drawShader)

            # Draw the source as a line (from start to end)
            glDrawArrays(GL_LINES, 0, 4)

            # Disable the vertex attribute array once done
            glDisableVertexAttribArray(self.drawShader.vertexPositionAttribute)

        # Now draw the walls (objects that block or reflect the waves)
        for wall in self.mediums:
            self.prep_draw(True)  # Prepare screen for drawing walls
            glBindBuffer(
                GL_ARRAY_BUFFER, self.sourceVBO.get_id()
            )  # Bind the source VBO

            # Draw the wall by drawing a line between the two ends
            WallCoords = derectify(
                wall.hitbox.collide(), self.size
            )  # Get wall's coordinates
            glLineWidth(1.5)  # Set line width for wall

            # Update the VBO with the new wall coordinates
            glBufferData(
                GL_ARRAY_BUFFER, np.array(WallCoords, dtype=np.float32), GL_STATIC_DRAW
            )
            glVertexAttribPointer(
                self.drawShader.vertexPositionAttribute,  # Position attribute in the drawing shader
                self.sourceVBO.itemSize,  # Number of items per vertex (2 for x, y)
                GL_FLOAT,  # Data type
                False,  # Don't normalize
                0,  # Stride
                True,  # Offset
            )

            # Set the uniform matrices for the drawing shader
            self.set_u_matrices(self.drawShader)

            # Enable vertex attribute array and draw the wall as a line strip
            glEnableVertexAttribArray(self.drawShader.vertexPositionAttribute)
            glDrawArrays(
                GL_LINE_STRIP, 0, 6
            )  # Draw the wall as a line strip (between two points)

            # Disable the vertex attribute array once done
            glDisableVertexAttribArray(self.drawShader.vertexPositionAttribute)

            # Restore color mask (so we can draw over the framebuffer)
            glColorMask(True, True, True, True)

        # Unbind the framebuffer (stop rendering to texture, render to screen instead)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def on_render(self):
        """
        Renders the simulation by drawing the final output to the screen.
        """
        glUseProgram(self.displayShader.get_pid())

        # Set render target to the main context (visible window)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Bind texture and set shader uniforms for rendering
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, 0)  # Unbind any previous texture
        glUniform1i(self.displayShader.samplerUniform, 0)  # Set texture unit 0
        glUniform1f(self.displayShader.brightnessUniform, 1)  # Set brightness level
        glUniform3fv(
            self.displayShader.coloursUniform,
            len(self.colourScheme),
            self.colourScheme,  # Use colour scheme
        )

        # Set transformation matrices for the shader
        self.set_u_matrices(self.displayShader)

        # Enable attributes for rendering
        glEnableVertexAttribArray(self.displayShader.vertexPositionAttribute)
        glEnableVertexAttribArray(self.displayShader.textureCoordAttribute)

        # Draw the scene using a triangle strip
        glDrawArrays(GL_TRIANGLE_STRIP, 0, self.vertexPositionBuffer.numItems)

        # Disable attributes after drawing
        glDisableVertexAttribArray(self.displayShader.vertexPositionAttribute)
        glDisableVertexAttribArray(self.displayShader.textureCoordAttribute)

        # Blit simulation output onto the main surface
        self.masterSurface.blit(self.simDisplaySurface, (0, 0))

        # Clear and draw UI elements
        self.inputsSurface.fill(Color(220, 220, 220))
        self.draw_sliders()

        # Add UI elements to the main display
        self.masterSurface.blit(self.inputsSurface, (self.width, 0))

        # Update the display
        pygame.display.flip()

    def on_cleanup(self):
        """
        Cleans up resources and quits the application.
        """
        pygame.quit()

    def on_execute(self):
        """
        Main execution loop for the simulation.
        Initializes, runs, and cleans up the program.
        """
        if self.on_init() == False:
            self.running = False

        # Add initial objects to the simulation
        self.add_source([self.width / 2, self.height / 2], 0, 10, 1)  # Center source
        self.add_source(
            [(self.width / 2) + 50, (self.height / 2) + 50], 1, 10, 1
        )  # Offset source
        self.add_wall([250, 550], [300, 10], 180, 2)  # Static wall

        # Main application loop
        while self.running:
            for event in pygame.event.get():
                self.on_event(event)  # Handle input events
            self.on_loop()  # Update simulation logic
            self.on_render()  # Render the updated scene

        self.on_cleanup()  # Cleanup before exiting

    def add_drag(self, item):
        """
        Adds a draggable object to the simulation.

        Parameters:
            item: The object to be made draggable.
        """
        # Store the draggable object in the list
        self.dragItems.append(item)

    def add_source(self, pos, id, frequency, amplitude):
        """
        Adds a wave source at a given position with specified properties.

        Parameters:
            pos (list): The [x, y] position of the source.
            id (int): Unique identifier for the source.
            frequency (float): Frequency of the wave source.
            amplitude (float): Amplitude of the wave source.
        """
        # Create a hitbox for the wave source with a fixed size of [8, 8]
        hitbox = Hitbox(pos, [8, 8], id)

        # Create a Source object using the hitbox
        source = Source(hitbox, frequency, amplitude)

        # Store the source in the sources list
        self.sources.append(source)

        # Make the source draggable by adding its collision hitbox
        self.add_drag(source.hitbox.collide())

    def add_wall(self, pos, size, rot, id):
        """
        Adds a wall (medium) to the simulation at a specified position and size.

        Parameters:
            pos (list): The [x, y] position of the wall.
            size (list): The [width, height] dimensions of the wall.
            rot (float): Rotation of the wall in degrees.
            id (int): Unique identifier for the wall.
        """
        # Create a hitbox for the wall
        hitbox = Hitbox(pos, size, id)

        # Create a Medium object representing the wall (n=0, meaning no refraction)
        wall = Medium(hitbox, rot, 0)

        # Store the wall in the mediums list
        self.mediums.append(wall)

        # Make the wall draggable by adding its collision hitbox
        self.add_drag(wall.hitbox.collide())

    def add_medium(self, pos, size, id, rot, n):
        """
        Adds a medium (e.g., a different refractive material) to the simulation.

        Parameters:
            pos (list): The [x, y] position of the medium.
            size (list): The [width, height] dimensions of the medium.
            id (int): Unique identifier for the medium.
            rot (float): Rotation of the medium in degrees.
            n (float): Refractive index of the medium.
        """
        # Create a hitbox for the medium
        hitbox = Hitbox(pos, size, id)

        # Create a Medium object with the given properties
        med = Medium(hitbox, rot, n)

        # Store the medium in the mediums list
        self.mediums.append(med)

        # Make the medium draggable by adding its collision hitbox
        self.add_drag(med.hitbox.collide())

    def prep_draw(self, wall):
        """
        Configures the OpenGL state, including the color mask, before any drawing happens.
        The color mask is used to control which color channels are affected by the drawing operation.

        Arguments Used:
            wall (bool): Flag indicating if the object being drawn is a wall.
                        - If True, it sets up the color mask for walls (blue channel).
                        - If False, it sets up the color mask for general drawing.
        """
        # Bind the framebuffer to render to the texture
        rttFramebuffer = self.renderTexture1.framebuffer
        glBindFramebuffer(GL_FRAMEBUFFER, rttFramebuffer.get_id())

        # Set the viewport size to match the framebuffer dimensions
        glViewport(0, 0, rttFramebuffer.get_width(), rttFramebuffer.get_height())

        # Use the drawing shader program
        glUseProgram(self.drawShader.get_pid())

        # If drawing a wall, use the blue channel for walls/mediums, else allow all channels
        if wall:
            # Blue channel for walls and media
            glColorMask(False, False, True, False)
            glVertexAttrib4f(self.drawShader.colourAttribute, 0.0, 0.0, 1.0, 1.0)
        else:
            # Allow all color channels except alpha
            glColorMask(True, True, True, False)

    def load_shader(self, shader_file):
        """
        Reads the shader file, determines the shader type (fragment or vertex),
        compiles the shader, and checks for compile errors. If the compilation fails, it prints an error message.

        Arguments Used:
            shader_file (str): The file path to the shader source file.

        Returns:
            int or None: Returns the compiled shader object if successful, or None if there was an error.
        """
        # Open the shader file and read its contents
        with open(shader_file, "r") as file:
            shader_source = file.read()

            # Check if shader source exists
            if shader_source:
                # Determine shader type (fragment or vertex) based on file extension
                if "fs" in shader_file:
                    shader = compileShader(shader_source, GL_FRAGMENT_SHADER)
                elif "vs" in shader_file:
                    shader = compileShader(shader_source, GL_VERTEX_SHADER)
                else:
                    return None  # Unknown shader type

                # Compile the shader and check for errors
                glCompileShader(shader)
                if not glGetShaderiv(shader, GL_COMPILE_STATUS):
                    print(
                        f"Shader compile error in {shader_file}: {glGetShaderInfoLog(shader)}"
                    )
                    return None

                return shader
            else:
                print("Shader source not found")
                return None

    def create_shader(self, fs, vs):
        """
        Creates a shader program by loading and compiling the corresponding fragment and vertex shaders.

        Arguments Used:
            fs (str): Path to the fragment shader file.
            vs (str): Path to the vertex shader file.

        Returns:
            Shader: Returns a Shader object containing the compiled shader program, or None if creation fails.

        This function loads both the fragment and vertex shaders, compiles them, and creates a shader program.
        It then retrieves the program's attribute and uniform locations.
        """
        # Load and compile the fragment shader
        try:
            frag_shader = self.load_shader(fs)
        except:
            print("Error: Fragment shader not found")
            return None

        # Load and compile the vertex shader
        try:
            vert_shader = self.load_shader(vs)
        except:
            print("Error: Vertex shader not found")
            return None

        # Create the appropriate shader class based on the fragment shader
        match fs:
            case "shaders/display-fs.glsl":
                shader = ShaderMain(glCreateProgram(), frag_shader, vert_shader)
            case "shaders/simulate-stat-fs.glsl" | "shaders/simulate-prog-fs.glsl":
                shader = ShaderSimulate(glCreateProgram(), frag_shader, vert_shader)
            case _:
                shader = Shader(glCreateProgram(), frag_shader, vert_shader)

        program = shader.get_pid()

        # Attach the vertex and fragment shaders to the program
        glAttachShader(program, vert_shader)
        glAttachShader(program, frag_shader)

        # Link the shader program
        glLinkProgram(program)
        glUseProgram(program)

        # Retrieve and store attribute locations
        shader.vertexPositionAttribute = glGetAttribLocation(program, "aPos")
        shader.textureCoordAttribute = glGetAttribLocation(program, "aTexCoord")
        shader.dampingAttribute = glGetAttribLocation(program, "aDamping")
        shader.colourAttribute = glGetAttribLocation(program, "aCol")

        # Retrieve and store uniform locations
        shader.pMatrixUniform = glGetUniformLocation(program, "pMatrix")
        shader.mvMatrixUniform = glGetUniformLocation(program, "mvMatrix")
        shader.samplerUniform = glGetUniformLocation(program, "sampler")

        return shader

    def set_area(self, x1, y1, x2, y2):
        """
        Adjusts the coordinates to fit within the simulation space and sets the texture coordinates
        and damping values for the rectangular area, storing the results in the simulation buffers.
        Damping is adjusted at the boundaries of the simulation area to reduce wave intensity at the edges.

        Arguments Used:
            x1 (float): The x-coordinate of the first corner of the rectangle.
            y1 (float): The y-coordinate of the first corner of the rectangle.
            x2 (float): The x-coordinate of the opposite corner of the rectangle.
            y2 (float): The y-coordinate of the opposite corner of the rectangle.
        """
        # Convert rectangle coordinates to normalized device space
        points = derectify([x2, y1, x1, y1, x2, y2, x1, y1, x2, y2, x1, y2], self.size)

        for i in range(5):
            xi = points[i * 2]
            yi = points[i * 2 + 1]

            # Adjust coordinates to fit into normalized device space [-1, 1]
            self.simPos.append(-1 + (2 * xi / self.width))
            self.simPos.append(-1 + (2 * yi / self.height))

            # Set texture coordinates, flipped vertically
            self.simTexCoord.append(xi / self.width)
            self.simTexCoord.append(1 - yi / self.height)

            # Set damping value, reduced at boundaries
            damp = self.damping
            if xi == 1 or yi == 1 or xi == self.width - 1 or yi == self.height - 1:
                damp = damp * 0.91
            self.simDamping.append(damp)

    def set_u_matrices(self, shader):
        """
        Sends the current projection and model-view matrices to the shader,
        which are necessary for operating on the opengl pipeline.

        Arguments Used:
            shader (Shader): The shader program that requires the matrices.
        """
        glUniformMatrix4fv(shader.pMatrixUniform, 1, False, self.pMatrix)
        glUniformMatrix4fv(shader.mvMatrixUniform, 1, False, self.mvMatrix)

    def create_texture(self):
        """
        Creates a framebuffer and a texture, setting up the necessary parameters for rendering to the texture.
        Also checks if the framebuffer and texture are correctly set up and verifies that no
        OpenGL errors occurred.

        Returns:
            Texture: The created texture object, or None if an error occurred during creation.
        """
        # Create an empty framebuffer and bind it
        framebuffer = np.empty(1, dtype=np.uint32)
        glCreateFramebuffers(1, framebuffer)
        fb = Framebuffer(framebuffer[0])
        glBindFramebuffer(GL_FRAMEBUFFER, fb.get_id())
        fb.set_width(self.width)
        fb.set_height(self.height)

        # Create an empty texture and bind it
        rtt = np.empty(1, dtype=np.uint32)
        glCreateTextures(GL_TEXTURE_2D, 1, rtt)
        self.rtt = Texture(int(rtt[0]), fb)
        glBindTexture(GL_TEXTURE_2D, self.rtt.get_id())

        # Set texture filtering to nearest neighbor
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

        # Set texture wrapping to clamp to border to avoid repetition
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)

        # Allocate storage for the texture
        glTexStorage2D(
            GL_TEXTURE_2D, 1, GL_RGBA8, self.rtt.get_width(), self.rtt.get_height()
        )

        # Create a renderbuffer for depth/stencil attachment
        renderbuffer = np.empty(1, dtype=np.uint32)
        glCreateRenderbuffers(1, renderbuffer)
        glBindRenderbuffer(GL_RENDERBUFFER, renderbuffer[0])

        # Attach the texture to the framebuffer
        glFramebufferTexture2D(
            GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.rtt.get_id(), 0
        )

        # Check the framebuffer status for completeness
        status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        if status != GL_FRAMEBUFFER_COMPLETE:
            print(f"Framebuffer error: {status}")
            return None

        # Read a single pixel to check if the framebuffer is correctly set up
        pixels = np.zeros(4, dtype=float)
        glReadPixels(0, 0, 1, 1, GL_RGBA, GL_FLOAT, pixels)
        if glGetError() != GL_NO_ERROR:
            print("glReadPixels failed")

        # Unbind the texture and framebuffer
        glBindTexture(GL_TEXTURE_2D, 0)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        return self.rtt

    def draw_sliders(self):
        """
        Draws sliders for user interaction on the input surface.
        Each slider represents a configurable parameter (e.g., amplitude, frequency).
        """

        totalcount = len(self.sliders)  # Total number of sliders

        for count in range(totalcount):
            slider = self.sliders[count]
            name = slider[0]  # Slider label
            min_val = slider[1]  # Minimum value of the slider
            max_val = slider[2]  # Maximum value of the slider
            val = slider[3]  # Current value of the slider

            # Calculate vertical position for the slider
            tall = ((self.height / totalcount) * 0.5 * (count + 1)) + self.height / 4

            # Draw slider handle (circular marker)
            pygame.draw.circle(
                self.inputsSurface,
                Color(120, 120, 120),
                (val / (max_val - min_val) * 220 + 40, tall),  # Position based on value
                5,  # Circle radius
            )

            # Draw slider track (horizontal line)
            pygame.draw.line(
                self.inputsSurface,
                Color(120, 120, 120),
                (40, tall),  # Start position
                (260, tall),  # End position
                3,  # Line thickness
            )

            # Render slider label
            text_size = [x / 2 for x in self.text.size(name)]
            text_pos = [150 - text_size[0], tall - text_size[1] + 15]
            text = self.text.render(name, False, Color(0, 0, 0))
            self.inputsSurface.blit(text, text_pos)

            # Render minimum value label
            min_text = self.text.render(str(min_val), True, Color(0, 0, 0))
            min_size = [x / 2 for x in self.text.size(str(min_val))]
            min_pos = [40 - min_size[0], tall - min_size[1] + 15]
            self.inputsSurface.blit(min_text, min_pos)

            # Render maximum value label
            max_text = self.text.render(str(max_val), True, Color(0, 0, 0))
            max_size = [x / 2 for x in self.text.size(str(max_val))]
            max_pos = [260 - max_size[0], tall - max_size[1] + 15]
            self.inputsSurface.blit(max_text, max_pos)

    def get_sliders(self, item):
        """
        Returns a list of sliders corresponding to the given item type.
        The sliders define adjustable properties such as amplitude and frequency for sources,
        or width, height, refractive index, and rotation for mediums.

        Parameters:
            item: The object (Source or Medium) for which sliders are generated.

        Returns:
            list: A list of sliders with their name, min/max values, and current value.
        """
        if isinstance(item, Source):
            return [
                ["Amplitude", 0, 1, item.get_amp()],
                ["Frequency", 1, 100, item.get_freq()],
            ]
        elif isinstance(item, Medium):
            return [
                ["Width", 1, 300, item.get_size()[0]],
                ["Height", 1, 300, item.get_size()[1]],
                ["Refractive Index", 0, 1, item.get_refractive_index()],
                ["Rotation", 0, 360, item.get_rot()],
            ]
        else:
            return []  # Return an empty list if the item is not a Source or Medium

    def set_slider(self):
        """
        Updates the value of a slider based on the user's mouse position.
        This allows interactive adjustment of properties by dragging the slider.

        The function checks if the mouse cursor is within the slider's vertical range
        and updates the corresponding value accordingly.
        """
        totalcount = len(self.sliders)  # Number of sliders
        pos = self.offset  # Mouse position offset

        for count in range(totalcount):
            slider = self.sliders[count]
            min_val = slider[1]  # Minimum slider value
            max_val = slider[2]  # Maximum slider value

            # Calculate the vertical position of the slider
            tall = ((self.height / totalcount) * 0.5 * (count + 1)) + self.height / 4

            # Define the interactive height range for detecting user input
            maxheight = tall + 5
            minheight = tall - 5

            # Check if the mouse is within the slider's vertical bounds
            if minheight < pos[1] < maxheight:
                # Check if the mouse is within the horizontal slider track
                if 0 < pos[0] - self.width - 40 < 260:
                    # Update slider value based on mouse X position
                    slider[3] = (pos[0] - self.width - 40) * (max_val - min_val) / 220

    def undo(self):
        """
        Undoes the last action recorded in the action stack.

        This function moves an item back to its previous position (if moved),
        removes an item (if created), or restores an item (if deleted).

        The action type is determined by the first element in the action tuple:
            - 'm' (move): Moves the item back to its previous position.
            - 'c' (create): Deletes the most recently created item.
            - 'd' (delete): Restores the most recently deleted item.
        """
        if self.actionstackpointer < 1:
            return  # No actions to undo

        try:
            action = self.actionstack[self.actionstackpointer - 1]
        except IndexError:
            return  # Prevent accessing an invalid action

        match action[0]:
            case "m":  # Move action: Move item back to previous position
                self.move_item(action[3], action[1])

            case "c":  # Create action: Remove the created item
                self.dragItems[action[3]] = None
                match action[2]:
                    case "s":  # Remove a source
                        for i, source in enumerate(self.sources):
                            if source.hitbox.get_id() == action[3]:
                                self.sources.pop(i)
                                break
                    case "w":  # Remove a wall
                        for i, wall in enumerate(self.mediums):
                            if wall.hitbox.get_id() == action[3]:
                                self.mediums.pop(i)
                                break

            case "d":  # Delete action: Restore deleted item
                if action[1] == "s":
                    self.add_source(action[2], len(self.dragItems), 10, 1)
                elif action[1] == "w":
                    self.add_wall(action[2], [300, 300], 0, len(self.dragItems))

        self.actionstackpointer -= 1  # Update pointer to reflect the undone action

    def redo(self):
        """
        Redoes the last undone action from the action stack.

        The action type is determined by the first element in the action tuple:
            - 'm' (move): Moves the item back to its final position.
            - 'c' (create): Re-adds an item that was deleted.
            - 'd' (delete): Deletes an item again after undoing its removal.
        """
        if self.actionstackpointer == len(self.actionstack):
            return  # No actions to redo

        try:
            action = self.actionstack[self.actionstackpointer]
        except IndexError:
            return  # Prevent accessing an invalid action

        match action[0]:
            case "m":  # Move action: Move item back to final position
                self.move_item(action[3], action[2])

            case "c":  # Create action: Restore item that was undone
                if action[2] == "s":
                    self.add_source(action[1], action[3], 10, 1)
                elif action[2] == "w":
                    self.add_wall(action[1], [300, 300], 0, action[3])

            case "d":  # Delete action: Remove item again
                self.dragItems[action[3]] = None
                match action[2]:
                    case "s":  # Delete a source again
                        for i, source in enumerate(self.sources):
                            if source.hitbox.get_id() == action[3]:
                                self.sources.pop(i)
                                break
                    case "w":  # Delete a wall again
                        for i, wall in enumerate(self.mediums):
                            if wall.hitbox.get_id() == action[3]:
                                self.mediums.pop(i)
                                break

        self.actionstackpointer += 1  # Update pointer to reflect the redone action

    def add_action(self, action):
        """
        Adds a new action to the action stack.

        If the stack pointer is at the end of the list, the action is appended.
        Otherwise, the stack is truncated at the pointer before adding the new action.

        Parameters:
            action (tuple): The action to be recorded.
        """
        if self.actionstackpointer == len(self.actionstack):
            self.actionstack.append(action)
        else:
            self.actionstack[self.actionstackpointer] = action
            self.actionstack = self.actionstack[: self.actionstackpointer + 1]

        self.actionstackpointer += 1  # Update pointer to reflect the added action

    def move_item(self, item, position):
        """
        Moves an item (source or wall) to a new position.

        Parameters:
            item (int): The ID of the item to be moved.
            position (tuple): The new (x, y) coordinates for the item.
        """
        self.dragItems[item].x, self.dragItems[item].y = position

        for source in self.sources:
            if source.hitbox.get_id() == item:
                source.set_pos(position)

        for wall in self.mediums:
            if wall.hitbox.get_id() == item:
                wall.set_pos(position)


# Run the application when this script is executed directly
if __name__ == "__main__":
    global WaveSim
    WaveSim = App(title="WaveSim")
    WaveSim.on_execute()
