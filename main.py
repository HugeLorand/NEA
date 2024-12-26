import pygame
from pygame.locals import *
import item_draggable

class App:
    def __init__(self,title):
        self._running = True
        self._display_surf = None
        self._size = self.weight, self.height = 1920, 1080
        self._caption = title
        self._dragitems = []
        self.selected = None
        self.offset = [0,0]

    def on_init(self):
        pygame.init()
        self._display_surf = pygame.display.set_mode(self._size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        self._caption = pygame.display.set_caption(self._caption)
        self._running = True
  
    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                #goes through _dragitems and selects an item that collides with the mouse, if available
                for index, item in enumerate(self._dragitems):           
                    if item.collidepoint(event.pos):
                        self.selected = index
                        mouse_x, mouse_y = event.pos
                        self.offset[0] = item.x - mouse_x
                        self.offset[1] = item.y - mouse_y
                        print(self.offset[0],self.offset[1])

        elif event.type == pygame.MOUSEBUTTONUP:
            #deselects item
            if event.button == 1:            
                self.selected = None

        elif event.type == pygame.MOUSEMOTION:
            if self.selected is not None: # selected can be `0` so `is not None` is required, which is more efficient than "!="
                # moves selected item
                self._dragitems[self.selected].x = event.pos[0] + self.offset[0]
                self._dragitems[self.selected].y = event.pos[1] + self.offset[1]
                


    def on_loop(self):
        pass
    def on_render(self):
        for item in self._dragitems:
            self._display_surf.fill(Color(0,0,0))
            pygame.draw.rect(self._display_surf,Color(255,255,255),item)
            pygame.display.flip()
    def on_cleanup(self):
        pygame.quit()
 
    def on_execute(self):
        if self.on_init() == False:
            self._running = False
        #adds a source in the centre of the screen with placeholder values
        self.add_source([self.weight/2,self.height/2],"point",10,10,100,[255,255,255],False)

        while( self._running ):
            for event in pygame.event.get():
                self.on_event(event)
            self.on_loop()
            self.on_render()
        self.on_cleanup()

    def add_drag(self,pos,size):
        #adds a draggable object at position [x,y], of size [width,height]
        item = item_draggable.Item(pos,size)
        self._dragitems.append(item.shape())
    
    def add_source(self,pos,type,frequency,wavelength,amplitude,colour,decay,size=[10,10]):
        #adds a source as a draggable object of size 10x10
        self.add_drag(pos,size)
        pass


        
 
if __name__ == "__main__" :
    WaveSim = App(title="WaveSim")
    WaveSim.on_execute()

