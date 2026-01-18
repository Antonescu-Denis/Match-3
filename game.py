import random, pgzrun, os
from pgzero.builtins import Actor, keys, clock
from PIL import Image

rows = 11
columns = 11
tile_size = 60
count = 7

TITLE = 'game'
WIDTH = (rows+2) * tile_size
HEIGHT = (columns+2) * tile_size

offset = tile_size
cursor = Actor('disabled_h', topleft = (offset, offset*1.5))
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

scores = {5:50, 'special':25, 4:10, 3:5}
curr_score = 0
swaps = 0
finished = False
clear_status = {True:'REACHED_TARGET', False:'NO_MOVES'}

board = []
for _ in range(columns):
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
            if tile:
                screen.blit(f"cell{tile}", (y*tile_size+offset+2, (x+0.5)*tile_size+offset+2))
                screen.blit(str(tile), (y*tile_size+offset, (x+0.5)*tile_size+offset))
            else:
                screen.blit('cell', (y*tile_size+offset+2, (x+0.5)*tile_size+offset+2))
    cursor.draw()
    screen.draw.text(f"Score: {curr_score}", (WIDTH*0.32, 20), fontname = 'minecraft', fontsize = 50, color = (255, 255, 255), align = 'center', owidth = 1)

def on_key_down(key):
    global board, rotated, pos_x, pos_y, enabled, cursor, pending_undo, should_undo, swaps

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
    swaps += 1

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
            if is_horizontal:
                tiles_above = curr_combo[0][0]
                tiles_below = rows-1 - curr_combo[0][0]
                for i in range(key):
                    tile_x = curr_combo[i][0]
                    tile_y = curr_combo[i][1]
                    temp = curr_combo[:]
                    above = 0
                    below = 0
                    if coords[curr_combo[i]] == 2:
                        for n in range(1, min(tiles_above, 3)+1):
                            if (tile_x-n, tile_y) in coords.keys():
                                if coords[(tile_x-n, tile_y)] == 5:
                                    break
                            if board[tile_x-n][tile_y] == board[tile_x][tile_y]:
                                above += 1
                                temp.append((tile_x-n, tile_y))
                            else:
                                break
                        for n in range(1, min(tiles_below, 3)+1):
                            if (tile_x+n, tile_y) in coords.keys():
                                if coords[(tile_x+n, tile_y)] == 5:
                                    break
                            if board[tile_x+n][tile_y] == board[tile_x][tile_y]:
                                below += 1
                                temp.append((tile_x+n, tile_y))
                            else:
                                break
                        if 2 < above+below+1 and above+below+1 < 5:
                            for temp_key in range(4, 2, -1):
                                removals = []
                                for j in range(len(matches[temp_key])):
                                    for item in temp:
                                        if item in matches[temp_key][j]:
                                            removals.insert(0, j)
                                            break
                                for thing in removals:
                                    matches[temp_key].remove(matches[temp_key][thing])
                            if key == 4:
                                if i < 2:
                                    temp.remove(curr_combo[3])
                                else:
                                    temp.remove(curr_combo[0])
                            if above+below+1 == 4:
                                if above > below:
                                    temp.remove((tile_x-above, tile_y))
                                elif above < below:
                                    temp.remove((tile_x+below, tile_y))
                            matches['special'].append(temp[:])
                            break
            else:
                left_tiles = curr_combo[0][1]
                right_tiles = columns-1 - curr_combo[0][1]
                for i in range(key):
                    tile_x = curr_combo[i][0]
                    tile_y = curr_combo[i][1]
                    if coords[curr_combo[i]] == 2:
                        temp = curr_combo[:]
                        left = 0
                        for n in range(1, min(left_tiles, 3)+1):
                            if (tile_x, tile_y-n) in coords.keys():
                                if coords[(tile_x, tile_y-n)] == 5:
                                    break
                            if board[tile_x][tile_y-n] == board[tile_x][tile_y]:
                                left += 1
                                temp.append((tile_x, tile_y-n))
                            else:
                                break
                        right = 0
                        for n in range(1, min(right_tiles, 3)+1):
                            if (tile_x, tile_y+n) in coords.keys():
                                if coords[(tile_x, tile_y+n)] == 5:
                                    break
                            if board[tile_x][tile_y+n] == board[tile_x][tile_y]:
                                right += 1
                                temp.append((tile_x, tile_y+n))
                            else:
                                break
                        if 2 < left+right+1 and left+right+1 < 5:
                            for temp_key in range(4, 2, -1):
                                removals = []
                                for j in range(len(matches[temp_key])):
                                    for item in temp:
                                        if item in matches[temp_key][j]:
                                            removals.insert(0, j)
                                            break
                                for thing in removals:
                                    matches[temp_key].remove(matches[temp_key][thing])
                            if key == 4:
                                if i < 2:
                                    temp.remove(curr_combo[3])
                                else:
                                    temp.remove(curr_combo[0])
                            if left+right+1 == 4:
                                if left > right:
                                    temp.remove((tile_x, tile_y-left))
                                elif left < right:
                                    temp.remove((tile_x, tile_y+right))
                            matches['special'].append(temp[:])
                            break

