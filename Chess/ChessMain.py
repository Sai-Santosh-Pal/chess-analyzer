import pygame as p
from ChessEngine import *
import random

WIDTH = HEIGHT = 512
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}

# ---------------------------- Utility UI helpers ----------------------------

def drawText(screen, text):
    """Helper to draw centered text on the board surface."""
    # Try Poppins (regular/thin), fallback to Arial (regular) if not available
    try:
        font = p.font.SysFont("Poppins", 40, False, False)
    except:
        font = p.font.SysFont("Arial", 40, False, False)
    # For best results, you can use a custom TTF file with p.font.Font('path/to/Poppins-Regular.ttf', 40)
    textObject = font.render(text, True, p.Color('white'))
    # Draw a semi-transparent rectangle behind the text for readability
    textBg = p.Surface((textObject.get_width()+20, textObject.get_height()+10))
    textBg.set_alpha(180)
    textBg.fill(p.Color('black'))
    textLocation = p.Rect(0, 0, WIDTH, HEIGHT).move(WIDTH/2 - textObject.get_width()/2,
                                                   HEIGHT/2 - textObject.get_height()/2)
    screen.blit(textBg, (textLocation.x-10, textLocation.y-5))
    screen.blit(textObject, textLocation)

def loadImages():
    pieces = ["wp", "wR", "wN", "wB", "wK", "wQ", "bp", "bR", "bN", "bB", "bK", "bQ"]
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("assests/" + piece + ".png"), (SQ_SIZE, SQ_SIZE))

def drawValidMoves(screen, validMoves, sqSelected):
    """Draw dots on squares where the selected piece can move. Captures show the capturable piece in a grey circle."""
    if sqSelected != ():
        r, c = sqSelected
        for move in validMoves:
            if move.startRow == r and move.startCol == c:
                centerX = move.endCol * SQ_SIZE + SQ_SIZE // 2
                centerY = move.endRow * SQ_SIZE + SQ_SIZE // 2
                if move.pieceCaptured != "--":
                    # Draw grey circle
                    radius = SQ_SIZE // 2 - 6
                    p.draw.circle(screen, p.Color('grey'), (centerX, centerY), radius)
                    # Draw the capturable piece image centered in the square
                    piece_img = IMAGES[move.pieceCaptured]
                    img_rect = piece_img.get_rect(center=(centerX, centerY))
                    screen.blit(piece_img, img_rect)
                else:
                    # Draw blue dot for normal move
                    radius = SQ_SIZE // 8
                    p.draw.circle(screen, p.Color('blue'), (centerX, centerY), radius)

def drawSelectedSquare(screen, sqSelected):
    """Highlight the selected square."""
    if sqSelected != ():
        r, c = sqSelected
        s = p.Surface((SQ_SIZE, SQ_SIZE))
        s.set_alpha(100)  # transparency
        s.fill(p.Color('yellow'))
        screen.blit(s, (c * SQ_SIZE, r * SQ_SIZE))

def drawMarkedSquares(screen, markedSquares):
    for (r, c) in markedSquares:
        s = p.Surface((SQ_SIZE, SQ_SIZE))
        s.set_alpha(120)
        s.fill(p.Color('red'))
        screen.blit(s, (c * SQ_SIZE, r * SQ_SIZE))

