# This is a very simple implementation of the UCT Monte Carlo Tree Search algorithm in Python 2.7.
# The function UCT(rootstate, itermax, verbose = False) is towards the bottom of the code.
# It aims to have the clearest and simplest possible code, and for the sake of clarity, the code
# is orders of magnitude less efficient than it could be made, particularly by using a
# state.GetRandomMove() or state.DoRandomRollout() function.
#
# Example GameState classes for Nim, OXO and Othello are included to give some idea of how you
# can write your own GameState use UCT in your 2-player game. Change the game to be played in
# the UCTPlayGame() function at the bottom of the code.
#
# Written by Peter Cowling, Ed Powley, Daniel Whitehouse (University of York, UK) September 2012.
#
# Licence is granted to freely use and distribute for any sensible/legal purpose so long as this comment
# remains in any distributed code.
#
# For more information about Monte Carlo Tree Search check out our web site at www.mcts.ai

from math import *
import sys
for path in sys.path:
	print (path)
import random
import types

import pygame
import os


# window dimensions
WIN_W = 800
WIN_H = 600

# buffer
BUFFER = WIN_H / 20

# header dimensions
HUD_H = 200

# border
BORDER_H = 20

# screen dimensions
SCREEN_W = WIN_W + 2 * BUFFER
SCREEN_H = WIN_H + HUD_H + 2 * BUFFER + BORDER_H + 50

# dot dimensions
DD = WIN_W / 9

# line dimensions
LD = WIN_H / 5

# other variables
FPS = 60
TIMER = 0

#Colors
BLACK = (0, 0, 0)  # dot color
CREAM = (243, 239, 225)  # font color
DB = (86, 70, 60)  # dark brown
WHITE = (255, 255, 255)
LC = (236, 204, 255)  # line color when mouse hovers over line
LC2 = (0, 186, 255)  # line color after mouse is clicked over line
PLACEHOLDER = (0, 100, 150)  # z color
TEAL = (142, 210, 201)  # player fill
ORANGE = (255, 122, 90)  # wozzy fill

