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
import random
import types
import sys

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
        #self.moves.remove(moveI)
        self.removeMove(moveI)
        return square_corners

    def removeMove(self, reMove):

        self.moves.remove(reMove)

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

        return self.moves[:]

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


class OXOState:
    """ A state of the game, i.e. the game board.
        Squares in the board are in this arrangement
        012
        345
        678
        where 0 = empty, 1 = player 1 (X), 2 = player 2 (O)
    """

    def __init__(self):
        self.playerJustMoved = 2  # At the root pretend the player just moved is p2 - p1 has the first move
        self.board = [0, 0, 0, 0, 0, 0, 0, 0, 0]  # 0 = empty, 1 = player 1, 2 = player 2

    def Clone(self):
        """ Create a deep clone of this game state.
        """
        st = OXOState()
        st.playerJustMoved = self.playerJustMoved
        st.board = self.board[:]
        return st

    def DoMove(self, move):
        """ Update a state by carrying out the given move.
            Must update playerToMove.
        """
        assert move >= 0 and move <= 8 and move == int(move) and self.board[move] == 0
        self.playerJustMoved = 3 - self.playerJustMoved
        self.board[move] = self.playerJustMoved

    def GetMoves(self):
        """ Get all possible moves from this state.
        """
        return [i for i in range(9) if self.board[i] == 0]

    def GetResult(self, playerjm):
        """ Get the game result from the viewpoint of playerjm.
        """
        for (x, y, z) in [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]:
            if self.board[x] == self.board[y] == self.board[z]:
                if self.board[x] == playerjm:
                    return 1.0
                else:
                    return 0.0
        if self.GetMoves() == []: return 0.5  # draw
        assert False  # Should not be possible to get here

    def __repr__(self):
        s = ""
        for i in range(9):
            s += ".XO"[self.board[i]]
            if i % 3 == 2: s += "\n"
        return s
class Node:
    """ A node in the game tree. Note wins is always from the viewpoint of playerJustMoved.
        Crashes if state not specified.
    """
    def __init__(self, move = None, parent = None, state = None):
        self.move = move # the move that got us to this node - "None" for the root node
        self.parentNode = parent # "None" for the root node
        self.childNodes = []
        self.wins = 0
        self.visits = 0
        self.untriedMoves = state.GetMoves() # future child nodes
        self.playerJustMoved = state.playerJustMoved # the only part of the state that the Node needs later
        
    def UCTSelectChild(self):
        """ Use the UCB1 formula to select a child node. Often a constant UCTK is applied so we have
            lambda c: c.wins/c.visits + UCTK * sqrt(2*log(self.visits)/c.visits to vary the amount of
            exploration versus exploitation.
        """
        s = sorted(self.childNodes, key = lambda c: c.wins/c.visits + 3.5*sqrt(2*log(self.visits)/c.visits))[-1]
        return s
    
    def AddChild(self, m, s):
        """ Remove m from untriedMoves and add a new child node for this move.
            Return the added child node
        """
        n = Node(move = m, parent = self, state = s)
        #print(self.untriedMoves)
        #print(m)
        self.childNodes.append(n)

        return n
    
    def Update(self, result):
        """ Update this node - one additional visit and result additional wins. result must be from the viewpoint of playerJustmoved.
        """
        self.visits += 1
        self.wins += result

    def __repr__(self):
        return "[M:" + str(self.move) + " W/V:" + str(self.wins) + "/" + str(self.visits) + " U:" + str(self.untriedMoves) + "]"

    def TreeToString(self, indent):
        s = self.IndentString(indent) + str(self)
        for c in self.childNodes:
             s += c.TreeToString(indent+1)
        return s

    def IndentString(self,indent):
        s = "\n"
        for i in range (1,indent+1):
            s += "| "
        return s

    def ChildrenToString(self):
        s = ""
        for c in self.childNodes:
             s += str(c) + "\n"
        return s


