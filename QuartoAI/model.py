import numpy as np
import collections

import torch
import torch.nn as nn

import game, MCTS

OBS_SHAPE = (4, game.GAME_ROWS, game.GAME_COLS)
NUM_FILTERS = 64

class Net(nn.Module):
    def __init__(self, input_shape, actions_n):
        super(Net, self).__init__()
        self.conv_in = nn.Sequential(
            nn.Conv2d(input_shape[1], NUM_FILTERS, kernel_size = 3, padding = 1),
            nn.BatchNorm2d(NUM_FILTERS),
            nn.LeakyReLU()
        )

        # layers with residual
        self.conv_1 = nn.Sequential(
            nn.Conv2d(NUM_FILTERS, NUM_FILTERS, kernel_size = 3, padding = 1),
            nn.BatchNorm2d(NUM_FILTERS),
            nn.LeakyReLU()
        )
        
        body_out_shape = (NUM_FILTERS, ) + input_shape[2:]
        
        # value head
        self.conv_val = nn.Sequential(
            nn.Conv2d(NUM_FILTERS, 1, kernel_size = 1),
            nn.BatchNorm2d(1),
            nn.LeakyReLU()
        )
        conv_val_size = self._get_conv_val_size(body_out_shape) + 1
        self.value = nn.Sequential(
            nn.Linear(conv_val_size, 20),
            nn.LeakyReLU(),
            nn.Linear(20, 1),
        )

        # policy head
        self.conv_policy = nn.Sequential(
            nn.Conv2d(NUM_FILTERS, 2, kernel_size=1),
            nn.BatchNorm2d(2),
            nn.LeakyReLU()
        )
        conv_policy_size = self._get_conv_policy_size(body_out_shape) + 1
        self.policy = nn.Sequential(
            nn.Linear(conv_policy_size, actions_n),
            nn.Softmax()
        )

    def _get_conv_val_size(self, shape):
        o = self.conv_val(torch.zeros(1, *shape))
        return int(np.prod(o.size()))

    def _get_conv_policy_size(self, shape):
        o = self.conv_policy(torch.zeros(1, *shape))
        return int(np.prod(o.size()))

    def forward(self, x, y):
        
        batch_size = x.size()[0]
        # y = y.unsqueeze(-1)
        
        v = self.conv_in(x)
        v = v + self.conv_1(v)
        
        val = self.conv_val(v)
        val = torch.cat((val.view(batch_size, -1), y), 1)
        val = self.value(val)
        
        pol = self.conv_policy(v)
        pol = torch.cat((pol.view(batch_size, -1), y), 1)
        pol = self.policy(pol)
        
        return pol, val

def _encode_list_state(dest_np, dest_np_2, state_list):
    """
    In-place encodes list state into the zero numpy array
    :param dest_np: dest array, expected to be zero
    :param state_list: state of the game in the list form
    :param who_move: player index (game.PLAYER_WHITE or game.PLAYER_BLACK) who to move
    """
    assert dest_np.shape == OBS_SHAPE
    for layer_idx, layer in enumerate(state_list[0]):
        for col_idx, col in enumerate(layer):
            for rev_row_idx, cell in enumerate(col):
                row_idx = game.GAME_ROWS - rev_row_idx - 1
                dest_np[layer_idx, row_idx, col_idx] = cell
    dest_np_2[0] = state_list[1]

def state_lists_to_batch(state_lists, device="mps"):
    """
    Convert list of list states to batch for network
    :param state_lists: list of 'list states'
    :param who_moves_lists: list of player index who moves
    :return Variable with observations
    """
    assert isinstance(state_lists, list)
    
    batch_size = len(state_lists)
    batch = np.zeros((batch_size,) + OBS_SHAPE, dtype=np.float32)
    batch_2 = np.zeros((batch_size, 1), dtype=np.float32)
    for idx, state in enumerate(state_lists):
        _encode_list_state(batch[idx], batch_2[idx], state)
    return torch.tensor(batch).to(device), torch.tensor(batch_2).to(device)

def play_game(mcts_stores, replay_buffer, net1, net2, steps_before_tau_0, mcts_searches, mcts_batch_size,
              net1_plays_first=None, device="mps"):
    """
    Play one single game, memorizing transitions into the replay buffer
    :param mcts_stores: could be None or single MCTS or two MCTSes for individual net
    :param replay_buffer: queue with (state, probs, values), if None, nothing is stored
    :param net1: player1
    :param net2: player2
    :return: value for the game in respect to player1 (+1 if p1 won, -1 if lost, 0 if draw)
    """
    assert isinstance(replay_buffer, (collections.deque, type(None)))
    assert isinstance(mcts_stores, (MCTS.MCTS, type(None), list))
    assert isinstance(net1, Net)
    assert isinstance(net2, Net)
    assert isinstance(steps_before_tau_0, int) and steps_before_tau_0 >= 0
    assert isinstance(mcts_searches, int) and mcts_searches > 0
    assert isinstance(mcts_batch_size, int) and mcts_batch_size > 0
    
    if mcts_stores is None:
        mcts_stores = [MCTS.MCTS(), MCTS.MCTS()]
    elif isinstance(mcts_stores, MCTS.MCTS):
        mcts_stores = [mcts_stores, mcts_stores]
        
    state = game.INITIAL_STATE
    
    nets = [net1, net2]
    if net1_plays_first is None:
        cur_player = np.random.choice(2)
        nets = nets if cur_player else [net2, net1]
    else:
        cur_player = 0 if net1_plays_first else 1
    step = 0
    tau = 1 if steps_before_tau_0 > 0 else 0
    game_history = []
    
    result = None
    
    cur_player = 0
    while result is None:
        # choose chess
        mcts_stores[cur_player].search_batch(mcts_searches, mcts_batch_size, state,
                                             0, nets[cur_player], device = device)
        probs, _ = mcts_stores[cur_player].get_policy_value(state, tau=tau)
        game_history.append((state, cur_player, probs))
        action = np.random.choice(game.GAME_COLS * game.GAME_ROWS, p=probs)
        if action not in game.possible_chess_moves(state):
            print("Impossible action selected")
        state, won = game.move(state, action)
        
        # choose position
        mcts_stores[1 - cur_player].search_batch(mcts_searches, mcts_batch_size, state,
                                             1, nets[1 - cur_player], device = device)
        probs, _ = mcts_stores[1 - cur_player].get_policy_value(state, tau=tau)
        game_history.append((state, 1 - cur_player, probs))
        action = np.random.choice(game.GAME_COLS * game.GAME_ROWS, p=probs)
        if action not in game.possible_position_moves(state):
            print("Impossible action selected")
        state, won = game.move(state, action)
        
        if won:
            result = 1
            net1_result = 1 if nets[1 - cur_player] == net1 else -1
            break
        cur_player = 1-cur_player
        
        if len(game.possible_position_moves(state)) == 0:
            result = 0
            net1_result = 0
            break
        
        step += 1
        if step >= steps_before_tau_0:
            tau = 0

    if replay_buffer is not None:
        for idx, (state, cur_player, probs) in enumerate(reversed(game_history)):
            replay_buffer.append((state, cur_player, probs, result))
            result = result if idx % 2 else -result

    return net1_result, step