class DotsAndBoxes:
    def __init__(self, width=4, height=4):
        """Take in input"""

        """if len(sys.argv[1:]) == 2:
            _test(int(sys.argv[1]), int(sys.argv[2]))
        elif len(sys.argv[1:]) == 1:
            _test(int(sys.argv[1]), int(sys.argv[1]))
        else:
            _test(4, 4)"""
        #the code is currently always running the else statement

        """Initializes a rectangular gameboard."""
        self.width, self.height = width, height
        assert 2 <= self.width and 2 <= self.height,\
            "Game can't be played on this board's dimension."
        self.board = {}
        self.squares = {}
        self.player = 0
        self.playerJustMoved = 1
        self.Stone = self.generateRosettaStone()
        self.moves = []
        self.GenerateMoves()
        """Initializes score array"""
        self.scores = [0,0]

    def Clone(self):
        st = DotsAndBoxes()
        st.playerJustMoved = self.playerJustMoved
        st.board = self.board.copy()
        st.squares = self.squares.copy()
        st.scores = self.scores[:]
        st.moves = self.moves[:]


        return st

    def isGameOver(self):
        """Returns true if no more moves can be made.

        The maximum number of moves is equal to the number of possible
        lines between adjacent dots.  I'm calculating this to be
        $2*w*h - h - w$; I think that's right.  *grin*
        """
        w, h = self.width, self.height
        return len(self.board.keys()) == 2 * w * h - h - w

    def _isSquareMove(self, move):
        """Returns a true value if a particular move will create a
        square.  In particular, returns a list of the the lower left
        corners of the squares captured by a move.

        (Note: I had forgotten about double crossed moves.  Gregor
        Lingl reported the bug; I'd better fix it now!  *grin*) """
        b = self.board
        mmove = self.makeMove  ## just to make typing easier
        ((x1, y1), (x2, y2)) = move
        captured_squares = []
        if self._isHorizontal(move):
            for j in [-1, 1]:
                if (b.has_key(mmove((x1, y1), (x1, y1 - j)))
                        and b.has_key(mmove((x1, y1 - j), (x1 + 1, y1 - j)))
                        and b.has_key(mmove((x1 + 1, y1 - j), (x2, y2)))):
                    captured_squares.append(min([(x1, y1), (x1, y1 - j),
                                                 (x1 + 1, y1 - j), (x2, y2)]))
        else:
            for j in [-1, 1]:

                if (b.has_key(mmove((x1, y1), (x1 - j, y1)))
                        and b.has_key(mmove((x1 - j, y1), (x1 - j, y1 + 1)))
                        and b.has_key(mmove((x1 - j, y1 + 1), (x2, y2)))):
                    captured_squares.append(min([(x1, y1), (x1 - j, y1),
                                                 (x1 - j, y1 + 1), (x2, y2)]))
        self.scores[self.player] += len(captured_squares)
        return captured_squares

    def _isHorizontal(self, move):
        "Return true if the move is in horizontal orientation."
        return abs(move[0][0] - move[1][0]) == 1

    def _isVertical(self, move):
        "Return true if the move is in vertical orientation."
        return not self.isHorizontal(self, move)

    def generateRosettaStone(self):

        #num = 0
        self.Stone = []
        for x1 in range(self.width):
            for y1 in range(self.height):
                for x2 in range(self.width):
                    for y2 in range(self.height):
                        if self.ultimateCheck(((x1, y1), (x2, y2))):
                            #num = num + 1
                            self.Stone.append(((x1, y1), (x2, y2)))

        #print(self.Stone)
        return self.Stone

    def rosettaStoneIndex(self, move):

        for pair in self.Stone:
            #print pair[0]
            #print pair[1]
            #print move
            #print pair
            #print pair[0],pair[1], move
            if pair == move:
                print "new move: ", self.Stone.index(pair)
                return self.Stone.index(pair)

    def rosettaStoneCoord(self, move):
        num = 0

        for pair in self.Stone:
            #print pair[0]
            #print pair[1]
            #print move
            #print pair
            #print pair[0],pair[1], move
            if self.Stone.index(pair) == move:
                return pair

    def DoMove(self, moveI):

        """Place a particular move on the board.  If any wackiness
        occurs, raise an AssertionError.  Returns a list of
        bottom-left corners of squares captured after a move."""
        move = self.rosettaStoneCoord(moveI)
        #print("moving")
        #print(moveI)
        #print(move)

        assert (self._isGoodCoord(move[0]) and
                self._isGoodCoord(move[1])), \
            "Bad coordinates, out of bounds of the board."
        move = self.makeMove(move[0], move[1])

        #print(move)

        self.board[move] = self.playerJustMoved
        ## Check if a square is completed.
        square_corners = self._isSquareMove(move)
        if square_corners:
            for corner in square_corners:
                self.squares[corner] = self.playerJustMoved
        else:
            self._switchPlayer()
        #print(self.moves)
        #print(moveI)
        self.moves.remove(moveI)
        return square_corners

    def _switchPlayer(self):
        self.player = (self.player + 1) % 2
        self.playerJustMoved = 3 - self.playerJustMoved
        #print self.playerJustMoved

    def getPlayer(self):
        return self.player

    def getSquares(self):
        """Returns a dictionary of squares captured.  Returns
        a dict of lower left corner keys marked with the
        player who captured them."""
        return self.squares

    def __str__(self):
        """Return a nice string representation of the board."""
        buffer = []
        print self.squares
        buffer.append("Player 1 Score: " + str(self.scores[0]) + "\t Player 2 Score: " + str(self.scores[1]) + "\n")

        ## do the top line
        for i in range(self.width - 1):
            if self.board.has_key(((i, self.height - 1), (i + 1, self.height - 1))):
                buffer.append("+--")
            else:
                buffer.append("+  ")
        buffer.append("+\n")

        ## and now do alternating vertical/horizontal passes
        for j in range(self.height - 2, -1, -1):
            ## vertical:
            for i in range(self.width):
                if self.board.has_key(((i, j), (i, j + 1))):
                    buffer.append("|")
                else:
                    buffer.append(" ")
                if self.squares.has_key((i, j)):
                    buffer.append("%s " % self.squares[i, j])
                else:
                    buffer.append("  ")
            buffer.append("\n")

            ## horizontal
            for i in range(self.width - 1):
                if self.board.has_key(((i, j), (i + 1, j))):
                    buffer.append("+--")
                else:
                    buffer.append("+  ")
            buffer.append("+\n")

        return ''.join(buffer)

    def ultimateCheck(self, move):
        # user input format (paranthesis and number)
        # xdelta, ydelta (length)
        # check if line is taken
        self.xdelta, self.ydelta = move[1][0] - move[0][0], move[1][1] - move[0][1]

        # print(move)
        while (self._isGoodCoord(move[0]) == False or self._isGoodCoord(move[1]) == False):
            # print("Fail:1")
            return False

        while (move[0][0] == move[0][1] == move[1][0] == move[1][1]):
            # print("Fail:2")
            return False

        # while ((abs(self.xdelta) > 1 and abs(self.ydelta) == 0) or (abs(self.xdelta) == 0 and abs(self.ydelta) > 1)) or (abs(self.xdelta) > 1 and abs(self.ydelta) > 1):
        #    return False


        while move[0][0] > self.width and move[1][0] > self.width and move[0][1] > self.height and move[1][
            1] > self.height:
            # print("Fail:3")
            return False

        mmove = self.organizeMove(move[0], move[1])

        if (mmove in self.Stone):
            # print("Fail:4")
            return False

        if (((abs(self.xdelta) == 0) and (abs(self.ydelta) == 1)) or (
                (abs(self.xdelta) == 1) and (abs(self.ydelta) == 0))):
            # print("Good Move")
            return True

    def ultimateCheck2ThisTimeItsPersonal(self, move):
        # user input format (paranthesis and number)
        # xdelta, ydelta (length)
        # check if line is taken
        self.xdelta, self.ydelta = move[1][0] - move[0][0], move[1][1] - move[0][1]

        #print(move)
        while (self._isGoodCoord(move[0]) == False or self._isGoodCoord(move[1]) == False):
            #print("Fail:1")
            return False

        while (move[0][0] == move [0][1] == move [1][0] == move [1][1]):
            #print("Fail:2")
            return False

        #while ((abs(self.xdelta) > 1 and abs(self.ydelta) == 0) or (abs(self.xdelta) == 0 and abs(self.ydelta) > 1)) or (abs(self.xdelta) > 1 and abs(self.ydelta) > 1):
        #    return False

        while move[0][0] > self.width and move[1][0] > self.width  and move[0][1] > self.height and move[1][1] > self.height:
            #print("Fail:3")
            return False

        mmove = self.organizeMove(move[0],move[1])

        while ( self.board.has_key(mmove)):
            #print("Fail:4")
            return False

        if (((abs(self.xdelta) == 0) and (abs(self.ydelta) == 1)) or ((abs(self.xdelta) == 1) and (abs(self.ydelta) == 0))):
            return True
        #print("Fail:5")
        return False
    def makeMove(self, coord1, coord2):
        """Return a new "move", and ensure it's in canonical form.
        (That is, force it so that it's an ordered tuple of tuples.)
        """
        self.xdelta, self.ydelta = coord2[0] - coord1[0], coord2[1] - coord1[1]

        while((abs(self.xdelta) > 1 and abs(self.ydelta) == 0) or (abs(self.xdelta) == 0 and abs(self.ydelta) > 1)):

            print ("Bad coordinates, not adjacent points.")
            move = input("Try again. Move?")

            assert (self._isGoodCoord(move[0]) and
                    self._isGoodCoord(move[1])), \
                "Bad coordinates, out of bounds of the board."
            move = self._makeMove(move[0]
                                  , move[1])
            assert (not self.board.has_key(move)), \
                "Bad move, line already occupied."
            self.board[move] = self.player
            ## Check if a square is completed.
            square_corners = self._isSquareMove(move)
            if square_corners:
                for corner in square_corners:
                    self.squares[corner] = self.player
            else:
                self._switchPlayer()
            return square_corners

        if coord1 < coord2:
            return (coord1, coord2)
        else:
            return (tuple(coord2), tuple(coord1))

    def organizeMove(self, coord1, coord2):
        """Return a new "move", and ensure it's in canonical form.
        (That is, force it so that it's an ordered tuple of tuples.)
        """

        if coord1 < coord2:
            return (coord1, coord2)
        else:
            return (tuple(coord2), tuple(coord1))

    def _isGoodCoord(self, coord):
        """Returns true if the given coordinate is good.

        A coordinate is "good" if it's within the boundaries of the
        game board, and if the coordinates are integers."""

        return (0 <= coord[0] < self.width
                and 0 <= coord[1] < self.height
                and isinstance(coord[0], types.IntType)
                and isinstance(coord[1], types.IntType))
    def GenerateMoves(self):

        for i in range(0,len(self.Stone)):
            self.moves.append(i)
        return self.moves

    def GetMoves(self):
        #print("Getting Moves")

        """for h1 in range(self.height):
            for w1 in range(self.width):
                for h2 in range(self.height):
                    for w2 in range(self.width):
                        #print(((w1, h2), (w2, h2)))
                        if (self.ultimateCheck2ThisTimeItsPersonal(((w1, h2), (w2, h2))) == True):
                            moves.append(self.rosettaStoneIndex(((w1, h1), (w2, h2))))"""
        #print("Finished getting Moves")

        return self.moves

    #give it playerjustmoved. If playerjustmoved wins then return 1.0
    def GetResult(self,playerjm):
        if self.GetMoves() == []:
            #print("Out of moves")
            #print playerjm
            #print self.player
            #print "Score: " ,self.scores, "playerjm: ", playerjm
            if self.scores[playerjm-1] > self.scores[3-playerjm-1]:
                return 1.0
            else:
                return 0.0
        else:
            print("This is bad")
            return 0.0


