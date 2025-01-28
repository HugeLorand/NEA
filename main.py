import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GL.shaders import compileShader, compileProgram
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
        self._running = True
        self._display_surf = None
        self._size = self.weight, self.height = 1080, 1080
        self._caption = title
        self._dragitems = []
        self._sources = []
        self._walls = []
        self._selected = None
        self._offset = [0, 0]
        self._clock = pygame.time.Clock()
        self.start_time = time.time()
        self._wavelength = 10
        self._wave_texture = None

    def on_init(self):
        pygame.init()
        self._display_surf = pygame.display.set_mode(
            self._size, pygame.DOUBLEBUF | pygame.OPENGL
        )
        self._caption = pygame.display.set_caption(self._caption)
        gluPerspective(45, (self.weight / self.height), 0.1, 50.0)
        glTranslatef(0.0, 0.0, -5)
        self._running = True

    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # goes through _dragitems and selects an item that collides with the mouse, if available
                for index, item in enumerate(self._dragitems):
                    if item[0].collidepoint(event.pos):
                        self._selected = index
                        mouse_x, mouse_y = event.pos
                        self._offset[0] = item[0].x - mouse_x
                        self._offset[1] = item[0].y - mouse_y

        elif event.type == pygame.MOUSEBUTTONUP:
            # deselects item
            if event.button == 1:
                self._selected = None

        elif event.type == pygame.MOUSEMOTION:
            if (
                self._selected is not None
            ):  # selected can be `0` so `is not None` is required, which is more efficient than "!="
                # moves selected item
                self._dragitems[self._selected][0].x = event.pos[0] + self._offset[0]
                self._dragitems[self._selected][0].y = event.pos[1] + self._offset[1]

    def on_loop(self):
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

        # Create the wave texture
        self._wave_texture = self.create_wave_texture()  # Generate the texture

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

    def add_drag(self, pos, size, color):
        # adds a draggable object at position [x,y], of size [width,height]
        item = item_draggable.Item(pos, size, color)
        self._dragitems.append(item.shape())

    def add_source(self, pos, frequency, wavelength, amplitude, color, decay):
        source = Source(pos, [10, 10], frequency, wavelength, amplitude, color, decay)
        self._sources.append(source)
        self.add_drag(pos, [10, 10], color)

    def add_wall(self, start_pos, end_pos, color):
        wall = Wall(start_pos, end_pos, color)
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

    def load_compute_shader(self, shader_file):
        with open(shader_file, "r") as f:
            shader_source = f.read()

        shader = compileShader(shader_source, GL_COMPUTE_SHADER)
        return shader

    def create_shader_program(self):
        shader = self.load_compute_shader("wave_compute_shader.glsl")
        program = compileProgram(shader)
        return program

    def create_wave_texture(self):
        self._wave_texture = glGenTextures(1)  # Generate the texture ID
        glBindTexture(GL_TEXTURE_2D, self._wave_texture)  # Bind it to GL_TEXTURE_2D

        # Initialize texture data with refractive index (blue channel)
        # For simplicity, we'll initialize with a default refractive index (e.g., 1.0 for air)
        initial_data = np.zeros(
            (self.height, self.weight, 4), dtype=np.float32
        )  # RGBA texture
        for i in range(self.height):
            for j in range(self.weight):
                # Set a default refractive index in the blue channel (for example, 1.0)
                initial_data[i][j][2] = 1.0  # Blue channel for refractive index

        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA32F,
            self.weight,
            self.height,
            0,
            GL_RGBA,
            GL_FLOAT,
            initial_data,
        )

        # Set texture parameters (e.g., linear filtering and wrapping)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

        return self._wave_texture  # Return the texture ID

    def dispatch_compute_shader(
        self, program, texture, width, height, time, sources, wavelength
    ):
        glUseProgram(program)

        # Correctly bind the texture to the shader
        glBindImageTexture(0, texture, 0, GL_FALSE, 0, GL_WRITE_ONLY, GL_RGBA32F)

        source_positions = [source.getpos() for source in sources]
        source_amplitudes = [source.getamp() for source in sources]

        # Flatten the source positions into pairs of floats (2 values per source)
        source_positions_flat = [coord for pos in source_positions for coord in pos]

        # Ensure the correct uniform location and pass the flattened array of floats
        location = glGetUniformLocation(program, "source_positions")
        if location != -1:  # Make sure the location is valid
            glUniform2fv(
                location,
                len(source_positions),
                np.array(source_positions_flat, dtype=np.float32),
            )
        else:
            print("Uniform 'source_positions' not found in the shader.")

        # Pass other uniforms to the shader
        glUniform1f(glGetUniformLocation(program, "time"), time)
        glUniform1fv(
            glGetUniformLocation(program, "source_amplitude"),
            len(source_amplitudes),
            source_amplitudes,
        )
        glUniform1f(glGetUniformLocation(program, "wavelength"), wavelength)

        # Dispatch the compute shader (dividing work into 16x16 work groups)
        glDispatchCompute(width // 16, height // 16, 1)
        glMemoryBarrier(GL_SHADER_IMAGE_ACCESS_BARRIER_BIT)

    def render_wave_texture(self):
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0)
        glVertex2f(0, 0)
        glTexCoord2f(1, 0)
        glVertex2f(self.weight, 0)
        glTexCoord2f(1, 1)
        glVertex2f(self.weight, self.height)
        glTexCoord2f(0, 1)
        glVertex2f(0, self.height)
        glEnd()


if __name__ == "__main__":
    WaveSim = App(title="WaveSim")
    WaveSim.on_execute()
