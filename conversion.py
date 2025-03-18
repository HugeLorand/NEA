import pygame
import numpy as np
from typing import List, Tuple


def rectify(
    corners: List[Tuple[float, float]], displaysize: Tuple[int, int]
) -> pygame.Rect:
    """
    Convert normalized OpenGL corners into a pygame.Rect object.

    Args:
        corners (List[Tuple[float, float]]): List of two (x, y) tuples in normalized OpenGL coordinates.
        displaysize (Tuple[int, int]): The size of the display (width, height).

    Returns:
        pygame.Rect: The rect representing the pixel coordinates of the input corners.
    """
    # Convert normalized OpenGL coordinates to pixel coordinates
    x1 = (corners[0][0] + 1) * (displaysize[0] / 2)
    y1 = (corners[0][1] + 1) * (displaysize[1] / 2)
    x2 = (corners[1][0] + 1) * (displaysize[0] / 2)
    y2 = (corners[1][1] + 1) * (displaysize[1] / 2)

    # Ensure proper ordering for pygame.Rect
    return pygame.Rect(
        min(x1, x2),  # Top-left corner x
        min(y1, y2),  # Top-left corner y
        abs(x2 - x1),  # Width
        abs(y2 - y1),  # Height
    )


def derectify(
    rect: pygame.Rect, displaysize: Tuple[int, int]
) -> List[Tuple[float, float, float]]:
    """
    Convert Pygame Rect to array of normalized OpenGL coordinates.

    Args:
        rect (pygame.Rect): The Pygame Rect object.
        displaysize (Tuple[int, int]): The size of the display (width, height).

    Returns:
        List[Tuple[float, float, float]]: List of normalized coordinates in OpenGL space.
    """
    # Ensure the rect contains four elements (x, y, width, height)
    if len(rect) == 4:
        corners = [
            (rect[0], rect[1]),  # Top-left
            (rect[0] + rect[2], rect[1]),  # Top-right
            (rect[0], rect[1] + rect[3]),  # Bottom-left
            (rect[0] + rect[2], rect[1] + rect[3]),  # Bottom-right
        ]
        # Normalize coordinates to OpenGL space
        return [
            (
                (2 * corner[0] / displaysize[0] - 1),
                (2 * corner[1] / displaysize[1] - 1),
                0.0,
            )
            for corner in corners
        ]
    else:
        return [((2 * rect[c] / displaysize[c % 2] - 1)) for c in range(len(rect))]


def invmat(matrix: np.ndarray) -> np.ndarray:
    """
    Calculate the inverse of a matrix, if possible.

    Args:
        matrix (np.ndarray): The matrix to invert.

    Returns:
        np.ndarray: The inverted matrix.

    Raises:
        ValueError: If the matrix is not square or is singular (determinant = 0).
    """
    # Check if the matrix is square
    if matrix.shape[0] != matrix.shape[1]:
        raise ValueError("The matrix must be square.")
    # Check if the determinant is zero
    if np.linalg.det(matrix) == 0:
        raise ValueError("Determinant of the matrix is zero, cannot compute inverse.")
    # Return the inverse of the matrix
    return np.linalg.inv(matrix)


def mat4tomat3(matrix: np.ndarray) -> np.ndarray:
    """
    Convert a 4x4 matrix to a 3x3 matrix by dropping the last row and column.

    Args:
        matrix (np.ndarray): A 4x4 matrix.

    Returns:
        np.ndarray: A 3x3 matrix.
    """
    return matrix[:3, :3]


def thickLinePoints(arr: List[float], thick: float) -> List[float]:
    """
    Generate the points of a thick line from an array of points.

    Args:
        arr (List[float]): List of vertex positions in the form [x1, y1, x2, y2, ..., xn, yn].
        thick (float): The thickness of the line.

    Returns:
        List[float]: List of points for the thick line.
    """
    result = []
    for i in range(0, len(arr) - 2, 2):
        dx = arr[i + 2] - arr[i]
        dy = arr[i + 3] - arr[i + 1]
        dl = np.sqrt(dx**2 + dy**2)

        if dl > 0:
            mult = thick / dl
            ax = mult * dy
            ay = -mult * dx

        result.append(arr[i] + ax)
        result.append(arr[i + 1] + ay)
        result.append(arr[i] - ax)
        result.append(arr[i + 1] + ay)

    # Add the last two points
    result.append(arr[i] + ax)
    result.append(arr[i + 1] + ay)
    result.append(arr[i] - ax)
    result.append(arr[i + 1] + ay)

    return result