class Object(pygame.sprite.Sprite):
    def __init__(self, width, height, x, y, type, image=None):
        pygame.sprite.Sprite.__init__(self)
        self.w = width
        self.h = height
        self.clicked = False
        self.type = type

        self.image = pygame.Surface((self.w, self.h), pygame.SRCALPHA).convert()
        self.set_image(image)
        self.image.set_alpha(0)

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.hitbox = self.rect
        self.hitbox = self.set_hitbox(type)

    def set_image(self, image):
        if image != None:
            self.image = pygame.image.load(image).convert_alpha()
            self.image = pygame.transform.scale(self.image, (self.w, self.h))

    def set_hitbox(self, type):
        if type == "hl":
            # find tuple for endpoints
            return pygame.Rect(self.rect.x + DD / 2, self.rect.y, LD, DD)
        elif type == "vl":
            # find tuple for endpoints
            return pygame.Rect(self.rect.x, self.rect.y + DD / 2, DD, LD)
        else:
            return pygame.Rect(self.rect.x, self.rect.y, self.w, self.h)

    def update(self, mousedown, run, dts, player_score, wozzy_score, z_group):
        if self.clicked is False:
            if self.hitbox.collidepoint(pygame.mouse.get_pos()):
                self.image.fill(LC)
                self.image.set_alpha(150)

                # change object color when mouse is clicked over it
                if mousedown:
                    self.image.fill(DB)
                    self.image.set_alpha(255)
                    self.clicked = True
                    self.tuple = run.get_tuple(self)
                    box_made = dts.DoMove(dts.rosettaStoneIndex(self.tuple))

                    # update scores
                    if len(box_made) > 0:
                        for box in box_made:
                            if run.turn%2 == 0:
                                run.wozzy_score = dts.scores[1]
                                wozzy_score.image = wozzy_score.font.render(str(run.wozzy_score), 1, WHITE)
                                for z in z_group:
                                    print "box left: " + str(z.rect.left) + " | box bottom: " + str(z.rect.bottom)
                                    print "box made: " + str(box[0]) + " | box made bottom : " + str(box[1])
                                    if z.rect.left == box[0] and z.rect.bottom == box[1]:
                                        print "zcapasda" + str(z.rect.x) + str(z.rect.y)
                                        z.image.fill(ORANGE)
                                        z.image.set_alpha(255)

                            else:
                                run.player_score = dts.scores[0]
                                player_score.image = player_score.font.render(str(run.player_score), 1, WHITE)
                                for z in z_group:
                                    if z.rect.x == box[0] and z.rect.y == box[1]:
                                        print "adpoasjpajp"  + str(z.rect.x) + str(z.rect.y)
                                        z.image.fill(TEAL)
                                        z.image.set_alpha(255)
                            print dts.scores[0], dts.scores[1]

                # make object transparent again if mouse isn't hovering over it / object wasn't clicked
            if self.hitbox.collidepoint(pygame.mouse.get_pos()) == 0:
                self.image.set_alpha(0)


