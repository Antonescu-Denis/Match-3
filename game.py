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
total_score = 0
play = 1
swaps = 0
total_swaps = 0
finished = False
clear_status = 'REACHED_TARGET'

turn = 'bot'
bot_cell_1 = None
bot_cell_2 = None

board = []
for _ in range(columns):
    tiles = []
    for _ in range(rows):
        tiles.append(random.randint(2, count))
    board.append(tiles)

with open('results\\summary.csv', 'w') as file:
    file.write('game_id,points,swaps,reached_target,stopping_reason')

def draw():
    global board, turn

    screen.clear()
    bg.draw()
    for x in range(columns):
        for y in range(rows):
            tile = board[x][y]
            if bot_cell_1 != None:
                screen.blit('bot_cell', (bot_cell_1[1]*tile_size+offset+2, (bot_cell_1[0]+0.5)*tile_size+offset+2))
            if bot_cell_2 != None:
                screen.blit('bot_cell', (bot_cell_2[1]*tile_size+offset+2, (bot_cell_2[0]+0.5)*tile_size+offset+2))

            if tile:
                screen.blit(f"cell{tile}", (y*tile_size+offset+2, (x+0.5)*tile_size+offset+2))
                screen.blit(str(tile), (y*tile_size+offset, (x+0.5)*tile_size+offset))
            else:
                screen.blit('cell', (y*tile_size+offset+2, (x+0.5)*tile_size+offset+2))
    if turn == 'player':
        cursor.draw()
    screen.draw.text(f"Score: {curr_score}", (WIDTH*0.32, 20), fontname = 'minecraft', fontsize = 50, color = (255, 255, 255), align = 'center', owidth = 1)

def on_key_down(key):
    global cursor, pending_undo, should_undo, swaps, total_swaps
    global board, rotated, pos_x, pos_y, enabled, turn

    if not enabled or turn == 'bot':
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
    total_swaps += 1

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
    global board, dropping, has_matched, should_undo, matches
    global coords, enabled, curr_score, total_score

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
            total_score += scores[key]

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
            board[0][y] = random.randint(2, count)
           
def cursor_status():
    global dropping, cursor, has_matched, enabled, turn

    if turn == 'bot':
        return

    if not dropping and not has_matched:
        enabled = True
        cursor.image = 'select_v' if rotated else 'select_h'
    else:
        enabled = False
        cursor.image = 'disabled_v' if rotated else 'disabled_h'

def check_undo():
    global dropping, pending_undo, should_undo, turn

    if turn == 'bot':
        return

    if not dropping and pending_undo and should_undo:
        if rotated:
            board[pos_x][pos_y], board[pos_x+1][pos_y] = board[pos_x+1][pos_y], board[pos_x][pos_y]
        else:
            board[pos_x][pos_y], board[pos_x][pos_y+1] = board[pos_x][pos_y+1], board[pos_x][pos_y]
        pending_undo = False
        should_undo = False
        cursor.image = 'select_v' if rotated else 'select_h'

def reset():
    global curr_score, swaps, finished, board, columns, bot_cell_1, bot_cell_2
    global has_matched, pending_undo, should_undo, matches, coords
    global rotated, pos_x, pos_y, enabled, dropping, clear_status

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
    clear_status = 'REACHED_TARGET'

    bot_cell_1 = None
    bot_cell_2 = None
    
    board = []
    for row in range(columns):
        tiles = []
        for _ in range(rows):
            tiles.append(random.randint(1, count))
        board.append(tiles)

