from main import *


matches_exist = False
total_score = 0
play = 1
main_line, overlap_1, overlap_2 = False, False, False

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

#   copy current board
#   starting from (0, 0) and until (x-1, y-1)
#       for each swap direction for current tile
#           if swap already made or if both tiles are the same
#               continue
#           if swap is horizontal
#               check 2 tiles above and below of each tile
#               check from 2 tiles left of first tile to 2 tiles right of the second tile
#               set appropriate flags for said lines
#           if swap is vertical
#               check 2 tiles left and right of each tile
#               check from 2 tiles above of first tile to 2 tiles below of the second tile
#               set appropriate flags for said lines
#           check flags for special matches
#               if perpendicular and (overlap_1 or overlap_2)
#                   check for special matches
#           if found matches
#               matches_exist = True
#               clear match
#               add score for that match
#               drop new items
#               check for any new matches and add scores for them
#               until no more matches are found
#           when new items stop falling
#           mark current swap as "already checked"
#           store score of current swap
#       pick swap with the highest score
# repeat until 10k score or until no matches exist
# write results to csv