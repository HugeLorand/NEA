import pygame
def rectify(corners):
    #converts a set of four vertices into a pygame Rect
    rect = pygame.Rect(corners[0][0],corners[0][1],corners[1][0]-corners[2][0],corners[1][1]-corners[2][1])
    return rect

def derectify(rect,displaysize):
    #converts a pygame Rect into a set of vertices
    corners = [((rect[0]/displaysize[0])-0.5,-(rect[1]/displaysize[1])+0.5,0),(((rect[0]+rect[2])/displaysize[0])-0.5,-(rect[1]/displaysize[1])+0.5,0),((rect[0]/displaysize[0])-0.5,-((rect[1]-rect[3])/displaysize[1])+0.5,0),(((rect[0]+rect[2])/displaysize[0])-0.5,-((rect[1]-rect[3])/displaysize[1])+0.5,0)]
    return corners
