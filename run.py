import pygame
from pygame.locals import *
from constants import *
from pacman import Pacman
from nodes import NodeGroup
from pellets import PelletGroup
from ghosts import GhostGroup
from fruit import Fruit
from pauser import Pause
from text import TextGroup
from sprites import LifeSprites
from sprites import MazeSprites
from mazedata import MazeData


# utlility functions begins

# retuns the Manhattan distance between two points [xy1] and [xy2]
def manhattanDistance(xy1, xy2):
    "Returns the Manhattan distance between points xy1 and xy2"
    return abs(xy1[0] - xy2[0]) + abs(xy1[1] - xy2[1])

# utlility functions end


'''
NOTE

New Attributes for GameController:
    self.pellets
    self.depth
    self.index
    self.COOL_DOWN


Multi Agent Functions:
    generateSuccessor(self, agent_index, action, game_state)
    evaluationFunction(self, game_state)
    minimax(self, curr_depth, agent_index, game_state)
    getAction(self, agent_index, dt)
'''


class GameController(object):
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(SCREENSIZE, 0, 32)
        self.background = None
        self.background_norm = None
        self.background_flash = None
        self.clock = pygame.time.Clock()
        self.fruit = None
        self.pause = Pause(True)
        self.level = 0
        self.lives = 5
        self.score = 0
        self.textgroup = TextGroup()
        self.lifesprites = LifeSprites(self.lives)
        self.flashBG = False
        self.flashTime = 0.2
        self.flashTimer = 0
        self.fruitCaptured = []
        self.fruitNode = None
        self.mazedata = MazeData()
        # added more attributes
        self.pellets = None
        self.depth = 2
        self.index = 0
        self.COOL_DOWN = 0
        self.COUNTER = 0

    def setBackground(self):
        self.background_norm = pygame.surface.Surface(SCREENSIZE).convert()
        self.background_norm.fill(BLACK)
        self.background_flash = pygame.surface.Surface(SCREENSIZE).convert()
        self.background_flash.fill(BLACK)
        self.background_norm = self.mazesprites.constructBackground(
            self.background_norm, self.level % 5)
        self.background_flash = self.mazesprites.constructBackground(
            self.background_flash, 5)
        self.flashBG = False
        self.background = self.background_norm

    def startGame(self):
        self.mazedata.loadMaze(self.level)
        self.mazesprites = MazeSprites(
            self.mazedata.obj.name+".txt", self.mazedata.obj.name+"_rotation.txt")
        self.setBackground()
        self.nodes = NodeGroup(self.mazedata.obj.name+".txt")
        self.mazedata.obj.setPortalPairs(self.nodes)
        self.mazedata.obj.connectHomeNodes(self.nodes)
        self.pacman = Pacman(self.nodes.getNodeFromTiles(
            *self.mazedata.obj.pacmanStart))
        self.pellets = PelletGroup(self.mazedata.obj.name+".txt")
        self.ghosts = GhostGroup(self.nodes.getStartTempNode(), self.pacman)
        self.ghosts.pinky.setStartNode(
            self.nodes.getNodeFromTiles(*self.mazedata.obj.addOffset(2, 3)))
        self.ghosts.inky.setStartNode(
            self.nodes.getNodeFromTiles(*self.mazedata.obj.addOffset(0, 3)))
        self.ghosts.clyde.setStartNode(
            self.nodes.getNodeFromTiles(*self.mazedata.obj.addOffset(4, 3)))
        self.ghosts.setSpawnNode(self.nodes.getNodeFromTiles(
            *self.mazedata.obj.addOffset(2, 3)))
        self.ghosts.blinky.setStartNode(
            self.nodes.getNodeFromTiles(*self.mazedata.obj.addOffset(2, 0)))

        self.nodes.denyHomeAccess(self.pacman)
        self.nodes.denyHomeAccessList(self.ghosts)
        self.ghosts.inky.startNode.denyAccess(RIGHT, self.ghosts.inky)
        self.ghosts.clyde.startNode.denyAccess(LEFT, self.ghosts.clyde)
        self.mazedata.obj.denyGhostsAccess(self.ghosts, self.nodes)

    def startGame_old(self):
        self.mazedata.loadMaze(self.level)
        self.mazesprites = MazeSprites("maze1.txt", "maze1_rotation.txt")
        self.setBackground()
        self.nodes = NodeGroup("maze1.txt")
        self.nodes.setPortalPair((0, 17), (27, 17))
        homekey = self.nodes.createHomeNodes(11.5, 14)
        self.nodes.connectHomeNodes(homekey, (12, 14), LEFT)
        self.nodes.connectHomeNodes(homekey, (15, 14), RIGHT)
        self.pellets = PelletGroup("maze1.txt")
        self.pacman = Pacman(self.nodes.getNodeFromTiles(15, 26))
        self.ghosts = GhostGroup(self.nodes.getStartTempNode(), self.pacman)
        self.ghosts.blinky.setStartNode(
            self.nodes.getNodeFromTiles(2+11.5, 0+14))
        self.ghosts.pinky.setStartNode(
            self.nodes.getNodeFromTiles(2+11.5, 3+14))
        self.ghosts.inky.setStartNode(
            self.nodes.getNodeFromTiles(0+11.5, 3+14))
        self.ghosts.clyde.setStartNode(
            self.nodes.getNodeFromTiles(4+11.5, 3+14))
        self.ghosts.setSpawnNode(self.nodes.getNodeFromTiles(2+11.5, 3+14))

        self.nodes.denyHomeAccess(self.pacman)
        self.nodes.denyHomeAccessList(self.ghosts)
        self.nodes.denyAccessList(2+11.5, 3+14, LEFT, self.ghosts)
        self.nodes.denyAccessList(2+11.5, 3+14, RIGHT, self.ghosts)
        self.ghosts.inky.startNode.denyAccess(RIGHT, self.ghosts.inky)
        self.ghosts.clyde.startNode.denyAccess(LEFT, self.ghosts.clyde)
        self.nodes.denyAccessList(12, 14, UP, self.ghosts)
        self.nodes.denyAccessList(15, 14, UP, self.ghosts)
        self.nodes.denyAccessList(12, 26, UP, self.ghosts)
        self.nodes.denyAccessList(15, 26, UP, self.ghosts)

    # multi-agent functions begins here

    # Updates the game state [game_state] after one move of an agent [agent_index]
    # Returns a new game state with an updated agent posisiton, legal moves for
    # that agent, and a new pellet list if neccessary
    def generateSuccessor(self, agent_index, action, game_state):
        # for reference: game_state = [pacPos, ghostsPos, legalMoves, dt, foodPos]
        if agent_index == 0:
            game_state[0] = self.pacman.successor_pos(
                game_state[0], action, game_state[3])
            # define this function in entity
            game_state[2][0] = self.pacman.validDirectionsFromPosition(
                game_state[0], self.nodes)
            # updating pellet list by removing pellet pacman just ate
            pellet = self.pacman.eatPelletsCheck(game_state[0], game_state[4])
            if pellet != None:
                game_state[4].remove(pellet)
        else:
            ghost_list = self.ghosts.ghosts
            ghost_num = agent_index - 4
            g = ghost_list[ghost_num]
            game_state[1][ghost_num] = g.successor_pos(
                game_state[1][ghost_num], action, game_state[3])
            game_state[2][ghost_num + 1] = g.validDirectionsFromPosition(
                game_state[1][ghost_num], self.nodes)
        return game_state

    # Evaluates a game state [game_state] at the leaf node of the minimax game
    # tree and returns a score for that game state
    def evaluationFunction(self, game_state):

        def ghost_eval(game_state, cur_score):
            ghostMHdist = []
            cur_pos = (game_state[0].x, game_state[0].y)
            for ghost in game_state[1]:
                ghost_pos = (ghost.x, ghost.y)
                ghostMHdist.append(manhattanDistance(cur_pos, ghost_pos))
            foodMHdist = []
            for food_obj in new_pellets:
                food = (food_obj.position.x, food_obj.position.y)
                foodMHdist.append(manhattanDistance(cur_pos, food))
            for dist in ghostMHdist:
                cur_score += dist
            if len(foodMHdist) > 0:
                cur_score -= min(foodMHdist)
            else:
                cur_score += 9999
            return cur_score

        def food_good(pos, pellets, score):
            pos = (pos.x, pos.y)
            foodMHdist = []
            for food_o in pellets:
                food = (food_o.position.x, food_o.position.y)
                foodMHdist.append(manhattanDistance(pos, food))
            for f in foodMHdist:
                if f != 0:
                    score += 50/f
                else:
                    score += 0
            score += len(pellets)
            return score

        lowValue = -10000000.0

        def ghost_dist(pos, ghosts, score):
            pos = (pos.x, pos.y)
            ghostMHdist = []
            for ghost_o in ghosts:
                ghost_p = (ghost_o.x, ghost_o.y)
                ghostMHdist.append(manhattanDistance(pos, ghost_p))
            for ghost_pos in ghostMHdist:
                score += ghost_pos
            return score/100

        def ghost_near(pos, ghosts, score):
            pos = (pos.x, pos.y)
            ghostMHdist = []
            for ghost_o in ghosts:
                ghost_p = (ghost_o.x, ghost_o.y)
                ghostMHdist.append(manhattanDistance(pos, ghost_p))
            for ghost in ghostMHdist:
                if ghost < 7:
                    score += (lowValue)
                else:
                    score += ghost
            return score/1000

        def num_close(pos, pellets, score):
            pos = (pos.x, pos.y)
            foodMHdist = []
            for pellet in pellets:
                pe = (pellet.position.x, pellet.position.y)
                foodMHdist.append(manhattanDistance(pos, pe))
            for peldist in foodMHdist:
                if peldist < 100:
                    score += 50/peldist
                if peldist < 50:
                    score += 50/peldist
                    if peldist < 10:
                        score += 50/peldist
                        if peldist < 5:
                            score += 50/peldist
            return score

        def closest_ghost(pos, pellets, ghosts, score):
            pos = (pos.x, pos.y)
            foodMHdist = []
            ghostMHdist = []
            for pellet in pellets:
                pe = (pellet.position.x, pellet.position.y)
                foodMHdist.append(manhattanDistance(pos, pe))
            for ghost_o in ghosts:
                ghost_p = (ghost_o.x, ghost_o.y)
                ghostMHdist.append(manhattanDistance(pos, ghost_p))
            return (min(ghostMHdist), min(foodMHdist))

        new_pos = game_state[0]
        new_pellets = game_state[4]
        new_ghosts = game_state[1]

        def normalize(x1, x2, x3, x4):
            mag = (((x1**2)+(x2**2)+(x3**2)+(x4**2))**(0.5))
            return [x1/mag, x2/mag, x3/mag, x4/mag]
        score = 0
        closest = closest_ghost(new_pos, new_pellets, new_ghosts, score)
        minGdist = closest[0]
        #score += ghost_eval(game_state,score)
        score += 10*food_good(new_pos, new_pellets, score)
        # score+= food
        score += ghost_dist(new_pos, new_ghosts, score)/50
        # score+= gh
        score += 5*num_close(new_pos, new_pellets, score)
        # score+=close
        score += ghost_near(new_pos, new_ghosts, score)
        # score+=near
        # x= normalize(food,gh,close,near)
        # return (closest[0]/closest[1])
        if minGdist < 10:
            return closest[0]
        else:
            return (score)

    # Iterates through all five game agent's to simulate all possible game
    # plays of those agents, pruning with alpha and beta if neccessary
    def minimax(self, curr_depth, agent_index, game_state, alpha, beta):
        if agent_index > 7:
            agent_index = 0
            curr_depth += 1

        if curr_depth == self.depth:
            return None, self.evaluationFunction(game_state)

        best_score, best_action = None, None
        if agent_index == 0:  # If it is max player's (pacman) turn
            # For each legal action of pacman
            for action in game_state[2][agent_index]:

                next_game_state = self.generateSuccessor(
                    agent_index, action, game_state)
                _, score = self.minimax(
                    curr_depth, agent_index + 4, next_game_state, alpha, beta)

                if best_score is None or score > best_score:
                    best_score = score
                    best_action = action

                alpha = max(alpha, score)

                if alpha > beta:
                    break
        else:
            for action in game_state[2][agent_index - 3]:

                next_game_state = self.generateSuccessor(
                    agent_index, action, game_state)
                _, score = self.minimax(
                    curr_depth, agent_index + 1, next_game_state, alpha, beta)

                if best_score is None or score < best_score:
                    best_score = score
                    best_action = action

                beta = min(beta, score)

                if beta < alpha:
                    break

        if best_score is None:
            return None, self.evaluationFunction(game_state)
        print(best_action, best_score)
        return best_action, best_score

    # Instantiates an inital game state from the current game's game state at
    # the time this function is called by update(self) and passes it as an
    # attribute to minimax along with values for alpha and beta
    def getAction(self, agent_index, dt):

        legalMoves = [None] * 5
        ghostsPos = [None] * 4

        pacPos = self.pacman.position
        legalMoves[0] = self.pacman.validDirections()

        ghost_list = self.ghosts.ghosts
        c = 0
        for g in ghost_list:
            ghostsPos[c] = g.position
            legalMoves[c + 1] = g.validDirections()
            c += 1

        foodPos = (self.pellets.pelletList).copy()

        game_state = [pacPos, ghostsPos, legalMoves, dt, foodPos]
        inf = float('inf')

        action, score = self.minimax(0, agent_index, game_state, -inf, inf)
        #print(score, action)
        return action

    # multi-agent functions ends here

    def update(self):
        dt = self.clock.tick(30) / 1000.0
        self.textgroup.update(dt)
        self.pellets.update(dt)
        if not self.pause.paused:
            self.ghosts.update(dt)
            if self.fruit is not None:
                self.fruit.update(dt)
            self.checkPelletEvents()
            self.checkGhostEvents()
            self.checkFruitEvents()

        if self.pacman.alive:
            if not self.pause.paused:
                # calls getAction for pacman when wanting to move that agent
                self.pacman.update(self.getAction(0, dt), dt)
        else:
            # calls getAction for pacman when wanting to move that agent
            self.pacman.update(self.getAction(0, dt), dt)

        if self.flashBG:
            self.flashTimer += dt
            if self.flashTimer >= self.flashTime:
                self.flashTimer = 0
                if self.background == self.background_norm:
                    self.background = self.background_flash
                else:
                    self.background = self.background_norm

        afterPauseMethod = self.pause.update(dt)
        if afterPauseMethod is not None:
            afterPauseMethod()
        self.checkEvents()
        self.render()

    def checkEvents(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                exit()
            elif event.type == KEYDOWN:
                if event.key == K_SPACE:
                    if self.pacman.alive:
                        self.pause.setPause(playerPaused=True)
                        if not self.pause.paused:
                            self.textgroup.hideText()
                            self.showEntities()
                        else:
                            self.textgroup.showText(PAUSETXT)
                            # self.hideEntities()

    def checkPelletEvents(self):
        pellet = self.pacman.eatPellets(self.pellets.pelletList)
        if pellet:
            self.pellets.numEaten += 1
            self.updateScore(pellet.points)
            if self.pellets.numEaten == 30:
                self.ghosts.inky.startNode.allowAccess(RIGHT, self.ghosts.inky)
            if self.pellets.numEaten == 70:
                self.ghosts.clyde.startNode.allowAccess(
                    LEFT, self.ghosts.clyde)
            self.pellets.pelletList.remove(pellet)
            if pellet.name == POWERPELLET:
                self.ghosts.startFreight()
            if self.pellets.isEmpty():
                self.flashBG = True
                self.hideEntities()
                self.pause.setPause(pauseTime=3, func=self.nextLevel)

    def checkGhostEvents(self):
        for ghost in self.ghosts:
            if self.pacman.collideGhost(ghost):
                if ghost.mode.current is FREIGHT:
                    self.pacman.visible = False
                    ghost.visible = False
                    self.updateScore(ghost.points)
                    self.textgroup.addText(
                        str(ghost.points), WHITE, ghost.position.x, ghost.position.y, 8, time=1)
                    self.ghosts.updatePoints()
                    self.pause.setPause(pauseTime=1, func=self.showEntities)
                    ghost.startSpawn()
                    self.nodes.allowHomeAccess(ghost)
                elif ghost.mode.current is not SPAWN:
                    if self.pacman.alive:
                        self.lives -= 1
                        self.lifesprites.removeImage()
                        self.pacman.die()
                        self.ghosts.hide()
                        if self.lives <= 0:
                            self.textgroup.showText(GAMEOVERTXT)
                            self.pause.setPause(
                                pauseTime=3, func=self.restartGame)
                        else:
                            self.pause.setPause(
                                pauseTime=3, func=self.resetLevel)

    def checkFruitEvents(self):
        if self.pellets.numEaten == 50 or self.pellets.numEaten == 140:
            if self.fruit is None:
                self.fruit = Fruit(
                    self.nodes.getNodeFromTiles(9, 20), self.level)
        if self.fruit is not None:
            if self.pacman.collideCheck(self.fruit):
                self.updateScore(self.fruit.points)
                self.textgroup.addText(str(
                    self.fruit.points), WHITE, self.fruit.position.x, self.fruit.position.y, 8, time=1)
                fruitCaptured = False
                for fruit in self.fruitCaptured:
                    if fruit.get_offset() == self.fruit.image.get_offset():
                        fruitCaptured = True
                        break
                if not fruitCaptured:
                    self.fruitCaptured.append(self.fruit.image)
                self.fruit = None
            elif self.fruit.destroy:
                self.fruit = None

    def showEntities(self):
        self.pacman.visible = True
        self.ghosts.show()

    def hideEntities(self):
        self.pacman.visible = False
        self.ghosts.hide()

    def nextLevel(self):
        self.showEntities()
        self.level += 1
        self.pause.paused = True
        self.startGame()
        self.textgroup.updateLevel(self.level)

    def restartGame(self):
        self.lives = 5
        self.level = 0
        self.pause.paused = True
        self.fruit = None
        self.startGame()
        self.score = 0
        self.textgroup.updateScore(self.score)
        self.textgroup.updateLevel(self.level)
        self.textgroup.showText(READYTXT)
        self.lifesprites.resetLives(self.lives)
        self.fruitCaptured = []

    def resetLevel(self):
        self.pause.paused = True
        self.pacman.reset()
        self.ghosts.reset()
        self.fruit = None
        self.textgroup.showText(READYTXT)

    def updateScore(self, points):
        self.score += points
        self.textgroup.updateScore(self.score)

    def render(self):
        self.screen.blit(self.background, (0, 0))
        # self.nodes.render(self.screen)
        self.pellets.render(self.screen)
        if self.fruit is not None:
            self.fruit.render(self.screen)
        self.pacman.render(self.screen)
        self.ghosts.render(self.screen)
        self.textgroup.render(self.screen)

        for i in range(len(self.lifesprites.images)):
            x = self.lifesprites.images[i].get_width() * i
            y = SCREENHEIGHT - self.lifesprites.images[i].get_height()
            self.screen.blit(self.lifesprites.images[i], (x, y))

        for i in range(len(self.fruitCaptured)):
            x = SCREENWIDTH - self.fruitCaptured[i].get_width() * (i+1)
            y = SCREENHEIGHT - self.fruitCaptured[i].get_height()
            self.screen.blit(self.fruitCaptured[i], (x, y))

        pygame.display.update()


if __name__ == "__main__":
    game = GameController()
    game.startGame()
    while True:
        game.update()