class Game:
    def __init__(self, screen, play, clock):
        self.screen = screen
        self.play = play
        self.clock = clock
        self.turn = 0
        self.title = Text(100, "Dots & Boxes", CREAM, SCREEN_W / 2, SCREEN_H / 10, "center", 'title')
        self.r = self.c = -1
        self.r2 = self.c2 = -1
        self.player_score = self.wozzy_score = 0

    def get_tuple(self, line):
        x = pygame.mouse.get_pos()[0]
        y = pygame.mouse.get_pos()[1]

        # vl col bounds
        a1_l = BUFFER
        a1_u = a1_l + DD
        a2_l = a1_u + LD
        a2_u = a2_l + DD
        a3_l = a2_u + LD
        a3_u = a3_l + DD
        a4_l = a3_u + LD
        a4_u = a4_l + DD

        # hl row bounds
        b1_l = HUD_H + BORDER_H + BUFFER
        b1_u = b1_l + DD
        b2_l = b1_u + LD
        b2_u = b2_l + DD
        b3_l = b2_u + LD
        b3_u = b3_l + DD
        b4_l = b3_u + LD
        b4_u = b4_l + DD

        # vl row bounds
        c1_l = HUD_H + BORDER_H + BUFFER + DD
        c1_u = c1_l + LD
        c2_l = c1_u + DD
        c2_u = c2_l + LD
        c3_l = c2_u + DD
        c3_u = c3_l + LD

        # hl col bounds
        d1_l = BUFFER + DD
        d1_u = d1_l + LD
        d2_l = d1_u + DD
        d2_u = d2_l + LD
        d3_l = d2_u + DD
        d3_u = d3_l + LD

        # vl_col
        if line.type == "vl":
            if x > a1_l and x < a1_u:
                self.c = 0
            elif x > a2_l and x < a2_u:
                self.c = 1
            elif x > a3_l and x < a3_u:
                self.c = 2
            elif x > a4_l and x < a4_u:
                self.c = 3
                # vl_row
            if y > c1_l and y < c1_u:
                self.r = 2
            elif y > c2_l and y < c2_u:
                self.r = 1
            elif y > c3_l and y < c3_u:
                self.r = 0

            self.r2 = self.r + 1
            self.c2 = self.c

        # hl_row
        if line.type == "hl":
            if x > d1_l and x < d1_u:
                self.c = 0
            elif x > d2_l and x < d2_u:
                self.c = 1
            elif x > d3_l and x < d3_u:
                self.c = 2

            if y > b1_l and y < b1_u:
                self.r = 3
            elif y > b2_l and y < b2_u:
                self.r = 2
            elif y > b3_l and y < b3_u:
                self.r = 1
            elif y > b4_l and y < b4_u:
                self.r = 0

            self.r2 = self.r
            self.c2 = self.c + 1

        return ((self.c, self.r), (self.c2, self.r2))


