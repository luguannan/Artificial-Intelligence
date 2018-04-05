# reversi.py

import copy

valueboard = [(99, -8, 8, 6, 6, 8, -8, 99),
              (-8, -24, -4, -3, -3, -4, -24, -8),
              (8, -4, 7, 4, 4, 7, -4, 8),
              (6, -3, 4, 0, 0, 4, -3, 6),
              (6, -3, 4, 0, 0, 4, -3, 6),
              (8, -4, 7, 4, 4, 7, -4, 8),
              (-8, -24, -4, -3, -3, -4, -24, -8),
              (99, -8, 8, 6, 6, 8, -8, 99),
              ]
letter = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
direction = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

depth = -1
best_move = None
output_result = []


def read_board_from_file():
    with open('input.txt', 'rb') as infile:
        board = []
        turn = infile.readline()[0]
        if turn == 'X':
            turnValue = 1
        else:
            turnValue = 0
        depth = int(infile.readline())
        line = infile.readline().strip('\n').strip('\r')
        # print line
        while line:
            board.append(list(line))
            line = infile.readline().strip('\n').strip('\r')

    return [board, turnValue, depth]


def cal_value(board):
    result = 0
    for i in range(8):
        for j in range(8):
            if board[i][j] == 'X':
                result += valueboard[i][j]
            elif board[i][j] == 'O':
                result -= valueboard[i][j]

    return result


def cal_avail_move(board, turnvalue):
    result = [];
    turn = ''
    turnop = ''
    if turnvalue == 1:
        turn = 'X'
        turnop = 'O'
    elif turnvalue == 0:
        turn = 'O'
        turnop = 'X'
        # else:
        # print 'turnValue error'

    for i in range(8):
        for j in range(8):
            if board[i][j] == turn:
                for k in range(8):
                    tmp = 0
                    nx = i + direction[k][0]
                    ny = j + direction[k][1]
                    while 0 <= nx < 8 and 0 <= ny < 8 and board[nx][ny] == turnop:
                        nx += direction[k][0]
                        ny += direction[k][1]
                        tmp += 1
                    if 0 <= nx < 8 and 0 <= ny < 8 and board[nx][ny] == '*' and tmp > 0:
                        result.append((nx, ny))

    return sorted(set(result))


def board_move(board, move, turnvalue):
    if turnvalue == 1:
        turn = 'X'
        turnop = 'O'
    elif turnvalue == 0:
        turn = 'O'
        turnop = 'X'

    x = move[0]
    y = move[1]

    if x < 0 and y < 0:
        return board

    turnlist = [(x, y)]

    for k in range(8):
        tmp = 0
        nx = x + direction[k][0]
        ny = y + direction[k][1]
        while 0 <= nx < 8 and 0 <= ny < 8 and board[nx][ny] == turnop:
            nx += direction[k][0]
            ny += direction[k][1]
            tmp += 1
            if 0 <= nx < 8 and 0 <= ny < 8 and board[nx][ny] == turn and tmp > 0:
                nx -= direction[k][0]
                ny -= direction[k][1]
                while 0 <= nx < 8 and 0 <= ny < 8 and board[nx][ny] == turnop:
                    turnlist.append((nx, ny))
                    nx -= direction[k][0]
                    ny -= direction[k][1]

        for (x, y) in turnlist:
            board[x][y] = turn

    return board


def reverse_turn(turnvalue):
    if turnvalue == 1:
        return 0
    elif turnvalue == 0:
        return 1


def cutoff(currentdepth):
    if currentdepth >= depth >= 0:
        return 1
    else:
        return 0


def node_name(move, depth):
    if depth == 0:
        return 'root'
    elif move[0] == move[1] == -1:
        return 'pass'
    else:
        return letter[move[1]] + str(move[0] + 1)


def value_str(value):
    if value == 100000:
        return 'Infinity'
    elif value == -100000:
        return '-Infinity'
    else:
        return str(value)


