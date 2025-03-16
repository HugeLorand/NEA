import pygame
from pygame.locals import *
import item_draggable
from source import Source
from medium import Medium


class App:
    def __init__(self, title):
        self._running = True
        self.inputsSurface = None
        self.dataSurface = None
        self._display_surf = None
        self.masterSurface = None
        self._size = self.weight, self.height = 1080, 1080
        self._caption = title
        self.dragItems = []
        self.numDragItems = 0
        self.sources = []
        self.walls = []
        self._selected = None
        self.active = 0
        self._offset = [0, 0]
        self._clock = pygame.time.Clock()
        self.sliders = []
        self.actionstack = []
        self.actionstackpointer = 0
        self.text = None

    def on_init(self):
        pygame.init()
        self.masterSurface = pygame.display.set_mode(
            (self.weight + 300, self.height + 200)
        )
        self._display_surf = pygame.Surface(self._size)
        self.dataSurface = pygame.Surface((self.weight + 300, 200))
        self.inputsSurface = pygame.Surface((300, self.height))
        self.masterSurface.blits(
            [
                (self._display_surf, (0, 0)),
                (self.dataSurface, (0, self.height)),
                (self.inputsSurface, (self.weight, 0)),
            ]
        )
        self._running = True
        pygame.font.init()
        self.text = pygame.font.SysFont("calibri", 15)

    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False

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
                            self._selected = index
                            self.active = index
                            self.add_action(
                                ["m", (item.x, item.y), (0, 0), self._selected]
                            )

                            mouse_x, mouse_y = event.pos
                            self._offset[0] = item.x - mouse_x
                            self._offset[1] = item.y - mouse_y
                except:
                    pass

        elif event.type == pygame.MOUSEBUTTONUP:
            # deselects item
            if event.button == 1:
                self._selected = None
                try:
                    self.actionstack[self.actionstackpointer - 1][2] = tuple(
                        [x + y for x, y in zip(event.pos, self._offset)]
                    )
                except:
                    pass

        elif event.type == pygame.MOUSEMOTION:
            if (
                self._selected is not None
            ):  # selected can be `0` so `is not None` is required, which is more efficient than "!="
                # moves selected item
                position = (
                    min(max(0, event.pos[0] + self._offset[0]), self.weight - 8),
                    min(max(0, event.pos[1] + self._offset[1]), self.height - 8),
                )
                self.move_item(self._selected, position)
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
        self._clock.tick(144)

    def on_render(self):
        self._display_surf.fill(Color(0, 0, 0))
        for item in self.sources:
            pygame.draw.rect(
                self._display_surf, Color(255, 0, 0), Rect(item.get_pos(), (8, 8))
            )
        for item in self.walls:
            coords = item.get_rotated()
            pygame.draw.lines(
                self._display_surf, Color(0, 0, 255), True, coords, width=5
            )
        self.masterSurface.blit(self._display_surf, (0, 0))
        self.inputsSurface.fill(Color(220, 220, 220))
        self.draw_sliders()
        self.masterSurface.blit(self.inputsSurface, (self.weight, 0))
        pygame.display.flip()

    def on_cleanup(self):
        pygame.quit()

    def on_execute(self):
        if self.on_init() == False:
            self._running = False
        # adds a source in the centre of the screen with placeholder values
        self.add_source([self.weight / 2, self.height / 2], 10, 1)
        self.add_source([(self.weight / 2) + 50, (self.height / 2) + 50], 10, 1)
        self.add_wall([250, 550], [300, 10], 180)

        while self._running:
            for event in pygame.event.get():
                self.on_event(event)
            self.on_loop()
            self.on_render()
        self.on_cleanup()

    def add_drag(self, pos, size, color):
        # adds a draggable object at position [x,y], of size [width,height]
        item = item_draggable.Item(pos, size, color)
        self.dragItems.append(item.shape())

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

    def add_drag(self, pos, size):
        # adds a draggable object at position [x,y], of size [width,height]
        id = self.numDragItems
        item = item_draggable.Item(pos, size, id)
        self.dragItems.append(item.hitbox())
        self.numDragItems += 1

    def add_source(self, pos, frequency, amplitude):
        # adds a wave source
        id = self.numDragItems
        source = Source(pos, id, frequency, amplitude)
        self.sources.append(source)
        self.add_drag(pos, [8, 8])

    def add_wall(self, pos, size, rot):
        # adds a wall
        id = self.numDragItems
        wall = Medium(pos, size, id, rot, 0)
        self.walls.append(wall)
        self.add_drag(pos, size)

    def add_medium(self, pos, size, n):
        id = self.numDragItems
        med = Medium(pos, size, id, n)
        self.walls.append(med)
        self.add_drag(pos, size)

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
