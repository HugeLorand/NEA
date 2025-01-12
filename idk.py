import pygame
from OpenGL.GL import *
import numpy as np

# Initialize pygame
pygame.init()

# Simulation parameters
WIDTH, HEIGHT = 800, 600
GRID_SIZE = 200
WAVE_SPEED = 0.03
DAMPING = 0.998
REFRACTION_SPEED = 0.02  # Wave speed in the refraction zone
SOURCES = [{'pos': [100, 100], 'velocity': [0.1, 0.0]}]  # Moving sources
REFLECTORS = [{'start': [50, 50], 'end': [150, 50], 'movable': True}]  # Reflective surfaces

# OpenGL setup
pygame.display.set_mode((WIDTH, HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)
glViewport(0, 0, WIDTH, HEIGHT)
glOrtho(0, GRID_SIZE, 0, GRID_SIZE, -1, 1)
glClearColor(0.0, 0.0, 0.0, 1.0)
glShadeModel(GL_SMOOTH)

# Initialize wave grid
height_map = np.zeros((GRID_SIZE, GRID_SIZE))
velocity_map = np.zeros((GRID_SIZE, GRID_SIZE))
refraction_zone = np.zeros((GRID_SIZE, GRID_SIZE), dtype=bool)

# Define a refraction zone
refraction_zone[100:150, 100:150] = True

# Function to update the wave simulation
def update_wave():
    global height_map, velocity_map

    # Compute Laplacian
    laplacian = (
        np.roll(height_map, 1, axis=0) +
        np.roll(height_map, -1, axis=0) +
        np.roll(height_map, 1, axis=1) +
        np.roll(height_map, -1, axis=1) -
        4 * height_map
    )

    # Update velocity and height with refraction zones
    wave_speed = np.where(refraction_zone, REFRACTION_SPEED, WAVE_SPEED)
    velocity_map += wave_speed * laplacian
    velocity_map *= DAMPING
    height_map += velocity_map

    # Add sources
    for source in SOURCES:
        x, y = map(int, source['pos'])
        height_map[x, y] += np.sin(pygame.time.get_ticks() * 0.01)
        source['pos'][0] += source['velocity'][0]
        source['pos'][1] += source['velocity'][1]

    # Handle moving sources hitting boundaries
    for source in SOURCES:
        if source['pos'][0] < 0 or source['pos'][0] >= GRID_SIZE:
            source['velocity'][0] *= -1
        if source['pos'][1] < 0 or source['pos'][1] >= GRID_SIZE:
            source['velocity'][1] *= -1

    # Reflective boundaries
    for reflector in REFLECTORS:
        start, end = reflector['start'], reflector['end']
        if reflector['movable']:
            # Example movement for reflectors
            start[0] += 0.1
            end[0] += 0.1
            if start[0] >= GRID_SIZE or end[0] >= GRID_SIZE:
                start[0] -= 0.1
                end[0] -= 0.1

        # Apply reflection logic
        for x in range(int(start[0]), int(end[0]) + 1):
            for y in range(int(start[1]), int(end[1]) + 1):
                if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                    height_map[x, y] = -height_map[x, y]  # Reflect wave

# Function to draw the wave
def draw_wave():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    glBegin(GL_POINTS)
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            value = height_map[x, y]
            color = (value + 1) / 2  # Normalize to [0, 1]
            glColor3f(color, color, color)
            glVertex2f(x, y)
    glEnd()

    # Draw reflectors
    glColor3f(1.0, 0.0, 0.0)
    glBegin(GL_LINES)
    for reflector in REFLECTORS:
        start, end = reflector['start'], reflector['end']
        glVertex2f(start[0], start[1])
        glVertex2f(end[0], end[1])
    glEnd()

    # Highlight refraction zone
    glColor4f(0.0, 0.0, 1.0, 0.3)
    glBegin(GL_QUADS)
    for x in range(GRID_SIZE - 1):
        for y in range(GRID_SIZE - 1):
            if refraction_zone[x, y]:
                glVertex2f(x, y)
                glVertex2f(x + 1, y)
                glVertex2f(x + 1, y + 1)
                glVertex2f(x, y + 1)
    glEnd()

    pygame.display.flip()

# User interaction to add/remove sources and reflectors
def handle_user_input():
    keys = pygame.key.get_pressed()
    mouse_buttons = pygame.mouse.get_pressed()
    mouse_pos = pygame.mouse.get_pos()

    grid_x = int(mouse_pos[0] / (WIDTH / GRID_SIZE))
    grid_y = int((HEIGHT - mouse_pos[1]) / (HEIGHT / GRID_SIZE))

    if mouse_buttons[0]:  # Left click to add a source
        SOURCES.append({'pos': [grid_x, grid_y], 'velocity': [0.0, 0.0]})
    elif mouse_buttons[2]:  # Right click to remove a source
        SOURCES[:] = [s for s in SOURCES if not (int(s['pos'][0]) == grid_x and int(s['pos'][1]) == grid_y)]

    if keys[pygame.K_r]:  # Press 'R' to add a movable reflector
        REFLECTORS.append({'start': [grid_x - 5, grid_y], 'end': [grid_x + 5, grid_y], 'movable': True})
    elif keys[pygame.K_d]:  # Press 'D' to remove a reflector
        REFLECTORS[:] = [r for r in REFLECTORS if not (r['start'][0] <= grid_x <= r['end'][0] and r['start'][1] == grid_y)]

# Main loop
running = True
clock = pygame.time.Clock()
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    handle_user_input()
    update_wave()
    draw_wave()
    clock.tick(60)

pygame.quit()