class Text(pygame.sprite.Sprite):
    def __init__(self, size, text, color, xpos, ypos, side, type, player=None):
        pygame.sprite.Sprite.__init__(self)
        self.font = pygame.font.SysFont("Britannic Bold", size)
        self.side = side
        self.x = xpos
        self.y = ypos
        self.image = self.font.render(text, 1, color)
        self.rect = self.image.get_rect()
        self.rect.move((0, self.y))
        self.type = type

        if player is not None:
            self.player = player
        if player is None:
            self.rect = self.rect.move(self.x - self.rect.width / 2, self.y - self.rect.height)

    def update(self, p_name, w_name, p_score, w_score):
        if self.type == "name":
            text_buffer = (SCREEN_W - p_name.rect.width - w_name.rect.width)/3
            if self.side == "left":
                self.rect = pygame.Rect(text_buffer, self.y, self.rect.width, self.rect.height)
            elif self.side == "right":
                self.rect = pygame.Rect(SCREEN_W - text_buffer - self.rect.width, self.y, self.rect.width, self.rect.height)
        elif self.type == "score":
            if self.side == "left":
                self.rect.centerx = p_name.rect.centerx
            elif self.side == "right":
                self.rect.centerx = w_name.rect.centerx
            self.rect.y = self.y
        else:
            self.rect = pygame.Rect(SCREEN_W/2, self.rect.y, self.rect.width, self.rect.height)