def bot():
    global board, enabled, scores, dropping, has_matched
    global pending_undo, should_undo, clear_status
    global finished, turn, swaps, total_swaps, bot_cell_1, bot_cell_2

    if not dropping and not has_matched:
        enabled = True
    else:
        enabled = False

    if not enabled or turn == 'player':
        return

    matches_exist = False
    smol = []
    highest = 0
    need_swap = []
    
    for x in range(columns):
        for y in range(rows):
            if y < rows-1:
                if board[x][y] == board[x][y+1]:
                    smol.append(((x, y), (x, y+1)))
            if x < columns-1:
                if board[x][y] == board[x+1][y]:
                    smol.append(((x, y), (x+1, y)))

    for tiles in smol:
        x1, y1 = tiles[0]
        x2, y2 = tiles[1]
        tile_type = board[x1][y1]
        if x1 == x2:
            max_left = min(y1, 3)
            max_right = min(rows-1 - y2, 3)
            max_up = min(x1, 2)
            max_down = min(columns-1 - x1, 2)
    
            if max_left > 0:
                left = 0
                up_1 = 0
                down_1 = 0
                diff_x = x1
                diff_y = y1-1
    
                for i in range(1, max_left):
                    if board[diff_x][diff_y-i] == tile_type:
                        left += 1
                    else:
                        break
                for i in range(1, max_up+1):
                    if board[diff_x-i][diff_y] == tile_type:
                        up_1 += 1
                    else:
                        break
                for i in range(1, max_down+1):
                    if board[diff_x+i][diff_y] == tile_type:
                        down_1 += 1
                    else:
                        break
    
                if left == 2:
                    if up_1 > 0:
                        highest = scores[5]
                        need_swap = [(diff_x, diff_y), (diff_x-1, diff_y)]
                        matches_exist = True
                    elif down_1 > 0:
                        highest = scores[5]
                        need_swap = [(diff_x, diff_y), (diff_x+1, diff_y)]
                        matches_exist = True
                if highest < scores['special']:
                    if up_1 == 2:
                        if left == 1:
                            highest = scores['special']
                            need_swap = [(diff_x, diff_y), (diff_x, diff_y-1)]
                            matches_exist = True
                        elif down_1 > 0:
                            highest = scores['special']
                            need_swap = [(diff_x, diff_y), (diff_x+1, diff_y)]
                            matches_exist = True
                    elif down_1 == 2:
                        if left == 1:
                            highest = scores['special']
                            need_swap = [(diff_x, diff_y), (diff_x, diff_y-1)]
                            matches_exist = True
                        elif up_1 > 0:
                            highest = scores['special']
                            need_swap = [(diff_x, diff_y), (diff_x-1, diff_y)]
                            matches_exist = True
                    elif up_1 == 1 and down_1 == 1:
                        if left == 1:
                            highest = scores['special']
                            need_swap = [(diff_x, diff_y), (diff_x, diff_y-1)]
                            matches_exist = True
                if highest < scores[4]:
                    if left == 1:
                        if up_1 > 0:
                            highest = scores[4]
                            need_swap = [(diff_x, diff_y), (diff_x-1, diff_y)]
                            matches_exist = True
                        elif down_1 > 0:
                            highest = scores[4]
                            need_swap = [(diff_x, diff_y), (diff_x+1, diff_y)]
                            matches_exist = True
                if highest < scores[3]:
                    if left == 1:
                        highest = scores[3]
                        need_swap = [(diff_x, diff_y), (diff_x, diff_y-1)]
                        matches_exist = True
                    elif up_1 > 0:
                        highest = scores[3]
                        need_swap = [(diff_x, diff_y), (diff_x-1, diff_y)]
                        matches_exist = True
                    elif down_1 > 0:
                        highest = scores[3]
                        need_swap = [(diff_x, diff_y), (diff_x+1, diff_y)]
                        matches_exist = True
            if highest == scores[5]:
                break
    
            if max_right > 0:
                right = 0
                up_2 = 0
                down_2 = 0
                diff_x = x2
                diff_y = y2+1
    
                for i in range(1, max_right):
                    if board[diff_x][diff_y+i] == tile_type:
                        right += 1
                    else:
                        break
                for i in range(1, max_up+1):
                    if board[diff_x-i][diff_y] == tile_type:
                        up_2 += 1
                    else:
                        break
                for i in range(1, max_down+1):
                    if board[diff_x+i][diff_y] == tile_type:
                        down_2 += 1
                    else:
                        break
    
                if right == 2:
                    if up_2 > 0:
                        highest = scores[5]
                        need_swap = [(diff_x, diff_y), (diff_x-1, diff_y)]
                        matches_exist = True
                    elif down_2 > 0:
                        highest = scores[5]
                        need_swap = [(diff_x, diff_y), (diff_x+1, diff_y)]
                        matches_exist = True
                if highest < scores['special']:
                    if up_2 == 2:
                        if right == 1:
                            highest = scores['special']
                            need_swap = [(diff_x, diff_y), (diff_x, diff_y+1)]
                            matches_exist = True
                        elif down_2 > 0:
                            highest = scores['special']
                            need_swap = [(diff_x, diff_y), (diff_x+1, diff_y)]
                            matches_exist = True
                    elif down_2 == 2:
                        if right == 1:
                            highest = scores['special']
                            need_swap = [(diff_x, diff_y), (diff_x, diff_y+1)]
                            matches_exist = True
                        elif up_2 > 0:
                            highest = scores['special']
                            need_swap = [(diff_x, diff_y), (diff_x-1, diff_y)]
                            matches_exist = True
                    elif up_2 == 1 and down_2 == 1:
                        if right == 1:
                            highest = scores['special']
                            need_swap = [(diff_x, diff_y), (diff_x, diff_y+1)]
                            matches_exist = True
                if highest < scores[4]:
                    if right == 1: 
                        if up_2 > 0:
                            highest = scores[4]
                            need_swap = [(diff_x, diff_y), (diff_x-1, diff_y)]
                            matches_exist = True
                        elif down_2 > 0:
                            highest = scores[4]
                            need_swap = [(diff_x, diff_y), (diff_x+1, diff_y)]
                            matches_exist = True
                if highest < scores[3]:
                    if right == 1:
                        highest = scores[3]
                        need_swap = [(diff_x, diff_y), (diff_x, diff_y+1)]
                        matches_exist = True
                    elif up_2 > 0:
                        highest = scores[3]
                        need_swap = [(diff_x, diff_y), (diff_x-1, diff_y)]
                        matches_exist = True
                    elif down_2 > 0:
                        highest = scores[3]
                        need_swap = [(diff_x, diff_y), (diff_x+1, diff_y)]
                        matches_exist = True
            if highest == scores[5]:
                break
        elif y1 == y2:
            max_up = min(x1, 3)
            max_down = min(columns-1 - x2, 3)
            max_left = min(y1, 2)
            max_right = min(rows-1 - y1, 2)
    
            if max_up > 0:
                up = 0
                left_1 = 0
                right_1 = 0
                diff_x = x1-1
                diff_y = y1
    
                for i in range(1, max_up):
                    if board[diff_x-i][diff_y] == tile_type:
                        up += 1
                    else:
                        break
                for i in range(1, max_left+1):
                    if board[diff_x][diff_y-i] == tile_type:
                        left_1 += 1
                    else:
                        break
                for i in range(1, max_right+1):
                    if board[diff_x][diff_y+i] == tile_type:
                        right_1 += 1
                    else:
                        break
    
                if up == 2:
                    if left_1 > 0:
                        highest = scores[5]
                        need_swap = [(diff_x, diff_y), (diff_x, diff_y-1)]
                        matches_exist = True
                    elif right_1 > 0:
                        highest = scores[5]
                        need_swap = [(diff_x, diff_y), (diff_x, diff_y+1)]
                        matches_exist = True
                if highest < scores['special']:
                    if left_1 == 2:
                        if up == 1:
                            highest = scores['special']
                            need_swap = [(diff_x, diff_y), (diff_x-1, diff_y)]
                            matches_exist = True
                        elif right_1 > 0:
                            highest = scores['special']
                            need_swap = [(diff_x, diff_y), (diff_x, diff_y+1)]
                            matches_exist = True
                    elif right_1 == 2:
                        if up == 1:
                            highest = scores['special']
                            need_swap = [(diff_x, diff_y), (diff_x-1, diff_y)]
                            matches_exist = True
                        elif left_1 > 0:
                            highest = scores['special']
                            need_swap = [(diff_x, diff_y), (diff_x, diff_y-1)]
                            matches_exist = True
                    elif left_1 == 1 and right_1 == 1:
                        if up == 1:
                            highest = scores['special']
                            need_swap = [(diff_x, diff_y), (diff_x-1, diff_y)]
                            matches_exist = True
                if highest < scores[4]:
                    if up == 1:
                        if left_1 > 0:
                            highest = scores[4]
                            need_swap = [(diff_x, diff_y), (diff_x, diff_y-1)]
                            matches_exist = True
                        elif right_1 > 0:
                            highest = scores[4]
                            need_swap = [(diff_x, diff_y), (diff_x, diff_y+1)]
                            matches_exist = True
                if highest < scores[3]:
                    if up == 1:
                        highest = scores[3]
                        need_swap = [(diff_x, diff_y), (diff_x-1, diff_y)]
                        matches_exist = True
                    elif left_1 > 0:
                        highest = scores[3]
                        need_swap = [(diff_x, diff_y), (diff_x, diff_y-1)]
                        matches_exist = True
                    elif right_1 > 0:
                        highest = scores[3]
                        need_swap = [(diff_x, diff_y), (diff_x, diff_y+1)]
                        matches_exist = True
            if highest == scores[5]:
                break
    
            if max_down > 0:
                down = 0
                left_2 = 0
                right_2 = 0
                diff_x = x2+1
                diff_y = y2
    
                for i in range(1, max_down):
                    if board[diff_x+i][diff_y] == tile_type:
                        down += 1
                    else:
                        break
                for i in range(1, max_left+1):
                    if board[diff_x][diff_y-i] == tile_type:
                        left_2 += 1
                    else:
                        break
                for i in range(1, max_right+1):
                    if board[diff_x][diff_y+i] == tile_type:
                        right_2 += 1
                    else:
                        break
    
                if down == 2:
                    if left_2 > 0:
                        highest = scores[5]
                        need_swap = [(diff_x, diff_y), (diff_x, diff_y-1)]
                        matches_exist = True
                    elif right_2 > 0:
                        highest = scores[5]
                        need_swap = [(diff_x, diff_y), (diff_x, diff_y+1)]
                        matches_exist = True
                if highest < scores['special']:
                    if left_2 == 2:
                        if down == 1:
                            highest = scores['special']
                            need_swap = [(diff_x, diff_y), (diff_x+1, diff_y)]
                            matches_exist = True
                        elif right_2 > 0:
                            highest = scores['special']
                            need_swap = [(diff_x, diff_y), (diff_x, diff_y+1)]
                            matches_exist = True
                    elif right_2 == 2:
                        if down == 1:
                            highest = scores['special']
                            need_swap = [(diff_x, diff_y), (diff_x+1, diff_y)]
                            matches_exist = True
                        elif left_2 > 0:
                            highest = scores['special']
                            need_swap = [(diff_x, diff_y), (diff_x, diff_y-1)]
                            matches_exist = True
                    elif left_2 == 1 and right_2 == 1:
                        if down == 1:
                            highest = scores['special']
                            need_swap = [(diff_x, diff_y), (diff_x+1, diff_y)]
                            matches_exist = True
                if highest < scores[4]:
                    if down == 1:
                        if left_2 > 0:
                            highest = scores[4]
                            need_swap = [(diff_x, diff_y), (diff_x, diff_y-1)]
                            matches_exist = True
                        elif right_2 > 0:
                            highest = scores[4]
                            need_swap = [(diff_x, diff_y), (diff_x, diff_y+1)]
                            matches_exist = True
                if highest < scores[3]:
                    if down == 1:
                        highest = scores[3]
                        need_swap = [(diff_x, diff_y), (diff_x+1, diff_y)]
                        matches_exist = True
                    elif left_2 > 0:
                        highest = scores[3]
                        need_swap = [(diff_x, diff_y), (diff_x, diff_y-1)]
                        matches_exist = True
                    elif right_2 > 0:
                        highest = scores[3]
                        need_swap = [(diff_x, diff_y), (diff_x, diff_y+1)]
                        matches_exist = True
            if highest == scores[5]:
                break

    if not matches_exist:
        found = False
        for x in range(columns):
            for y in range(rows-2):
                if board[x][y] == board[x][y+2]:
                    if x > 0:
                        if board[x][y] == board[x-1][y+1]:
                            found = True
                            need_swap = [(x, y+1), (x-1, y+1)]
                            break
                    if x < columns-1:
                        if board[x][y] == board[x+1][y+1]:
                            found = True
                            need_swap = [(x, y+1), (x+1, y+1)]
                            break
            if found:
                break

        if not found:
            for y in range(rows):
                for x in range(columns-2):
                    if board[x][y] == board[x+2][y]:
                        if y > 0:
                            if board[x][y] == board[x+1][y-1]:
                                found = True
                                need_swap = [(x+1, y), (x+1, y-1)]
                                break
                        if y < rows-1:
                            if board[x][y] == board[x+1][y+1]:
                                found = True
                                need_swap = [(x+1, y), (x+1, y+1)]
                                break
                if found:
                    break
        matches_exist = found

    if matches_exist:
        bot_cell_1 = (need_swap[0][0], need_swap[0][1]) 
        bot_cell_2 = (need_swap[1][0], need_swap[1][1])
        board[need_swap[0][0]][need_swap[0][1]], board[need_swap[1][0]][need_swap[1][1]] = board[need_swap[1][0]][need_swap[1][1]], board[need_swap[0][0]][need_swap[0][1]]

        pending_undo = True
        should_undo = True
        swaps += 1
        total_swaps += 1
    else:
        finished = True
        clear_status = 'NO_MOVES'
        results()
    enabled = False

def results():
    global play, swaps, finished, clear_status, curr_score, total_score, total_swaps

    with open(f"tests\\{play}.csv", 'w') as file:
        file.write('game_id,points,swaps,reached_target,stopping_reason\n')
        file.write(f"{play},{curr_score},{swaps},{finished},{clear_status}")
    with open('results\\summary.csv', 'a') as file:
        file.write(f"\n{play},{curr_score},{swaps},{finished},{clear_status}")
    total_score += curr_score
    total_swaps += swaps
    play += 1
    reset()
    pass

def cycle():
    global enabled, finished, play, curr_score, board, bot_cell_1, bot_cell_2

    if not finished:
        if curr_score >= 10000:
            finished = True
            results()
            bot_cell_1 = None
            bot_cell_2 = None
        check_matches()
        check_undo()
        add_new_tiles()
        check_gaps()
        cursor_status()
        bot()


clock.schedule_interval(cycle, 0.001)
os.environ['SDL_VIDEO_CENTERED'] = '1'
pgzrun.go()