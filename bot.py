from main import *

# patterns for bot to match (any orientation):
# region
#     3 combo:
#           - X X
#         or
#           X - X
#         or
#           X X -
#     4 combo:
#           X - X X
#         or
#           X X - X
#     5 combo:
#           X X - X X
#     L combo:
#           - X X
#           X
#           X
#         or
#           X X -
#               X
#               X
#         or
#           X
#           X
#           - X X
#         or
#               X
#               X
#           X X -
#     T combo:
#           X - X
#             X
#             X
#         or
#             X
#             X
#           X - X
#         or
#           X
#           - X X
#           X
#         or
#               X
#           X X -
#               X
# endregion