def main():
    global TIMER, WHITE
    TIMER += 1

    pygame.display.set_caption('Game Name')

    run = Game(pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.SRCALPHA), True, pygame.time.Clock())

    # create game objects
    header = pygame.image.load("images/header.jpg")
    header = pygame.transform.scale(header, (SCREEN_W, HUD_H))
    header_rect = header.get_rect()

    border = pygame.image.load("images/border.png")
    border = pygame.transform.scale(border, (SCREEN_W, BORDER_H))
    border_rect = border.get_rect()
    border_rect = border_rect.move((0, HUD_H))

    game_bg = pygame.image.load("images/game_bg.jpg")
    game_bg = pygame.transform.scale(game_bg, (SCREEN_W, WIN_H + BUFFER * 2))
    game_bg_rect = game_bg.get_rect()
    game_bg_rect = game_bg_rect.move((0, HUD_H + BORDER_H))

    player_name = Text(60, "Human:" , WHITE, 0, SCREEN_H / 10, 'left', 'name', 'player')
    player_score = Text(80, str(run.player_score), WHITE, 0, SCREEN_H * 5 / 32, 'left', 'score', 'player')
    wozzy_name = Text(60, "Wozzy:", WHITE, 0, SCREEN_H / 10, 'right', 'name', 'wozzy')
    wozzy_score = Text(80, str(run.wozzy_score), WHITE, 0, SCREEN_H * 5 / 32, 'right', 'score', 'wozzy')

    dts = DotsAndBoxes()

    # create groups
    dot_group = pygame.sprite.Group()
    line_group = pygame.sprite.Group()
    b_group = pygame.sprite.Group()
    z_group = pygame.sprite.Group()
    name_group = pygame.sprite.Group()
    name_group.add(player_name, wozzy_name)
    score_group = pygame.sprite.Group()
    score_group.add(player_score, wozzy_score)

    # load level
    level = [
        "DLDLDLD",
        "BZBZBZB",
        "DLDLDLD",
        "BZBZBZB",
        "DLDLDLD",
        "BZBZBZB",
        "DLDLDLD", ]

    # build level
    x = BUFFER
    y = HUD_H + BUFFER + BORDER_H
    for row in level:
        for col in row:
            if col == "D":
                d = Object(DD, DD, x, y, "dot", "images/dot.png")
                dot_group.add(d)

            if col == "L":
                l = Object(LD + DD, DD, x - DD / 2, y, "hl")
                line_group.add(l)

            if col == 'B':
                b = Object(DD, LD + DD, x, y - DD / 2, "vl")
                b_group.add(b)

            if col == "Z":
                z = Object(LD, LD, x, y, "placeholder")
                z_group.add(z)

            if col == "D" or col == "B":
                x += DD
            if col == "L" or col == "Z":
                x += LD

        if col == "D" or col == "L":
            y += DD
        if col == "B" or col == "Z":
            y += LD
        x = BUFFER

    while run.play:
        mousedown = False
        for event in pygame.event.get():
            # checks if window exit button is pressed
            if event.type == pygame.QUIT:
                sys.exit()
            # checks if mouse is clicked
            if event.type == pygame.MOUSEBUTTONDOWN:
                mousedown = True

        # update line
        line_group.update(mousedown, run, dts, player_score, wozzy_score, z_group)
        b_group.update(mousedown, run, dts, player_score, wozzy_score, z_group)

        # update text positions
        name_group.update(player_name, wozzy_name, player_score, wozzy_score)
        score_group.update(player_name, wozzy_name, player_score, wozzy_score)

        '''
        if computer go

            convert m to r,col
            use that to set in game
        elif mousedown
            human goes'''


        # draw groups
        run.screen.blit(header, header_rect)
        run.screen.blit(run.title.image, run.title.rect)
        run.screen.blit(border, border_rect)
        run.screen.blit(game_bg, game_bg_rect)
        name_group.draw(run.screen)
        score_group.draw(run.screen)
        dot_group.draw(run.screen)
        line_group.draw(run.screen)
        b_group.draw(run.screen)
        z_group.draw(run.screen)

        run.clock.tick(FPS)
        pygame.display.flip()


if __name__ == "__main__":
    # Forces static position of screen
    os.environ['SDL_VIDEO_CENTERED'] = '1'

    # Runs imported module
    pygame.init()

    main()