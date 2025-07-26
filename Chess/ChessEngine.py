class GameState():
    def __init__(self):
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]]
        self.moveFunctions = {"p": self.getPawnMoves, "R": self.getRookMoves, "N": self.getKnightMoves, 
        "B": self.getBishopMoves, "Q": self.getQueenMoves, "K": self.getKingMoves}

        self.whiteToMove = True
        self.moveLog = []
        self.whiteKingLocation = (7, 4)
        self.blackKingLocation = (0, 4)
        self.checkMate = False
        self.staleMate = False
        self.pins = []
        self.checks = []
        self.enpassantPossible = ()
        self.currentCastlingRight = CastleRights(True, True, True, True)
        self.castleRightsLog = [CastleRights(self.currentCastlingRight.wks, self.currentCastlingRight.bks,
                                             self.currentCastlingRight.wqs, self.currentCastlingRight.bqs)]
        self.redoStack = []
        self.positionCounts = {}
        self.repetitionDraw = False


    def getPositionHash(self):
        # Hash includes board, side to move, castling rights, en passant
        board_str = ''.join([''.join(row) for row in self.board])
        castling = f"{self.currentCastlingRight.wks}{self.currentCastlingRight.bks}{self.currentCastlingRight.wqs}{self.currentCastlingRight.bqs}"
        ep = str(self.enpassantPossible)
        stm = 'w' if self.whiteToMove else 'b'
        return board_str + stm + castling + ep

    def updateRepetition(self):
        h = self.getPositionHash()
        self.positionCounts[h] = self.positionCounts.get(h, 0) + 1
        if self.positionCounts[h] >= 3:
            self.repetitionDraw = True
        else:
            self.repetitionDraw = False

    def makeMove(self, move, clear_redo=True):
        self.board[move.startRow][move.startCol] = "--"
        self.board[move.endRow][move.endCol] = move.pieceMoved
        self.moveLog.append(move)
        self.whiteToMove = not self.whiteToMove
        if move.pieceMoved == "wK":
            self.whiteKingLocation = (move.endRow, move.endCol)
        elif move.pieceMoved == "bK":
            self.blackKingLocation = (move.endRow, move.endCol)
        if move.isPawnPromotion:
            self.board[move.endRow][move.endCol] = move.pieceMoved[0] + "Q"
        if move.isEnpassantMove:
            self.board[move.startRow][move.endCol] = "--"
        
        if move.pieceMoved[1] == "p" and abs(move.startRow - move.endRow) == 2:
            self.enpassantPossible = ((move.startRow + move.endRow) //2, move.startCol)
        else:
            self.enpassantPossible = ()
       
        #castle move
        if move.isCastleMove:
            print(f"\nExecuting castle move:")
            print(f"Before castle - King at ({move.startRow}, {move.startCol}) moving to ({move.endRow}, {move.endCol})")
            if move.endCol - move.startCol == 2: #kingside castle
                print("Kingside castle - Moving rook from h1/h8 to f1/f8")
                self.board[move.endRow][move.endCol - 1] = self.board[move.endRow][move.endCol + 1] #moves the rook to f1/f8
                self.board[move.endRow][move.endCol + 1] = "--" #erase old rook from h1/h8
            else: #queen side castle
                print("Queenside castle - Moving rook from a1/a8 to d1/d8")
                self.board[move.endRow][move.endCol + 1] = self.board[move.endRow][move.endCol - 2] #moves the rook to d1/d8
                self.board[move.endRow][move.endCol - 2] = "--" #erase old rook from a1/a8
            print("Board state after castle:")
            self._printBoard()

        #update castling rights - whenever its a rook or a king move
        self.updateCastleRights(move)
        self.castleRightsLog.append(CastleRights(self.currentCastlingRight.wks, self.currentCastlingRight.bks,
                                self.currentCastlingRight.wqs, self.currentCastlingRight.bqs))
        if clear_redo:
            self.redoStack = []  # Only clear redo stack on user move
        self.updateRepetition()



    def undoMove(self):
        if len(self.moveLog) != 0:
            move = self.moveLog.pop()
            self.board[move.startRow][move.startCol] = move.pieceMoved
            self.board[move.endRow][move.endCol] = move.pieceCaptured
            self.whiteToMove = not self.whiteToMove
            if move.pieceMoved == "wK":
                self.whiteKingLocation = (move.startRow, move.startCol)
            elif move.pieceMoved == "bK":
                self.blackKingLocation = (move.startRow, move.startCol)
            if move.isEnpassantMove:
                self.board[move.endRow][move.endCol] = "--"
                self.board[move.startRow][move.endCol] = move.pieceCaptured
                self.enpassantPossible = (move.endRow, move.endCol)
            if move.pieceMoved[1] == "p" and abs(move.startRow - move.endRow) == 2:
                self.enpassantPossible = ()
            self.redoStack.append(move)
            # Remove this position from repetition count
            h = self.getPositionHash()
            if h in self.positionCounts:
                self.positionCounts[h] -= 1
            self.repetitionDraw = False

    def redoMove(self):
        if self.redoStack:
            move = self.redoStack.pop()
            self.makeMove(move, clear_redo=False)

    def updateCastleRights(self, move):
        if move.pieceMoved == "wK":
            self.currentCastlingRight.wks = False
            self.currentCastlingRight.wqs = False
        elif move.pieceMoved == "bK":
            self.currentCastlingRight.bks = False
            self.currentCastlingRight.bqs = False
        elif move.pieceMoved == "wR":
            if move.startRow == 7:
                if move.startCol == 0: #left rook
                    self.currentCastlingRight.wqs = False
                elif move.startCol == 7: #right rook
                    self.currentCastlingRight.wks = False
        elif move.pieceMoved == "bR":
            if move.startRow == 0:
                if move.startCol == 0: #left rook
                    self.currentCastlingRight.bqs = False
                elif move.startCol == 7: #right rook
                    self.currentCastlingRight.bks = False

    def getValidMoves(self):
        tempEnpassantPossible = self.enpassantPossible
        tempCastleRights = CastleRights(self.currentCastlingRight.wks, self.currentCastlingRight.bks,
                                        self.currentCastlingRight.wqs, self.currentCastlingRight.bqs) #copy the
        # ------------------------------------------------------------------
        # 1. Detect checks and pins FIRST so that move generation respects them
        # ------------------------------------------------------------------

        inCheckFlag, self.pins, self.checks = self.checkForPinsAndChecks()

        # ------------------------------------------------------------------
        # 2. Generate all standard (non-castling) moves. Because self.pins has been
        #    set, the individual piece-move generators will correctly prune moves
        #    for pinned pieces.
        # ------------------------------------------------------------------

        moves = self.getAllPossibleMoves()

        if self.whiteToMove:
            kingRow, kingCol = self.whiteKingLocation
        else:
            kingRow, kingCol = self.blackKingLocation

        if inCheckFlag:
            if len(self.checks) == 1:
                moves = self.getAllPossibleMoves()
                check = self.checks[0]
                checkRow, checkCol, checkDirRow, checkDirCol = check
                pieceChecking = self.board[checkRow][checkCol]

                validSquares = []
                if pieceChecking[1] == "N":  # Knight checks can only be blocked by capturing
                    validSquares = [(checkRow, checkCol)]
                else:
                    for i in range(1, 8):
                        validSquare = (kingRow + checkDirRow * i, kingCol + checkDirCol * i)
                        validSquares.append(validSquare)
                        if validSquare == (checkRow, checkCol):
                            break

                # Remove moves that don't block or capture the checking piece
                for i in range(len(moves) - 1, -1, -1):
                    if moves[i].pieceMoved[1] != "K":
                        if (moves[i].endRow, moves[i].endCol) not in validSquares:
                            moves.pop(i)
            else:
                # Double check — only king moves are legal. Clear other moves first.
                moves = []
                self.getKingMoves(kingRow, kingCol, moves)
        else:
            # King is not in check – we can now consider castling moves.
            if self.whiteToMove:
                self.getCastleMoves(self.whiteKingLocation[0], self.whiteKingLocation[1], moves)
            else:
                self.getCastleMoves(self.blackKingLocation[0], self.blackKingLocation[1], moves)

        # ------------------------------------------------------------------
        # 3. Final legality filter – ensure no move leaves own king in check
        # ------------------------------------------------------------------

        legalMoves = []
        for move in moves:
            self.makeMove(move)
            # After making the move, the turn has switched to the opponent. Switch it back
            # temporarily so `inCheck()` tests OUR king, not the opponent's.
            self.whiteToMove = not self.whiteToMove
            isOwnKingInCheck = self.inCheck()
            self.whiteToMove = not self.whiteToMove  # restore turn indicator
            self.undoMove()
            if not isOwnKingInCheck:
                legalMoves.append(move)

        # ------------------------------------------------------------------
        # 4. Determine checkmate or stalemate conditions (after legality filter)
        # ------------------------------------------------------------------

        if len(legalMoves) == 0:
            # Recompute to be absolutely certain, ignoring earlier cached value
            currentInCheck = self.inCheck()
            if currentInCheck:
                self.checkMate = True
                self.staleMate = False
            else:
                self.staleMate = True
                self.checkMate = False
        else:
            self.checkMate = False
            self.staleMate = False

        self.enpassantPossible = tempEnpassantPossible
        self.currentCastlingRight = tempCastleRights
        return legalMoves


    def checkForPinsAndChecks(self):
        pins = []
        checks = []
        inCheck = False
        if self.whiteToMove:
            enemyColor = "b"
            allyColor = "w"
            startRow = self.whiteKingLocation[0]
            startCol = self.whiteKingLocation[1]
        else:
            enemyColor = "w"
            allyColor = "b"
            startRow = self.blackKingLocation[0]
            startCol = self.blackKingLocation[1]
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1,), (1, -1), (1, 1))
        for j in range(len(directions)):
            d = directions[j]
            possiblePin = ()
            for i in range(1, 8):
                endRow = startRow + d[0] * i
                endCol = startCol + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    endPiece = self.board[endRow][endCol]
                    if endPiece[0] == allyColor and endPiece[1] != "K":
                        if possiblePin == ():
                            possiblePin = (endRow, endCol, d[0], d[1])
                        else:
                            break
                    elif endPiece[0] == enemyColor:
                        type = endPiece[1]
                        # For orthogonal directions (j 0–3) rooks or queens give check/pin.
                        # For diagonal directions (j 4–7) bishops or queens give check/pin.
                        if (0 <= j <= 3 and type == "R") or \
                                (4 <= j <= 7 and type == "B") or \
                                (i == 1 and type == "p" and ((enemyColor == "w" and 6 <= j <= 7) or (enemyColor == "b" and 4 <= j <= 5))) or \
                                (type == "Q") or (i == 1 and type == "K"):
                            if possiblePin == ():
                                inCheck = True 
                                checks.append((endRow, endCol, d[0], d[1]))
                                break
                            else:
                                pins.append(possiblePin)
                                break
                        else:
                            break
        
        knightMoves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1,-2), (1, 2), (2, -1), (2, 1))
        for m in knightMoves:
            endRow = startRow + m[0]
            endCol = startCol + m[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] == enemyColor and endPiece[1] == "N":
                    inCheck = True
                    checks.append((endRow, endCol, m[0], m[1]))
        return inCheck, pins, checks

    def inCheck(self):
        if self.whiteToMove:
            return self.squareUnderAttack(self.whiteKingLocation[0], self.whiteKingLocation[1])
        else:
            return self.squareUnderAttack(self.blackKingLocation[0], self.blackKingLocation[1])

    def squareUnderAttack(self, r, c):
        self.whiteToMove = not self.whiteToMove
        oppMoves = self.getAllPossibleMoves()
        self.whiteToMove = not self.whiteToMove
        for move in oppMoves:
            if move.endRow == r and move.endCol == c:
                return True
        return False

    def getAllPossibleMoves(self):
        moves = []
        for r in range (len(self.board)):
            for c in range(len(self.board[r])):
                turn = self.board[r][c][0]
                if (turn == "w" and self.whiteToMove) or (turn == "b" and not self.whiteToMove):
                    piece = self.board[r][c][1]
                    self.moveFunctions[piece](r, c, moves)
        return moves

    def getPawnMoves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) -1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        if self.whiteToMove:
            if self.board[r - 1][c] == "--":
                if not piecePinned or pinDirection == (-1, 0):
                    moves.append(Move((r, c), (r-1, c), self.board))
                    if r == 6 and self.board[r - 2][c] == "--":
                        moves.append(Move((r, c), (r-2, c), self.board))
            if c - 1 >= 0:
                if self.board[r - 1][c - 1][0] == "b":
                    if not piecePinned or pinDirection == (-1, -1):
                        moves.append(Move((r, c), (r-1, c-1), self.board))
                elif (r-1, c-1) == self.enpassantPossible:
                    moves.append(Move((r, c), (r-1, c-1), self.board, isEnpassantMove = True))

            if c + 1 <= 7:
                if self.board[r - 1][c + 1][0] == "b":
                    if not piecePinned or pinDirection == (-1, 1):
                        moves.append(Move((r, c), (r-1, c+1), self.board))
                elif (r-1, c+1) == self.enpassantPossible:
                    moves.append(Move((r, c), (r-1, c+1), self.board, isEnpassantMove = True))
        else:
            if self.board[r+1][c] == "--":
                if not piecePinned or pinDirection == (1, 0):
                    moves.append(Move((r, c), (r+1, c), self.board))
                    if r == 1 and self.board[r + 2][c] == "--":
                        moves.append(Move((r, c), (r + 2, c), self.board))
            if c - 1 >= 0:
                if self.board[r + 1][c - 1][0] == "w":
                    if not piecePinned or pinDirection == (1, -1):
                        moves.append(Move((r, c), (r + 1, c - 1), self.board))
                elif (r+1, c-1) == self.enpassantPossible:
                    moves.append(Move((r, c), (r+1, c-1), self.board, isEnpassantMove = True))
            if c + 1 <= 7:
                if self.board[r + 1][c + 1][0] == "w":
                    if not piecePinned or pinDirection == (1, 1):
                        moves.append(Move((r, c), (r + 1, c + 1), self.board))
                elif (r+1, c+1) == self.enpassantPossible:
                    moves.append(Move((r, c), (r+1, c+1), self.board, isEnpassantMove = True))

    def getRookMoves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        pinsCopy = self.pins[:]
        for i in range(len(pinsCopy) -1, -1, -1):
            if pinsCopy[i][0] == r and pinsCopy[i][1] == c:
                piecePinned = True
                pinDirection = (pinsCopy[i][2], pinsCopy[i][3])
                if self.board[r][c][1] != "Q":
                    self.pins.remove(pinsCopy[i])
                break
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1))
        enemyColor = "b" if self.whiteToMove else "w"
        for d in directions:
            for i in range(1, 8):
                endRow = r + d[0] * i 
                endCol = c + d[1] * i 
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    if not piecePinned or pinDirection == d or pinDirection == (-d[0], -d[1]):
                        endPiece = self.board[endRow][endCol]
                        if endPiece == "--":
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                        elif endPiece[0] == enemyColor:
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                            break
                        else:
                            break
                else:   
                    break

    def getKnightMoves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) -1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break
        knightMoves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1,-2), (1, 2), (2, -1), (2, 1))
        allyColor = "w" if self.whiteToMove else "b"
        for m in knightMoves:
            endRow = r + m[0]
            endCol = c + m[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                if not piecePinned:
                    endPiece = self.board[endRow][endCol]
                    if endPiece[0] != allyColor:
                        moves.append(Move((r, c), (endRow, endCol), self.board))

    def getBishopMoves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        pinsCopy = self.pins[:]
        for i in range(len(pinsCopy) -1, -1, -1):
            if pinsCopy[i][0] == r and pinsCopy[i][1] == c:
                piecePinned = True
                pinDirection = (pinsCopy[i][2], pinsCopy[i][3])
                self.pins.remove(pinsCopy[i])
                break
        directions = ((-1, -1), (-1, 1), (1, -1), (1, 1))
        enemyColor = "b" if self.whiteToMove else "w"
        for d in directions:
            for i in range(1, 8):
                endRow = r + d[0] * i
                endCol = c + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    if not piecePinned or pinDirection == d or pinDirection == (-d[0], -d[1]):
                        endPiece = self.board[endRow][endCol]
                        if endPiece == "--":
                            moves.append(Move((r, c), (endRow,endCol), self.board))
                        elif endPiece[0] == enemyColor:
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                            break
                        else:
                            break
                else:
                    break


    def getQueenMoves(self, r, c, moves):
        self.getRookMoves(r, c, moves)
        self.getBishopMoves(r, c, moves)

    def getKingMoves(self, r, c, moves):
        rowMoves = (-1, -1, -1, 0, 0, 1, 1, 1)
        colMoves = (-1, 0, 1, -1, 1, -1, 0, 1)
        allyColor = "w" if self.whiteToMove else "b"
        for i in range(8):
            endRow = r + rowMoves[i]
            endCol = c + colMoves[i]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] != allyColor:
                    if allyColor == "w":
                        self.whiteKingLocation = (endRow, endCol)
                    else:
                        self.blackKingLocation = (endRow, endCol)
                    inCheckFlag, pins, checks = self.checkForPinsAndChecks()
                    if not inCheckFlag:
                        moves.append(Move((r, c), (endRow, endCol), self.board))
                    if allyColor == "w":
                        self.whiteKingLocation = (r, c)
                    else:
                        self.blackKingLocation = (r, c)


    """
    get Castle moves
    """
    def getCastleMoves(self, r, c, moves):
        print(f"\nChecking castle moves for {'white' if self.whiteToMove else 'black'} at row {r}, col {c}")
        if self.squareUnderAttack(r, c):
            print("Cannot castle: King is in check")
            return #cant castle while in check
        if (self.whiteToMove and self.currentCastlingRight.wks) or (not self.whiteToMove and self.currentCastlingRight.bks):
            print("Checking kingside castle possibility")
            self.getKingsideCastleMoves(r, c, moves)
        if (self.whiteToMove and self.currentCastlingRight.wqs) or (not self.whiteToMove and self.currentCastlingRight.bqs):
            print("Checking queenside castle possibility")
            self.getQueensideCastleMoves(r, c, moves)
        

    def getKingsideCastleMoves(self, r, c, moves):
        print(f"Kingside castle check - squares empty? {self.board[r][c + 1] == '--' and self.board[r][c + 2] == '--'}")
        if self.board[r][c + 1] == "--" and self.board[r][c + 2] == "--":
            if not self.squareUnderAttack(r, c + 1) and not self.squareUnderAttack(r, c + 2):
                print("Adding kingside castle move")
                moves.append(Move((r, c), (r, c + 2), self.board, isCastleMove=True))
            else:
                print("Cannot castle kingside: Path through check")

    def getQueensideCastleMoves(self, r, c, moves):
        print(f"Queenside castle check - squares empty? {self.board[r][c-1] == '--' and self.board[r][c-2] == '--'}")
        if self.board[r][c-1] == "--" and self.board[r][c-2] == "--":
            if not self.squareUnderAttack(r, c - 1) and not self.squareUnderAttack(r, c - 2):
                print("Adding queenside castle move")
                moves.append(Move((r, c), (r, c - 2), self.board, isCastleMove=True))
            else:
                print("Cannot castle queenside: Path through check")

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------

    def _printBoard(self):
        """Pretty-prints the current board to stdout for debugging purposes."""
        for row in self.board:
            print(" ".join(piece.ljust(2) for piece in row))
        print()

    def resetRepetition(self):
        self.positionCounts = {}
        self.repetitionDraw = False


