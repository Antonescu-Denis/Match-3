import random, pgzrun
from PIL import Image
import os


rows = 10
columns = 10
tile_size = 60
count = 7

TITLE = 'game'
WIDTH = (rows+1) * tile_size
HEIGHT = (columns+1) * tile_size

offset = tile_size//2
cursor = Actor('disabled_h', topleft = (offset, offset))
img = Image.open('images/_bg.png')
img = img.resize((WIDTH, HEIGHT))
img = img.save('images/_resized.png')
bg = Actor('_resized')

rotated = False
pos_x, pos_y = 0, 0
enabled = False
dropping = False
has_matched = False
pending_undo = False
should_undo = False

board = []
for row in range(columns):
    tiles = []
    for _ in range(rows):
        tiles.append(random.randint(3, count))
    board.append(tiles)


def draw():
    global board

    screen.clear()
    bg.draw()
    for y in range(columns):
        for x in range(rows):
            tile = board[y][x]
            if tile:
                screen.blit('cell_bg', (x*tile_size+offset+2, y*tile_size+offset+2))
                screen.blit(str(tile), (x*tile_size+offset, y*tile_size+offset))
    cursor.draw()

def on_key_down(key):
    global board, rotated, pos_x, pos_y, enabled, cursor, pending_undo, should_undo

    if not enabled:
        return
    if (key == keys.LEFT or key == keys.A) and pos_y > 0:
        cursor.x -= tile_size
        pos_y -= 1
    if (key == keys.RIGHT or key == keys.D):
        if (not rotated and pos_y < rows-2) or (rotated and pos_y < rows-1):
            cursor.x += tile_size
            pos_y += 1
    if (key == keys.UP or key == keys.W) and pos_x > 0:
        cursor.y -= tile_size
        pos_x -= 1
    if (key == keys.DOWN or key == keys.S):
        if (not rotated and pos_x < columns-1) or (rotated and pos_x < columns-2):
            cursor.y += tile_size
            pos_x += 1
    if key == keys.R:
        if not rotated:
            cursor.image = 'select_v'
            cursor.x -= offset
            cursor.y += offset
            rotated = True

            if pos_x == rows-1:
                cursor.y -= tile_size
                pos_x -= 1
        else:
            cursor.image = 'select_h'
            cursor.x += offset
            cursor.y -= offset
            rotated = False

            if pos_y == columns-1:
                cursor.x -= tile_size
                pos_y -= 1
    if key == keys.SPACE or key == keys.RETURN:
        if rotated:
            board[pos_x][pos_y], board[pos_x+1][pos_y] = board[pos_x+1][pos_y], board[pos_x][pos_y]
            cursor.image = 'disabled_v'
        else:
            board[pos_x][pos_y], board[pos_x][pos_y+1] = board[pos_x][pos_y+1], board[pos_x][pos_y]
            cursor.image = 'disabled_h'
        enabled = False
        pending_undo = True
        should_undo = True

def drop_tiles(x, y):
    global board

    for row in range(x, 0, -1):
        board[row][y] = board[row-1][y]
    board[0][y] = 0

def check_matches():
    global board, dropping, has_matched, should_undo

    matches = {}
    matches[5] = []
    matches['special'] = []
    matches[4] = []
    matches[3] = []
    if dropping or enabled:
        return
    has_matched = False

    # vertical combos
    for y in range(rows):
        temp_x = []
        last_type = 0
        for x in range(columns):
            if board[x][y] != 0:
                if len(temp_x) == 5:
                    matches[5].append(temp_x)
                    has_matched = True
                    should_undo = False
                    temp_x = []
                if board[x][y] == last_type:
                    temp_x.append((x, y))
                else:
                    if len(temp_x) >= 3:
                        matches[len(temp_x)].append(temp_x)
                        has_matched = True
                        should_undo = False
                    temp_x = []
                    temp_x.append((x, y))
                    last_type = board[x][y]
        if len(temp_x) >= 3:
            matches[len(temp_x)].append(temp_x)
            has_matched = True
            should_undo = False

    # horizontal combos
    for x in range(columns):
        temp_y = []
        last_type = 0
        for y in range(rows):
            if board[x][y] != 0:
                if len(temp_y) == 5:
                    matches[5].append(temp_y)
                    has_matched = True
                    should_undo = False
                    temp_y = []
                if board[x][y] == last_type:
                    temp_y.append((x, y))
                else:
                    if len(temp_y) >= 3:
                        matches[len(temp_y)].append(temp_y)
                        has_matched = True
                        should_undo = False
                    temp_y = []
                    temp_y.append((x, y))
                    last_type = board[x][y]
        if len(temp_y) >= 3:
            matches[len(temp_y)].append(temp_y)
            has_matched = True
            should_undo = False

    # if 2 len(3) lines overlap
    #     add their items in matches['special']
    #     remove those items from matches[3]
    # if a len(3) line overlaps with a len(4) line
    #     depending on where the overlap is on the len(4) line
    #         add all items from the len(4) line except for the furthest one from overlap ([0,1] - 3, [2,3] - 0)
    #         add the items from the len(3) line
    # if 2 len(4) lines overlap
    #     depending on where the overlap is on the len(4) lines
    #         add all items from the len(4) lines except for the furthest ones from overlap ([0,1] - 3, [2,3] - 0)
    
    # overlaps, L combos and T combos
    for key in matches.keys():
        for i in range(len(matches[key])):
            pass

    # clear combos
    for key in matches.keys():
        for match in matches[key]:
            for v, h in match:
                board[v][h] = 0

def check_gaps():
    global board, rotated, dropping

    dropping = False
    for x in range(columns-1, -1, -1):
        for y in range(rows):
            if board[x][y] == 0:
                drop_tiles(x, y)
                dropping = True

def add_new_tiles():
    global board

    for x in range(rows):
        if board[0][x] == 0:
            board[0][x] = random.randint(1, count)
           
def cursor_status():
    global dropping, cursor, has_matched, enabled

    if not dropping and not has_matched:
        enabled = True
        cursor.image = 'select_v' if rotated else 'select_h'
    else:
        enabled = False
        cursor.image = 'disabled_v' if rotated else 'disabled_h'

def check_undo():
    global dropping, pending_undo, should_undo

    if not dropping and pending_undo and should_undo:
        if rotated:
            board[pos_x][pos_y], board[pos_x+1][pos_y] = board[pos_x+1][pos_y], board[pos_x][pos_y]
        else:
            board[pos_x][pos_y], board[pos_x][pos_y+1] = board[pos_x][pos_y+1], board[pos_x][pos_y]
        pending_undo = False
        should_undo = False
        cursor.image = 'select_v' if rotated else 'select_h'

def cycle():
    check_matches()
    check_undo()
    check_gaps()
    add_new_tiles()
    cursor_status()


clock.schedule_interval(cycle, 0.5)
os.environ['SDL_VIDEO_CENTERED'] = '1'
pgzrun.go()