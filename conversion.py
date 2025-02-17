import pygame
import numpy as np


def rectify(corners, displaysize):

    # Convert normalized OpenGL corners into a pygame.Rect object
    # `corners` is a list of two (x, y) tuples in normalized OpenGL coordinates.
    # `displaysize` is the size of the display (width, height).

    # Convert normalized OpenGL coordinates to pixel coordinates
    x1 = (corners[0][0] + 1) * (displaysize[0] / 2)
    y1 = (corners[0][1] + 1) * (displaysize[1] / 2)
    x2 = (corners[1][0] + 1) * (displaysize[0] / 2)
    y2 = (corners[1][1] + 1) * (displaysize[1] / 2)

    # Ensure proper ordering for pygame.Rect
    rect = pygame.Rect(
        min(x1, x2),  # Top-left corner x
        min(y1, y2),  # Top-left corner y
        abs(x2 - x1),  # Width
        abs(y2 - y1),  # Height
    )
    return rect


def derectify(rect, displaysize):
    # Convert Pygame Rect to array of coordinates
    match len(rect):
        case 2:
            return (
                (2 * rect[0] / displaysize[0]) - 1,
                (2 * rect[1] / displaysize[1]) - 1,
            )
        case 4:
            corners = [
                (rect[0], rect[1]),  # Top-left
                (rect[0] + rect[2], rect[1]),  # Top-right
                (rect[0], rect[1] + rect[3]),  # Bottom-left
                (rect[0] + rect[2], rect[1] + rect[3]),  # Bottom-right
            ]
            # Normalise coordinates so they can be used by OpenGL
            corners = [
                (2 * corner[0] / displaysize[0] - 1, 2 * corner[1] / displaysize[1] - 1)
                for corner in corners
            ]
            return [((corner[0]), (corner[1]), 0) for corner in corners]
        case _:
            raise ValueError("Coord or Rect must have 2 or 4 elements")


def invmat(matrix):
    # check if the matrix is square
    if matrix.shape[0] != matrix.shape[1]:
        raise ValueError("The matrix must be square")
    # check if the determinant of the matrix is zero
    if np.linalg.det(matrix) == 0:
        raise ValueError("Determinant of the matrix is zero")
    # return the inverse of the matrix
    return np.linalg.inv(matrix)


def mat4tomat3(matrix):
    # drop the last row and column
    return matrix[:3, :3]
