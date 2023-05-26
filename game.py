import numpy as np
import torch

GAME_COLS = 4
GAME_ROWS = 4
GAME_HEIGHT = 4
BITS_IN_LEN = 3
COUNT_TO_WIN = 4

def bits_to_int(bits):
    res = 0
    for b in bits:
        res *= 17 
        res += b
    return res

def int_to_bits(num, bits):
    res = []
    for _ in range(bits):
        res.append(num % 17)
        num //= 17
    res.append(num % 17)
    return res[::-1]

def encode_lists(field_lists):
    """
    Encode lists representation into the binary numbers
    :param field_lists: list of GAME_COLS lists with  0s, 1s and 2s
    :return: integer number with encoded game state
    """
    assert isinstance(field_lists, list)
    print(field_lists)
    bits = []
    for layer in field_lists[0]:
        for col in layer:
            bits.extend(col)
    bits.append(field_lists[1])
    return bits_to_int(bits)

INITIAL_STATE = encode_lists([[[[0 for k in range(GAME_COLS)] for j in range(GAME_COLS)] for i in range(GAME_HEIGHT)], 16])

def decode_binary(state_int):
    """
    Decode binary representation into the list view
    :param state_int: integer representing the field
    :return: list of GAME_COLS lists
    """
    assert isinstance(state_int, int)
    bits = int_to_bits(state_int, bits = GAME_COLS * GAME_ROWS * GAME_HEIGHT)
    res = []
    for layer in range(GAME_ROWS):
        tmp_res = []
        for col in range(GAME_COLS):
            vals = bits[col * GAME_ROWS + (layer * 16):(col + 1) * GAME_ROWS + (layer * 16)]
            tmp_res.append(vals)
        res.append(tmp_res)
    res = [res]
    res.append(bits[-1])
    return res

def possible_position_moves(state_int):
    """
    This function could be calculated directly from bits, but I'm too lazy
    :param state_int: field representation
    :return: the list of columns which we can make a move
    """
    assert isinstance(state_int, int)
    field = decode_binary(state_int)
    res = []
    cnt = 0
    for layer in field[0][0]:
        for num in layer:
            if num == 0:
                res.append(cnt)
            cnt += 1
            
    return res

def possible_chess_moves(state_int):
    assert isinstance(state_int, int)
    field = decode_binary(state_int)
    res = [num for num in range(16)]
    
    for x in range(GAME_COLS):
        for y in range(GAME_ROWS):
            target = ''
            for layer in field[0]:
                target += str(layer[x][y])
            if int(target) != 0:
                target = int(str(int(target) - 1111), 2)
                try:
                    res.remove(target)
                except:
                    pass
    return res

def _check_won(field_layer, col, row, chess):
    """
    Check for horisontal/diagonal win condition for the last player moved in the column
    :param field_layer: layer of field
    :param col: column index
    :param row: rolum index
    :param chess: this layer chess
    :return: True if won, False if not
    """
    if row == col:
        for x in range(GAME_COLS):
            if field_layer[x][x] != chess:
                break
            elif x == GAME_COLS - 1:
                return True
    for x in range(GAME_COLS):
        if field_layer[col][x] != chess:
            break
        elif x == GAME_COLS - 1:
            return True
    
    for x in range(GAME_COLS):
        if field_layer[x][row] != chess:
            break
        elif x == GAME_COLS - 1:
            return True
    return False


def move(state_int, action):
    """
    Perform move into given column. Assume the move could be performed, otherwise, assertion will be raised
    :param state_int: current state
    :param col: column to make a move
    :param player: player index (PLAYER_WHITE or PLAYER_BLACK
    :return: tuple of (state_new, won). Value won is bool, True if this move lead
    to victory or False otherwise (but it could be a draw)
    """
    assert isinstance(state_int, int)
    assert isinstance(action, int)
    assert 0 <= action < GAME_COLS * GAME_ROWS
    won = False
    
    field = decode_binary(state_int)

    if field[1] != 16:
        chess = str(int(format(field[1], 'b')) + 1111)
        col = int(action / 4)
        row = int(action % 4)
        
        for idx, layer in enumerate(field[0]):
            layer[col][row] = int(chess[idx])
            won = won if won else _check_won(layer, col, row, int(chess[idx]))

        # check for victory: the simplest vertical case
        field[1] = 16
    else:
        field[1] = action
    state_new = encode_lists(field)
    return state_new, won



