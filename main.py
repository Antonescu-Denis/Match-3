import random, pgzrun
from PIL import Image
import os


rows = 11
columns = 11
tile_size = 60
count = 4

TITLE = 'game'
WIDTH = (rows+2) * tile_size
HEIGHT = (columns+2) * tile_size

offset = tile_size*1.5
cursor = Actor('disabled_h', topleft = (offset, offset))
img = Image.open('images/bg.png')
img = img.resize((WIDTH, HEIGHT))
img = img.save('images/resized.png')
bg = Actor('resized')

rotated = False
pos_x, pos_y = 0, 0
enabled = False
dropping = False
has_matched = False
pending_undo = False
should_undo = False
matches = {}
coords = {}

board = []
thing = 6
for row in range(columns):
    tiles = []
    for _ in range(rows):
        tiles.append(random.randint(1, count))
    board.append(tiles)

def draw():
    global board

    screen.clear()
    bg.draw()
    for x in range(columns):
        for y in range(rows):
            tile = board[x][y]
            if tile < 10:
                screen.blit(f"cell{tile}", (y*tile_size+offset+2, x*tile_size+offset+2))
                screen.blit(str(tile), (y*tile_size+offset, x*tile_size+offset))
            else:
                screen.blit(str(tile%10), (y*tile_size+offset, x*tile_size+offset))
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
            rotated = True
            if pos_x == rows-1:
                cursor.y -= tile_size
                pos_x -= 1
        else:
            cursor.image = 'select_h'
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

def special_matches():
    global board, dropping, has_matched, should_undo, matches, coords, enabled

    for key in range(4, 2, -1):
        if len(matches[key]) < 1:
            continue
        for curr_combo in matches[key]:
            is_horizontal = True
            for i in range(1, key):
                if curr_combo[0][0] != curr_combo[i][0]:
                    is_horizontal = False
                    break
            if not is_horizontal:
                continue
            tiles_above = curr_combo[0][0]
            tiles_below = rows-1 - curr_combo[0][0]
            for i in range(key):
                tile_x = curr_combo[i][0]
                tile_y = curr_combo[i][1]
                if coords[curr_combo[i]] == 2:
                    temp = curr_combo[:]
                    above = 0
                    for n in range(1, min(tiles_above, 3)+1):
                        if board[tile_x-n][tile_y] == board[tile_x][tile_y]:
                            above += 1
                            temp.append((tile_x-n, tile_y))
                        else:
                            break
                    below = 0
                    for n in range(1, min(tiles_below, 3)+1):
                        if board[tile_x+n][tile_y] == board[tile_x][tile_y]:
                            below += 1
                            temp.append((tile_x+n, tile_y))
                        else:
                            break

                    if 2 < above+below+1 and above+below+1 < 5:
                        removals = []
                        for temp_key in range(4, 2, -1):
                            for j in range(len(matches[temp_key])):
                                for item in temp:
                                    if item in matches[temp_key][j]:
                                        removals.insert(0, j)
                                        break
                        for thing in removals:
                            matches[temp_key].remove(matches[temp_key][thing])
                        matches['special'].append(temp[:])
                        #for i in range(len(temp)):
                        #    print(f"----- {temp[i]} -----")
                        # somehow skip to the next iteration
                else:
                        pass

    #        if there's any len(3) line combo intersecting/perpendicular
    #        check if it's actually a len(4) by checking the item right before and right after the found len(3)
    #            if found combo is intersecting curr_combo
    #                if both are len(3)
    #                    add those items to set
    #                if one is len(3) and one is len(4)
    #                    add all items from len(3) to set
    #                    for len(4), check where it overlaps
    #                    add all its items to set, except the furthest from intersection
    #                if both are len(4)
    #                    check where it overlaps for both
    #                    add all their items to set, except the furthest ones from intersection
    #            if found combo is perpendicular to curr_combo
    #                if both are len(3)
    #                    for current combo, add all its items to set
    #                    for found combo, add all its items to set, except the furthest from curr_combo
    #                if one is len(3) and one is len(4)
    #                    if len(3) is current combo
    #                        for current combo, add all its items to set
    #                        for found combo, add all its items to set, except the 2 furthest from curr_combo
    #                    if len(4) is current line
    #                        for current combo, add all its items to set, except the furthest from perpendicular combo
    #                        for found combo, add all its items to set, except the furthest from curr_combo
    #                if both are len(4)
    #                    for current combo, add all its items to set, except the furthest from perpendicular combo
    #                    for found combo, add all its items to set, except the 2 furthest from curr_combo

def fill_coords(temp):
    global coords
    
    for thing in temp:
        if thing in coords.keys():
            coords[thing] += 1
        else:
            coords[thing] = 1

def check_matches():
    global board, dropping, has_matched, should_undo, matches, coords, enabled

    matches = {}
    matches[5] = []
    matches['special'] = []
    matches[4] = []
    matches[3] = []
    coords = {}

    if dropping or enabled:
        return
    has_matched = False

    for x in range(columns):
        temp_y = []
        last_type = 0
        for y in range(rows):
            if board[x][y] != 0:
                if len(temp_y) == 5:
                    matches[5].append(temp_y[:])
                    fill_coords(temp_y)
                    has_matched = True
                    should_undo = False
                    temp_y = []
                if board[x][y] == last_type:
                    temp_y.append((x, y))
                else:
                    if len(temp_y) >= 3:
                        matches[len(temp_y)].append(temp_y[:])
                        fill_coords(temp_y)
                        has_matched = True
                        should_undo = False
                    temp_y = []
                    temp_y.append((x, y))
                    last_type = board[x][y]
        if len(temp_y) >= 3:
            matches[len(temp_y)].append(temp_y[:])
            fill_coords(temp_y)
            has_matched = True
            should_undo = False

    for y in range(rows):
        temp_x = []
        last_type = 0
        for x in range(columns):
            if board[x][y] != 0:
                if len(temp_x) == 5:
                    matches[5].append(temp_x[:])
                    fill_coords(temp_x)
                    has_matched = True
                    should_undo = False
                    temp_x = []
                if board[x][y] == last_type:
                    temp_x.append((x, y))
                else:
                    if len(temp_x) >= 3:
                        matches[len(temp_x)].append(temp_x[:])
                        fill_coords(temp_x)
                        has_matched = True
                        should_undo = False
                    temp_x = []
                    temp_x.append((x, y))
                    last_type = board[x][y]
        if len(temp_x) >= 3:
            matches[len(temp_x)].append(temp_x[:])
            fill_coords(temp_x)
            has_matched = True
            should_undo = False

    special_matches()

    print('\n----------------------------------------')
    for key in matches.keys():
        print(f"{key}:")
        for match in matches[key]:
            print(f"    {f"{match}"[1:-1]}")
            for v, h in match:
                board[v][h] += 10
        print()
    print('----------------------------------------\n')

def drop_tiles(x, y):
    global board

    for row in range(x, 0, -1):
        board[row][y] = board[row-1][y]
    board[0][y] = 0

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

    for y in range(rows):
        if board[0][y] == 0:
            board[0][y] = random.randint(1, count)
           
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
    #check_undo()
    #check_gaps()
    #add_new_tiles()
    cursor_status()


cycle()#clock.schedule_interval(cycle, 0.1)
os.environ['SDL_VIDEO_CENTERED'] = '1'
pgzrun.go()