class CastleRights():
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs


class Move():

    ranksToRows = {"1": 7, "2": 6, "3": 5, "4": 4,
                   "5": 3, "6": 2, "7": 1, "8": 0}
    rowsToRanks = {v: k for k, v in ranksToRows.items()}
    filesToCols = {"a": 0, "b": 1, "c": 2, "d": 3,
                   "e": 4, "f": 5, "g": 6, "h": 7}
    colsToFiles = {v: k for k, v in filesToCols.items()}

    def __init__(self, startSq, endSq, board, isEnpassantMove = False, isCastleMove = False):
        self.startRow = startSq[0]
        self.startCol = startSq[1]
        self.endRow = endSq[0]
        self.endCol = endSq[1]
        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]
        self.isPawnPromotion = (self.pieceMoved == "wp" and self.endRow == 0) or (self.pieceMoved == "bp" and self.endRow == 7)
        self.isEnpassantMove = isEnpassantMove
        if self.isEnpassantMove:
            self.pieceCaptured = "wp" if self.pieceMoved == "bp" else "bp"
        #castle move
        self.isCastleMove = isCastleMove

        self.moveID = self.startRow * 1000 + self.startCol * 100 + self.endRow * 10 + self.endCol

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False


    def getChessNotation(self):
        return self.getRankFile(self.startRow, self.startCol) + self.getRankFile(self.endRow, self.endCol)

    def getRankFile(self, r, c):
        return self.colsToFiles[c] + self.rowsToRanks[r]