def alpha_beta_search(board, turnvalue, depth):

    def max_value(board, move, turnvalue, alpha, beta, depth):
        board_move(board, move, reverse_turn(turnvalue))
        if cutoff(depth) != 0:

            v = cal_value(board)
            output_result.append(
                node_name((move[0], move[1]), depth) + ',' + str(depth) + ',' + value_str(v) + ',' + value_str(
                    alpha) + ',' + value_str(beta))
            return v
        v = -100000
        output_result.append(
            node_name((move[0], move[1]), depth) + ',' + str(depth) + ',' + value_str(v) + ',' + value_str(
                alpha) + ',' + value_str(beta))
        # board = board_move(board, move, reverse_turn(turnvalue))
        moves = cal_avail_move(board, turnvalue)
        if len(moves) == 0:
            if move[0] == move[1] == -1:
                v = cal_value(board)
                output_result.append(
                    node_name((move[0], move[1]), depth) + ',' + str(depth + 1) + ',' + value_str(v) + ',' + value_str(
                        alpha) + ',' + value_str(beta))
                if v >= beta:
                    output_result.append(
                        node_name((move[0], move[1]), depth) + ',' + str(depth) + ',' + value_str(v) + ',' + value_str(
                            alpha) + ',' + value_str(beta))
                    return v
                if depth == 0 and alpha < v:
                    global best_move
                    best_move = (x, y)
                alpha = max(alpha, v)
                output_result.append(
                    node_name((move[0], move[1]), depth) + ',' + str(depth) + ',' + value_str(v) + ',' + value_str(
                        alpha) + ',' + value_str(beta))
                return v
            else:
                moves.append((-1, -1))
        for (x, y) in moves:
            # print node_name((x, y), depth + 1) + ',' + str(depth + 1) + value_str(v) + ',' + value_str(
            #    alpha) + ',' + value_str(beta)
            board_new = copy.deepcopy(board)
            v = max(v, min_value(board_new, (x, y), reverse_turn(turnvalue), alpha, beta, depth + 1))
            if v >= beta:
                output_result.append(
                    node_name((move[0], move[1]), depth) + ',' + str(depth) + ',' + value_str(v) + ',' + value_str(
                        alpha) + ',' + value_str(beta))
                return v
            if depth == 0 and alpha < v:
                best_move = (x, y)
            alpha = max(alpha, v)
            output_result.append(
                node_name((move[0], move[1]), depth) + ',' + str(depth) + ',' + value_str(v) + ',' + value_str(
                    alpha) + ',' + value_str(beta))
        return v

    def min_value(board, move, turnvalue, alpha, beta, depth):
        board_move(board, move, reverse_turn(turnvalue))
        if cutoff(depth) != 0:
            v = cal_value(board)
            output_result.append(
                node_name((move[0], move[1]), depth) + ',' + str(depth) + ',' + value_str(v) + ',' + value_str(
                    alpha) + ',' + value_str(beta))
            return v
        v = 100000
        output_result.append(
            node_name((move[0], move[1]), depth) + ',' + str(depth) + ',' + value_str(v) + ',' + value_str(
                alpha) + ',' + value_str(beta))
        moves = cal_avail_move(board, turnvalue)
        if len(moves) == 0:
            if move[0] == move[1] == -1:
                v = cal_value(board)
                output_result.append(
                    node_name((move[0], move[1]), depth) + ',' + str(depth + 1) + ',' + value_str(v) + ',' + value_str(
                        alpha) + ',' + value_str(beta))
                if v <= alpha:
                    output_result.append(
                        node_name((move[0], move[1]), depth) + ',' + str(depth) + ',' + value_str(v) + ',' + value_str(
                            alpha) + ',' + value_str(beta))
                    return v
                beta = max(alpha, v)
                output_result.append(
                    node_name((move[0], move[1]), depth) + ',' + str(depth) + ',' + value_str(v) + ',' + value_str(
                        alpha) + ',' + value_str(beta))
                return v
            else:
                moves.append((-1, -1))
        for (x, y) in moves:
            # print node_name((x, y), depth + 1) + ',' + str(depth + 1) + value_str(v) + ',' + value_str(
            #     alpha) + ',' + value_str(beta)
            board_new = copy.deepcopy(board)
            v = min(v, max_value(board_new, (x, y), reverse_turn(turnvalue), alpha, beta, depth + 1))
            if v <= alpha:
                output_result.append(
                    node_name((move[0], move[1]), depth) + ',' + str(depth) + ',' + value_str(v) + ',' + value_str(
                        alpha) + ',' + value_str(beta))
                return v
            beta = max(alpha, v)
            output_result.append(
                node_name((move[0], move[1]), depth) + ',' + str(depth) + ',' + value_str(v) + ',' + value_str(
                    alpha) + ',' + value_str(beta))
        return v
    output_result.append('Node,Depth,Value,Alpha,Beta')
    v = max_value(board, (-2, -2), turnvalue, -100000, 100000, 0)
    return best_move


def main():
    game = read_board_from_file()
    global depth
    depth = game[2]
    alpha_beta_search(game[0], game[1], 0)
    global best_move
    if best_move is not None:
        result_board = board_move(game[0], best_move, game[1])
    else:
        result_board = game[0]

    with open('output.txt', 'wb') as outfile:

        for i in range(8):
            outfile.write(''.join(result_board[i]))
            outfile.write('\n')

        outfile.write('\n'.join(output_result))

main()
