from turtle import pos
from nodes import Node
from nodes import NodeGroup
import pygame
from pygame.locals import *
from vector import Vector2
from constants import *
from random import randint

'''
NOTE

custom helper functions:
    successor_pos(self, position, direction, dt)
    validDirectionsFromPosition(self, position)
    validDirectionFromPosition(self, position, direction, nodes)
    goalDirectionFromPosition(self, position, directions)

'''


class Entity(object):
    def __init__(self, node):
        self.name = None
        self.directions = {UP: Vector2(0, -1), DOWN: Vector2(0, 1),
                           LEFT: Vector2(-1, 0), RIGHT: Vector2(1, 0), STOP: Vector2()}
        self.direction = STOP
        # 100
        self.setSpeed(100)
        self.radius = 10
        self.collideRadius = 5
        self.color = WHITE
        self.visible = True
        self.disablePortal = False
        self.goal = None
        self.directionMethod = self.randomDirection
        self.setStartNode(node)
        self.image = None

    def setPosition(self):
        self.position = self.node.position.copy()

    def update(self, dt):
        self.position += self.directions[self.direction]*self.speed*dt

        if self.overshotTarget():
            self.node = self.target
            directions = self.validDirections()
            direction = self.directionMethod(directions)
            if not self.disablePortal:
                if self.node.neighbors[PORTAL] is not None:
                    self.node = self.node.neighbors[PORTAL]
            self.target = self.getNewTarget(direction)
            if self.target is not self.node:
                self.direction = direction
            else:
                self.target = self.getNewTarget(self.direction)

            self.setPosition()

    # getting next position of an agent currently in position [position] and moving
    # one step in the direction [direction]
    # NOTE should not need to do much ehre since direction should always be an int
    def successor_pos(self, position, direction, dt):
        return (position + self.directions[direction]*self.speed*dt)

    def validDirection(self, direction):
        if direction is not STOP:
            if self.name in self.node.access[direction]:
                if self.node.neighbors[direction] is not None:
                    return True
        return False

    # NOTE this was erroring out since direction was None. Maybe look into
    # this since this is potentially why the pacman just stops moving.
    # i prevented the error by adding the extra constraint to the info statement

    # direction is not None and
    def getNewTarget(self, direction):
        if self.validDirection(direction):
            return self.node.neighbors[direction]
        return self.node

    def overshotTarget(self):
        if self.target is not None:
            vec1 = self.target.position - self.node.position
            vec2 = self.position - self.node.position
            node2Target = vec1.magnitudeSquared()
            node2Self = vec2.magnitudeSquared()
            return node2Self >= node2Target
        return False

    def reverseDirection(self):
        self.direction *= -1
        temp = self.node
        self.node = self.target
        self.target = temp

    def oppositeDirection(self, direction):
        if direction is not STOP:
            if direction == self.direction * -1:
                return True
        return False

    def validDirections(self):
        directions = []
        for key in [UP, DOWN, LEFT, RIGHT]:
            if self.validDirection(key):
                if key != self.direction * -1:
                    directions.append(key)
        if len(directions) == 0:
            directions.append(self.direction * -1)
        return directions

    # NOTE this is the same but calls validDirectionFromPosition()
    def validDirectionsFromPosition(self, position, nodes):
        directions = []
        for key in [UP, DOWN, LEFT, RIGHT]:
            # need a valid direction function that takes in positional arguement
            # currently uses self.node???
            if self.validDirectionFromPosition(position, key, nodes):
                if key != self.direction * -1:
                    directions.append(key)
        if len(directions) == 0:
            directions.append(self.direction * -1)
        return directions

    # NOTE there are two ways to create a NODE: either use the node
    # constructor or create a node using the custom function getNodeFromPosition()
    # see nodes.py for how getNodeFromPosition() was implemented
    def validDirectionFromPosition(self, position, direction, nodes):
        #node = nodes.getNodeFromPosition(position.x, position.y)
        node = Node(position.x, position.y)
        if direction is not STOP:
            if self.name in node.access[direction]:
                if node.neighbors[direction] is not None:
                    return True
        return False

    def randomDirection(self, directions):
        return directions[randint(0, len(directions)-1)]

    def goalDirection(self, directions):
        distances = []
        for direction in directions:
            vec = self.node.position + \
                self.directions[direction]*TILEWIDTH - self.goal
            distances.append(vec.magnitudeSquared())
        index = distances.index(min(distances))
        return directions[index]

    # Getting direction ghost should head in to advance towards go from position <position>
    # NOTE changed this to output the index and not directions[index]. again, not sure if this is what we want.
    def goalDirectionFromPosition(self, position, directions):
        distances = []
        for direction in directions:
            vec = position + \
                self.directions[direction]*TILEWIDTH - self.goal
            distances.append(vec.magnitudeSquared())
        index = distances.index(min(distances))
        return index
        # return directions[index]

    def setStartNode(self, node):
        self.node = node
        self.startNode = node
        self.target = node
        self.setPosition()

    def setBetweenNodes(self, direction):
        if self.node.neighbors[direction] is not None:
            self.target = self.node.neighbors[direction]
            self.position = (self.node.position + self.target.position) / 2.0

    def reset(self):
        self.setStartNode(self.startNode)
        self.direction = STOP
        self.speed = 100
        self.visible = True

    def setSpeed(self, speed):
        self.speed = speed * TILEWIDTH / 16

    def render(self, screen):
        if self.visible:
            if self.image is not None:
                adjust = Vector2(TILEWIDTH, TILEHEIGHT) / 2
                p = self.position - adjust
                screen.blit(self.image, p.asTuple())
            else:
                p = self.position.asInt()
                pygame.draw.circle(screen, self.color, p, self.radius)