def UCT(rootstate, itermax, verbose = False):
    """ Conduct a UCT search for itermax iterations starting from rootstate.
        Return the best move from the rootstate.
        Assumes 2 alternating players (player 1 starts), with game results in the range [0.0, 1.0]."""

    rootnode = Node(state = rootstate)

    for i in range(itermax):
        node = rootnode
        state = rootstate.Clone()
        #print"Select"
        #Select
        #print state.GetMoves()
        #print node.untriedMoves
        while node.untriedMoves == [] and node.childNodes != []: # node is fully expanded and non-terminal
            #print "Selecting"
            node = node.UCTSelectChild()
            state.DoMove(node.move)
            #state.removeMove(node.move)

        # Expand
        #print"Expand"
        #print state.GetMoves()

        if node.untriedMoves != []: # if we can expand (i.e. state/node is non-terminal)
            #print "Expanding"
            m = random.choice(node.untriedMoves)
            state.DoMove(m)
            node.untriedMoves.remove(m)
            node = node.AddChild(m,state) # add child and descend tree


        # Rollout - this can often be made orders of magnitude quicker using a state.GetRandomMove() function
        #print"autobots"
        #print state.GetMoves()
        while state.GetMoves() != []: # while state is non-terminal
            #print "Rolling Out"
            #print state.GetMoves()
            r = random.choice(state.GetMoves())
            state.DoMove(r)
        #print "Backpropagate"
        #print state.GetMoves()

        while node != None: # backpropagate from the expanded node and work back to the root node
            #print "Backpropagating"
            node.Update(state.GetResult(node.playerJustMoved)) # state is terminal. Update node with result from POV of node.playerJustMoved
            node = node.parentNode

    # Output some information about the tree - can be omitted
    if (verbose): print (rootnode.TreeToString(0))
    else:
        print(rootnode.ChildrenToString())


    return sorted(rootnode.childNodes, key = lambda c: c.visits)[-1].move # return the move that was most visited
                
def UCTPlayGame(firstplayer,itterations):
    """ Play a sample game between two UCT players where each player gets a different number 
        of UCT iterations (= simulations = tree nodes).
    """
    state = DotsAndBoxes() # uncomment to play Dots and Boxes
    #state = OXOState()
    while (state.GetMoves() != []):
        print(str(state))

        if state.playerJustMoved == 2:
            print "Thinking"
            m = UCT(rootstate = state.Clone(), itermax = 5000, verbose = False) # play with values for itermax and verbose = True
            #i = input("Player 1 Enter the location of your move")
            #m = state.rosettaStoneIndex(i)
        else:
            m = UCT(rootstate = state.Clone(), itermax = 1, verbose = False)

            """i = input("Player 1 Enter the location of your move")
            I = state.organizeMove(i[0],i[1])
            while state.ultimateCheck2ThisTimeItsPersonal(I) == False:
                print("\n \n" + str(state))
                print "That move was invalid."
                i = input("Player 1 Enter the location of your move \n")
                I = state.organizeMove(i[0], i[1])
            
            m = state.rosettaStoneIndex(I)
            """
        #print("Best Move: " + str(state.rosettaStoneCoord(m)) + "\n")
        state.DoMove(m)
    print(str(state))
    print state.playerJustMoved
    if state.GetResult(state.playerJustMoved) == 1.0:
        print("Player " + str(state.playerJustMoved) + " wins!")
        return state.playerJustMoved
    elif state.GetResult(state.playerJustMoved) == 0.0:
        print("Player " + str(3 - state.playerJustMoved) + " wins!")
        return 3 - state.playerJustMoved
    else: print("Nobody wins!")
    return state.playerJustMoved

if __name__ == "__main__":
    """ Play a single game to the end using UCT for both players. 
    """
    UCTPlayGame(2,10000)
    """
    scores = [0,0]
    for i in range(0,50):
        scores[UCTPlayGame(2,1000)-1] += 1
        print scores
    print "Player 2, 10000 itterations vs 1 50 games" , scores
    """