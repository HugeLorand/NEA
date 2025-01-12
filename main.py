import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import item_draggable
import conversion

SQUARE_EDGES = [(0,1),(0,2),(1,3),(2,3)]

class App:
    def __init__(self,title):
        self._running = True
        self._display_surf = None
        self._size = self.weight, self.height = 1080, 1080
        self._caption = title
        self._dragitems = []
        self._selected = None
        self._offset = [0,0]
        self._clock = pygame.time.Clock()

    def on_init(self):
        pygame.init()
        self._display_surf = pygame.display.set_mode(self._size, pygame.DOUBLEBUF | pygame.OPENGL)
        self._caption = pygame.display.set_caption(self._caption)
        gluPerspective(45, (self.weight/self.height), 0.1, 50.0)
        glTranslatef(0.0,0.0, -5)
        self._running = True
  
    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                #goes through _dragitems and selects an item that collides with the mouse, if available
                for index, item in enumerate(self._dragitems):           
                    if item[0].collidepoint(event.pos):
                        self._selected = index
                        mouse_x, mouse_y = event.pos
                        self._offset[0] = item[0].x - mouse_x
                        self._offset[1] = item[0].y - mouse_y

        elif event.type == pygame.MOUSEBUTTONUP:
            #deselects item
            if event.button == 1:            
                self._selected = None

        elif event.type == pygame.MOUSEMOTION:
            if self._selected is not None: # selected can be `0` so `is not None` is required, which is more efficient than "!="
                # moves selected item
                self._dragitems[self._selected][0].x = event.pos[0] + self._offset[0]
                self._dragitems[self._selected][0].y = event.pos[1] + self._offset[1]
                


    def on_loop(self):
        self._clock.tick(144)
    def on_render(self):
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        self.draw_items()
        #insert here shader that renders waves to screen by taking previous frame and running calculations on each pixel to decode r g and b channels (displacement, velocity, refractive index at position)
        pygame.display.flip()
    def on_cleanup(self):
        pygame.quit()
 
    def on_execute(self):
        if self.on_init() == False:
            self._running = False
        #adds a source in the centre of the screen with placeholder values
        self.add_source([self.weight/2,self.height/2],"point",10,10,100,Color(255,0,0),False)
        self.add_source([(self.weight/2)+50,(self.height/2)+50],"point",10,10,100,Color(0,0,255),False)

        while( self._running ):
            for event in pygame.event.get():
                self.on_event(event)
            self.on_loop()
            self.on_render()
        self.on_cleanup()

    def add_drag(self,pos,size,color):
        #adds a draggable object at position [x,y], of size [width,height]
        item = item_draggable.Item(pos,size,color)
        self._dragitems.append(item.shape())
    
    def add_source(self,pos,type,frequency,wavelength,amplitude,color,decay,size=[100,100]):
        #adds a source as a draggable object of size 10x10
        self.add_drag(pos,size,color)
        pass

    def draw_items(self):
        for item in self._dragitems:
            draw = conversion.derectify(item[0],(self.weight,self.height))
            glBegin(GL_LINES)
            for edge in SQUARE_EDGES:
                for vertex in edge:
                    glVertex3fv(draw[vertex])
            glEnd()


 
if __name__ == "__main__" :
    WaveSim = App(title="WaveSim")
    WaveSim.on_execute()

