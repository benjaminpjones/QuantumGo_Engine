import random
from action_space import action_map_19x19, action_map_9x9, action_map_5x5
from board import Board
from board import Player
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock


counter = 1
counter_lock = Lock()

#monte carlo tree search
class MCTS:

    def __init__(self):
        pass

    def run(self):
        board = Board()
        board_driver = board.get_driver()

        board.login()
        board.create_game()

        player_black = Player('black', board_driver)
        player_black.take_seat()
        
        parent = Node(board.get_sgf_data(), action_map_19x19.copy(), None, 0, 0)

        need_to_select_player = False

        player_has_passed = False

        while True:
            """
            profiler = cProfile.Profile()
            profiler.enable()
            """
            parent.create_children(parent.get_board_state(), parent.get_action_space())
            parent.simulate_children_and_update()

            if(need_to_select_player):
                player_black.select_player(player_has_passed)

            next_move = parent.get_best_move()

            player_black.make_move(next_move)
            
            if(next_move == 362):
                break
            elif(next_move == 361):
                player_has_passed = True
        
            parent = parent.get_best_child()

            parent.get_action_space().pop(next_move)

            need_to_select_player = True

            #need to wait until player white makes move.
            time.sleep(5)

            #the move that player white makes is not available to player black.
            parent.get_action_space().pop(board.get_sgf_data()[-1])


            """
            profiler.disable()
            Takes 36.85 seconds to write to file
            with open('profile_output.txt', 'w') as f:
                ps = pstats.Stats(profiler, stream=f).sort_stats('cumulative')
                ps.print_stats()
            """
        print("Game Over")
        
            
        
class Node:

    def __init__(self, board_state, action_space, parent, games_played, games_won):

        self.board_state = board_state

        self.action_space = action_space

        self.parent = parent

        self.children = []

        self.games_played = games_played

        self.games_won = games_won

        self.next_move = None

    def get_board_state(self):
            
        return self.board_state
    
    def get_action_space(self):

        return self.action_space

    def get_parent(self):
            
        return self.parent    

    def get_child(self):
    
        return self.child

    def get_games_played(self):

        return self.games_played
    
    def get_games_won(self):

        return self.games_won
    
    def get_next_move(self):
        
        return self.next_move
    
    def set_board_state(self, board_state):

        self.board_state = board_state
    
    def set_action_space(self, action_space):
            
        self.action_space = action_space

    def set_parent(self, parent):

        self.parent = parent        

    def set_child(self, child):

        self.child = child

    def set_games_played(self, games_played):
            
        self.games_played = games_played
    
    def set_games_won(self, games_won):

        self.games_won = games_won
    
    def set_next_move(self, next_move):

        self.next_move = next_move

    def create_children(self, board_state, action_space):

        for key, value in action_space.items():

            child = Node(board_state, action_space, self, 0, 0)
            child.set_next_move(key)
            self.children.append(child)

    def simulate_children_and_update(self):
        def simulate_child(child):
            global counter
            with counter_lock:
                print(f"Simulating child {counter}")
                counter += 1

            child_result = child.simulate(child.get_board_state())
            #resimulate if error occurs
            """
            while child_result == "Error":
                child_result = child.simulate(child.get_board_state())
            """
            if child_result == 'B':
                child.set_games_won(child.get_games_won() + 1)
            child.set_games_played(child.get_games_played() + 1)

        with ThreadPoolExecutor() as executor:
            executor.map(simulate_child, self.children)

        print("Done simulating the next round of nodes")
    
    def simulate(self, previous_game_moves):

        current_game_moves = []

        temp_action_space = action_map_19x19.copy()
             
        current_game_moves = previous_game_moves

        total_moves = len(current_game_moves)

        while True:
        
            random_action = random.choice(list(temp_action_space.keys()))

            #cannot pass during quantum stone placment phase
            if total_moves <= 2 and random_action == 361:
                random_action = random.choice(list(temp_action_space.keys()))
                            
            #if player resigns end game
            if(random_action == 362):
                current_game_moves.append(random_action)
                return 'W' if len(current_game_moves) % 2 == 0 else 'B'
            
            # if both players pass end game
            elif(random_action == 361 and current_game_moves[-1]):
                current_game_moves.append(random_action)
                #here need to run simulation to see who won
                #why is get_game_result automatically called?
                #return get_game_result(current_game_moves)
            
            else:
                current_game_moves.append(random_action)
                temp_action_space.pop(random_action)

            total_moves += 1

        #dont need return statement here b/c there is no case where a player dosent resign or pass

    def get_best_child(self):

        max_ratio = 0
        best_child = None
        best_children = []

        for child in self.children:
            if child.get_games_played() == 0: # not sure why some children have 0 games played
                continue

            win_ratio = child.get_games_won() / child.get_games_played()

            if win_ratio > max_ratio:
                max_ratio = win_ratio
                best_child = child
                best_children = []
            
            #need to make sure we are not just selecting the first child if some ratios are same
            #exploration vs exploitation - use upper confidence bound instead
            elif win_ratio == max_ratio:
                best_children.append(child)

        return best_child if best_children == [] else random.choice(best_children)

    def get_best_move(self):

        best_child = self.get_best_child()
        return best_child.get_next_move()


def get_game_result(game_moves):
    new_board = Board()
    new_board_driver = new_board.get_driver()
    new_board.login()
    new_board.create_game()

    player_black = Player('black', new_board_driver)
    player_black.take_seat()
 
    player_white = Player('white', new_board_driver)
    player_white.take_seat()

    for index, move in enumerate(game_moves):
        player = player_black if index % 2 == 0 else player_white
        player.select_player()
        player.make_move(move)

    return new_board.get_game_result()