def drawArrows(screen, arrows):
    for (start, end) in arrows:
        sr, sc = start
        er, ec = end
        start_px = (sc * SQ_SIZE + SQ_SIZE // 2, sr * SQ_SIZE + SQ_SIZE // 2)
        end_px = (ec * SQ_SIZE + SQ_SIZE // 2, er * SQ_SIZE + SQ_SIZE // 2)
        # Draw line
        p.draw.line(screen, (255, 140, 0), start_px, end_px, 8)
        # Draw arrowhead
        import math
        angle = math.atan2(end_px[1] - start_px[1], end_px[0] - start_px[0])
        arrow_length = 20
        arrow_angle = math.pi / 7
        for sign in [-1, 1]:
            dx = arrow_length * math.cos(angle + sign * arrow_angle)
            dy = arrow_length * math.sin(angle + sign * arrow_angle)
            p.draw.line(screen, (255, 140, 0), end_px, (end_px[0] - dx, end_px[1] - dy), 8)

# Update drawGameState to include arrows
def drawGameState(screen, gs, sqSelected, validMoves, markedSquares, arrows, show_arrows=True, show_moves=True):
    drawBoard(screen)
    drawMarkedSquares(screen, markedSquares)
    drawSelectedSquare(screen, sqSelected)
    if show_moves:
        drawValidMoves(screen, validMoves, sqSelected)
    highlightChecks(screen, gs)
    drawPieces(screen, gs.board)
    if show_arrows:
        drawArrows(screen, arrows)


def highlightChecks(screen, gs):
    """Highlight the king square red when that king is in check."""
    if gs.inCheck():
        kingRow, kingCol = gs.whiteKingLocation if gs.whiteToMove else gs.blackKingLocation
        s = p.Surface((SQ_SIZE, SQ_SIZE))
        s.set_alpha(120)  # transparency
        s.fill(p.Color('red'))
        screen.blit(s, (kingCol * SQ_SIZE, kingRow * SQ_SIZE))

class ConfettiParticle:
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(-50, 0)
        self.size = random.randint(4, 10)
        self.color = random.choice([
            (255, 0, 0), (0, 255, 0), (0, 0, 255),
            (255, 255, 0), (255, 0, 255), (0, 255, 255),
            (255, 128, 0), (128, 0, 255), (0, 128, 255)
        ])
        self.vx = random.uniform(-1, 1)
        self.vy = random.uniform(2, 5)
        self.angle = random.uniform(0, 360)
        self.angular_velocity = random.uniform(-5, 5)
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.angle += self.angular_velocity
    def draw(self, screen):
        rect = p.Surface((self.size, self.size), p.SRCALPHA)
        rect.fill(self.color)
        rotated = p.transform.rotate(rect, self.angle)
        screen.blit(rotated, (self.x, self.y))

def drawConfetti(screen, confetti_particles):
    for particle in confetti_particles:
        particle.draw(screen)

def animateMove(move, screen, board, clock):
    dR = move.endRow - move.startRow
    dC = move.endCol - move.startCol
    framesPerSquare = 10
    frameCount = (abs(dR) + abs(dC)) * framesPerSquare
    for frame in range(frameCount + 1):
        r, c = (move.startRow + dR * frame / frameCount, move.startCol + dC * frame / frameCount)
        drawBoard(screen)
        drawPieces(screen, board)
        # Erase the piece from its end square
        color = p.Color("white") if (move.endRow + move.endCol) % 2 == 0 else p.Color("dark green")
        p.draw.rect(screen, color, p.Rect(move.endCol*SQ_SIZE, move.endRow*SQ_SIZE, SQ_SIZE, SQ_SIZE))
        # Draw captured piece (if any)
        if move.pieceCaptured != "--":
            screen.blit(IMAGES[move.pieceCaptured], p.Rect(move.endCol*SQ_SIZE, move.endRow*SQ_SIZE, SQ_SIZE, SQ_SIZE))
        # Draw moving piece
        screen.blit(IMAGES[move.pieceMoved], p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
        p.display.flip()
        clock.tick(60)

def main():
    p.init()
    screen = p.display.set_mode((WIDTH, HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    gs = GameState()
    validMoves = gs.getValidMoves()
    moveMade = False

    loadImages()
    running = True
    sqSelected = ()
    playerClicks = []
    markedSquares = set()
    arrows = []
    arrow_drag_start = None
    confetti_particles = []
    confetti_active = False
    # confetti_timer = 0  # No longer needed
    while running:
        for e in p.event.get():
            if e.type == p.QUIT:
                running == False
            # Right mouse button down: start arrow drag or remove arrow or toggle mark
            elif e.type == p.MOUSEBUTTONDOWN and e.button == 3:
                location = p.mouse.get_pos()
                col = location[0] // SQ_SIZE
                row = location[1] // SQ_SIZE
                # If clicking on start of an arrow, remove it
                for arrow in arrows:
                    if arrow[0] == (row, col):
                        arrows.remove(arrow)
                        break
                else:
                    # If not dragging, start arrow drag
                    arrow_drag_start = (row, col)
                    # Also allow toggling red mark if not dragging
                    if (row, col) in markedSquares:
                        markedSquares.remove((row, col))
                    else:
                        markedSquares.add((row, col))
                    # Clear selection and legal moves when starting arrow mode
                    sqSelected = ()
                    playerClicks = []
            # Right mouse button up: finish arrow drag
            elif e.type == p.MOUSEBUTTONUP and e.button == 3 and arrow_drag_start is not None:
                location = p.mouse.get_pos()
                col = location[0] // SQ_SIZE
                row = location[1] // SQ_SIZE
                if (row, col) != arrow_drag_start:
                    arrows.append((arrow_drag_start, (row, col)))
                arrow_drag_start = None
            # Left click: normal move/select, but also clear mark if present
            elif (e.type == p.MOUSEBUTTONDOWN and e.button == 1 and not moveMade and not gs.checkMate and not gs.staleMate):
                location = p.mouse.get_pos()
                col = location[0] // SQ_SIZE
                row = location[1] // SQ_SIZE
                # If clicking a marked square, just remove the mark
                if (row, col) in markedSquares:
                    markedSquares.remove((row, col))
                    sqSelected = ()
                    playerClicks = []
                else:
                    # If selecting a piece, clear all arrows
                    arrows = []
                    if sqSelected == (row, col):
                        sqSelected = ()
                        playerClicks = []
                    else:
                        sqSelected = (row, col)
                        playerClicks.append(sqSelected)
                    if len(playerClicks) == 2:
                        move = Move(playerClicks[0], playerClicks[1], gs.board)
                        print(move.getChessNotation())
                        for i in range(len(validMoves)):
                            if move == validMoves[i]:
                                gs.makeMove(validMoves[i])
                                animateMove(validMoves[i], screen, gs.board, clock)
                                moveMade = True
                                sqSelected = ()
                                playerClicks = []
                        if not moveMade:
                            playerClicks = [sqSelected]
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:
                    gs.undoMove()
                    moveMade = True
                elif e.key == p.K_r:  # reset the game
                    gs = GameState()
                    validMoves = gs.getValidMoves()
                    sqSelected = ()
                    playerClicks = []
                    moveMade = False
                    markedSquares = set()
                    arrows = []
                    confetti_particles = []
                    confetti_active = False
                    # confetti_timer = 0
                    gs.resetRepetition()
                elif e.key == p.K_y:  # redo move
                    gs.redoMove()
                    moveMade = True

        if moveMade:
            validMoves = gs.getValidMoves()
            moveMade = False
        
        # Only show possible moves if a piece is selected and not drawing an arrow, and there are no arrows
        if sqSelected != () and arrow_drag_start is None and not arrows:
            drawGameState(screen, gs, sqSelected, validMoves, markedSquares, arrows, show_arrows=False, show_moves=True)
        else:
            drawGameState(screen, gs, sqSelected, validMoves, markedSquares, arrows, show_arrows=True, show_moves=False)

        # Display end-game message if applicable
        if gs.checkMate:
            winner = 'Black' if gs.whiteToMove else 'White'
            drawText(screen, f'Checkmate! {winner} wins.')
            # Start confetti if not already started
            if not confetti_active:
                confetti_particles = [ConfettiParticle() for _ in range(120)]
                confetti_active = True
                # confetti_timer = p.time.get_ticks()
        elif gs.staleMate:
            drawText(screen, 'Stalemate!')
            confetti_active = False
            confetti_particles = []
        elif gs.repetitionDraw:
            drawText(screen, 'Draw (by repetition)!')

        # Animate confetti if active
        if confetti_active:
            for particle in confetti_particles:
                particle.update()
            drawConfetti(screen, confetti_particles)
            # Remove particles that fall off the screen
            confetti_particles = [p for p in confetti_particles if p.y < HEIGHT]
            # Stop confetti when all particles are gone
            if not confetti_particles:
                confetti_active = False

        clock.tick(MAX_FPS)
        p.display.flip()

    

def drawBoard(screen):
    colors = [p.Color("white"), p.Color("dark green")]
    for r in range (DIMENSION):
        for c in range (DIMENSION):
            color = colors[((r+c) % 2)]
            p.draw.rect(screen, color, p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
            

def drawPieces(screen, board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--":
                screen.blit(IMAGES[piece],  p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))




if __name__ == "__main__":
    main()