def fill_coords(temp):
    global coords
    
    if len(temp) == 5:
        for thing in temp:
            coords[thing] = 5
        return

    for thing in temp:
        if thing in coords.keys():
            coords[thing] += 1
        else:
            coords[thing] = 1

def check_matches():
    global board, dropping, has_matched, should_undo, matches, coords, enabled, curr_score

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
            if (x, y) in coords.keys():
                if coords[(x, y)] == 5:
                    temp_y = []
                    last_type = board[x+1][y]
                    continue
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
                    temp_y = []
                    temp_y.append((x, y))
                    last_type = board[x][y]
        if len(temp_y) == 5:
            matches[5].append(temp_y[:])
            fill_coords(temp_y)
            has_matched = True
            should_undo = False
            
    for y in range(rows):
        temp_x = []
        last_type = 0
        for x in range(columns):
            if (x, y) in coords.keys():
                if coords[(x, y)] == 5:
                    temp_x = []
                    continue
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
                    temp_x = []
                    temp_x.append((x, y))
                    last_type = board[x][y]
        if len(temp_x) == 5:
            matches[5].append(temp_x[:])
            fill_coords(temp_x)
            has_matched = True
            should_undo = False


    for x in range(columns):
        temp_y = []
        last_type = 0
        for y in range(rows):
            if (x, y) in coords.keys():
                if coords[(x, y)] == 5:
                    continue
            if board[x][y] != 0:
                if len(temp_y) == 4:
                    matches[4].append(temp_y[:])
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
            if (x, y) in coords.keys():
                if coords[(x, y)] == 5:
                    continue
            if board[x][y] != 0:
                if len(temp_x) == 4:
                    matches[4].append(temp_x[:])
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

    for key in matches.keys():
        for match in matches[key]:
            for v, h in match:
                board[v][h] = 0
            curr_score += scores[key]

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

def reset():
    global rotated, pos_x, pos_y, enabled, dropping
    global has_matched, pending_undo, should_undo, matches, coords
    global curr_score, swaps, finished, board, columns

    rotated = False
    pos_x, pos_y = 0, 0
    enabled = False
    
    dropping = False
    has_matched = False
    pending_undo = False
    should_undo = False
    matches = {}
    coords = {}
    
    curr_score = 0
    swaps = 0
    finished = False
    
    board = []
    for row in range(columns):
        tiles = []
        for _ in range(rows):
            tiles.append(random.randint(1, count))
        board.append(tiles)


def bot():
    global board, enabled, curr_score

    if not enabled:
        return

    matches_exist = False
    total_score = 0
    play = 1
    smol = []
    highest = 0
    
    for x in range(columns):
        for y in range(rows):
            if y < rows-1:
                if board[x][y] == board[x][y+1]:
                    smol.append(((x, y), (x, y+1)))
            if x < columns-1:
                if board[x][y] == board[x+1][y]:
                    smol.append(((x, y), (x+1, y)))

    for tiles in smol:
        if tiles[0][0] == tiles[1][0]:
            max_left = min(tiles[0][1], 3)
            max_right = min(rows-1 - tiles[1][1], 3)
            max_up = min(tiles[0][0], 2)
            max_down = min(columns-1 - tiles[0][0], 2)

            if max_left > 0:
                diff = (tiles[0][0], tiles[0][1]-1)

        elif tiles[0][1] == tiles[1][1]:
            max_up = min(tiles[0][0], 3)
            max_down = min(columns-1 - tiles[1][0], 3)
            max_left = min(tiles[0][1], 2)
            max_right = min(rows-1 - tiles[0][1], 2)



    #print()
    #for tile in smol:
    #    print(f"{tile}")
    #print('\n\n\n')

    #   - scan board for any 2 tile combos
    #       - look for different tiles on both ends
    #       - from those, scan 1 tile in the other 3 directions
    #           - in each direction a matching tile is found
    #           - scan the next tile to see if it's also a matching tile
    #   - based on how many are in each direction
    #   - evaluate which swap to do for that 2 tile combo to create an actual match
    #   - stop at the first 5 line combo found
    enabled = False
    curr_score = 10000

def results():
    # csv:
    #   - game_id - {play}
    #   - score - {curr_score}
    #   - swaps - {swaps}
    #   - finished - {finished}
    #   - why_stopped - {clear_status[finished]}
    #   - moves_left - {10k-score if not finished else '-'}
    # total_score += curr_score
    # add 1 to play
    pass


def cycle():
    global enabled, finished, play

    if curr_score < 10000:
        check_matches()
        check_undo()
        add_new_tiles()
        check_gaps()
        bot()
    else:
        finished = True
        enabled = False
    cursor_status()


clock.schedule_interval(cycle, 0.1)
os.environ['SDL_VIDEO_CENTERED'] = '1'
pgzrun.go()