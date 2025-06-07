import time
import random
import numpy as np
from utils import *
from Greedy_ai import Greedy_AI2048


class MCTSNode:
    def __init__(self, game, parent=None, move=None):
        self.game = game
        self.parent = parent
        self.move = move
        self.children = {}
        self.visits = 0
        self.score = 0
        self.untried_moves = self._get_untried_moves()
    
    def _get_untried_moves(self):
        valid_moves = []
        for direction in range(4):
            game_copy = fast_copy_game(self.game)
            if game_copy.move(direction):
                valid_moves.append(direction)
        return valid_moves
    
    def add_child(self, move):
        game_copy = fast_copy_game(self.game)
        game_copy.move(move)
        child = MCTSNode(game_copy, self, move)
        self.untried_moves.remove(move)
        self.children[move] = child
        return child
    
    def update(self, score):
        self.visits += 1
        self.score += score
    
    def fully_expanded(self):
        return len(self.untried_moves) == 0
    
    def best_child(self, exploration_weight=1.4):
        if not self.children:
            return None
            
        best_score = float('-inf')
        best_child = None
        
        for child in self.children.values():
            if child.visits == 0:
                return child
                
            exploit = child.score / child.visits
            explore = exploration_weight * np.sqrt(2 * np.log(self.visits) / child.visits)
            ucb = exploit + explore
            
            if ucb > best_score:
                best_score = ucb
                best_child = child
                
        return best_child


class MCTS_AI2048(Greedy_AI2048):
    def __init__(self, game=None, simulation_time=3.0):
        super().__init__(game)
        self.simulation_time = simulation_time
        self.stats = {"simulations": 0, "greedy_used": 0, "mcts_used": 0}
        self.prev_root = None  # 存储前一步的搜索树
        self.prev_move = None  # 记录上一步选择的移动
        self.tree_reuse_count = 0  # 统计树复用次数
    

    def _can_move_in_direction(self, grid, direction):
        """检查指定方向是否可移动"""
        if direction == 0:  # 上
            for j in range(4):
                for i in range(1, 4):
                    if grid[i][j] != 0 and (grid[i-1][j] == 0 or grid[i-1][j] == grid[i][j]):
                        return True
        elif direction == 1:  # 右
            for i in range(4):
                for j in range(3):
                    if grid[i][j] != 0 and (grid[i][j+1] == 0 or grid[i][j+1] == grid[i][j]):
                        return True
        elif direction == 2:  # 下
            for j in range(4):
                for i in range(3):
                    if grid[i][j] != 0 and (grid[i+1][j] == 0 or grid[i+1][j] == grid[i][j]):
                        return True
        elif direction == 3:  # 左
            for i in range(4):
                for j in range(1, 4):
                    if grid[i][j] != 0 and (grid[i][j-1] == 0 or grid[i][j-1] == grid[i][j]):
                        return True
        return False
    

    def _get_valid_moves(self, game):
        """获取所有有效移动方向"""
        valid_moves = []
        grid = game.grid
        
        for direction in range(4):
            if self._can_move_in_direction(grid, direction):
                game_copy = fast_copy_game(game)
                if game_copy.move(direction):
                    valid_moves.append(direction)
        
        return valid_moves
    

    def _get_game_state_stats(self, game):
        """获取游戏状态的统计信息"""
        return {
            'score': game.get_score(),
            'max_tile': max(max(row) for row in game.get_grid()),
            'empty_count': sum(row.count(0) for row in game.get_grid()),
            'eval': self._evaluate(game)
        }
    

    def _is_same_state(self, game1, game2):
        """检查两个游戏状态是否相似"""
        score1, score2 = game1.get_score(), game2.get_score()
        if abs(score1 - score2) > max(score1, score2) * 0.05:
            return False

        grid1 = game1.get_grid()
        grid2 = game2.get_grid()
        
        # 主要方块匹配策略
        match_count = 0
        important_count = 0
        max_value = max(max(row) for row in grid1)
        
        # 动态确定重要方块的阈值 - 值越大的方块越重要
        threshold = max(8, max_value // 16)
        
        for i in range(4):
            for j in range(4):
                # 完全匹配大方块
                if grid1[i][j] >= threshold:
                    important_count += 1
                    if grid1[i][j] == grid2[i][j]:
                        match_count += 1
                    else:
                        # 大方块不匹配直接返回False
                        return False
                # 中等方块允许少量不匹配
                elif grid1[i][j] >= threshold // 2:
                    if grid1[i][j] != grid2[i][j]:
                        # 允许最多2个中等方块不匹配
                        if important_count >= 2:
                            return False
                        important_count += 1
        
        # 检查空格数量是否接近
        empty1 = sum(row.count(0) for row in grid1)
        empty2 = sum(row.count(0) for row in grid2)
        
        # 空格数相差不超过1格
        if abs(empty1 - empty2) > 1:
            return False
        
        if important_count == 0:
            match_cells = sum(grid1[i][j] == grid2[i][j] for i in range(4) for j in range(4))
            return match_cells >= 13
        
        return True


    def get_move(self):
        if not self.game:
            return random.randint(0, 3)
        
        # 贪婪搜索基准
        depth = 3
        greedy_move, _ = self._look_ahead(self.game, depth)
        
        if greedy_move is None:
            for direction in range(4):
                game_copy = fast_copy_game(self.game)
                if game_copy.move(direction):
                    greedy_move = direction
                    break
            
            if greedy_move is None:
                greedy_move = random.randint(0, 3)
        
        # MCTS搜索
        root = None
        if self.prev_root and self.prev_move is not None:
            # 查找前一步选择的移动对应的子节点
            if self.prev_move in self.prev_root.children:
                child_node = self.prev_root.children[self.prev_move]
                if child_node and self._is_same_state(child_node.game, self.game):
                    root = child_node
                    root.parent = None  # 断开与旧树的连接
                    self.tree_reuse_count += 1
                    self.stats["tree_reuse"] = self.tree_reuse_count
        if root is None:
            root = MCTSNode(self.game)

        if len(root.untried_moves) <= 1:
            self.stats["greedy_used"] += 1
            return greedy_move
        
        mcts_move = self._mcts_search(root)

        # 保存当前的搜索树和选择的移动，供下一步使用
        self.prev_root = root
        self.prev_move = mcts_move
        
        # 比较两种移动
        greedy_game = fast_copy_game(self.game)
        greedy_game.move(greedy_move)
        greedy_score = self._evaluate(greedy_game)
        
        mcts_game = fast_copy_game(self.game)
        mcts_game.move(mcts_move)
        mcts_score = self._evaluate(mcts_game)
        
        # 动态阈值：基于最大方块和空格数
        max_tile = max(max(row) for row in self.game.get_grid())
        empty_count = sum(row.count(0) for row in self.game.get_grid())
        
        threshold = 0.6 if max_tile >= 1024 else 0.7 if max_tile >= 256 else 0.8

        if empty_count < 4:
            threshold += 0.05
        if self.stats["simulations"] > 600:
            threshold -= 0.05

        # 决策逻辑
        if mcts_score >= greedy_score * threshold:
            self.stats["mcts_used"] += 1
            return mcts_move
        else:
            self.stats["greedy_used"] += 1
            return greedy_move
    

    def _mcts_search(self, root):
        start_time = time.time()
        iteration = 0
        max_iterations = 1000
        
        while time.time() - start_time < self.simulation_time and iteration < max_iterations:
            node = self._select(root)
            
            if node.untried_moves and not self._is_terminal(node.game):
                node = self._expand(node)
            
            reward = self._simulate(node)
            
            self._backpropagate(node, reward)
            
            iteration += 1
        
        self.stats["simulations"] += iteration
        
        if not root.children:
            return random.choice(root.untried_moves) if root.untried_moves else 0
        
        best_move = None
        max_visits = -1
        
        # 使用访问次数而非UCB值来决定根节点的最佳移动
        for move, child in root.children.items():
            if child.visits > max_visits:
                max_visits = child.visits
                best_move = move
        
        return best_move
    

    def _select(self, node):
        current = node
        
        # 动态调整UCB探索权重
        max_tile = max(max(row) for row in current.game.get_grid())
        if max_tile >= 512:
            exploration_weight = 1.1  # 高分局面更注重利用
        elif max_tile >= 256:
            exploration_weight = 1.3
        else:
            exploration_weight = 1.5  # 早期更多探索
            
        while not self._is_terminal(current.game) and current.fully_expanded():
            child = current.best_child(exploration_weight=exploration_weight)
            if not child:
                break
            current = child
        
        return current
    

    def _expand(self, node):
        if not node.untried_moves:
            return node
        
        best_score = float('-inf')
        best_moves = []
        
        for move in node.untried_moves:
            game_copy = fast_copy_game(node.game)
            if game_copy.move(move):
                score = self._evaluate(game_copy)
                
                if score > best_score:
                    best_score = score
                    best_moves = [move]
                elif score == best_score:
                    best_moves.append(move)
        
        expand_move = random.choice(best_moves) if best_moves else random.choice(node.untried_moves)
        return node.add_child(expand_move)
    

    def _simulate(self, node):
        game = fast_copy_game(node.game)
        
        initial_state = self._get_game_state_stats(game)
        
        # 动态调整模拟深度
        max_tile = initial_state['max_tile']
        if max_tile >= 512:
            depth = 16
            random_factor = 0.03
        elif max_tile >= 128:
            depth = 12
            random_factor = 0.06
        else:
            depth = 8
            random_factor = 0.12
        
        steps = 0
        
        while game.get_game_state() == 0 and steps < depth:
            valid_moves = self._get_valid_moves(game)
            
            if not valid_moves:
                break
            
            best_move = random.choice(valid_moves) if random.random() < random_factor else self._evaluate_moves(game, valid_moves)
            
            game.move(best_move)
            
            # 添加随机方块
            empty_cells = [(i, j) for i in range(4) for j in range(4) if game.grid[i][j] == 0]
            if empty_cells:
                i, j = random.choice(empty_cells)
                game.grid[i][j] = 2 if random.random() < 0.9 else 4
            
            steps += 1
            
            # 提前终止检查 - 如果评估严重下降，提前结束模拟
            if steps >= 4 and self._evaluate(game) < initial_state['eval'] * 0.75: break
        
        final_state = self._get_game_state_stats(game)
        
        # 计算复合奖励
        score_gain = (final_state['score'] - initial_state['score']) / 1000
        tile_gain = np.log2(final_state['max_tile'] / max(1, initial_state['max_tile']))
        empty_diff = final_state['empty_count'] - initial_state['empty_count']
        eval_diff = final_state['eval'] - initial_state['eval']
        
        reward = (0.5 * eval_diff + 0.25 * score_gain + 0.15 * tile_gain + 0.1 * empty_diff)
        
        # 游戏状态奖励
        if game.get_game_state() == 1:
            reward *= 10
        elif game.get_game_state() == 2:
            reward /= 10
        
        return reward
    

    def _evaluate_moves(self, game, valid_moves):
        """评估多个移动并选择最佳的"""
        best_score = float('-inf')
        best_move = random.choice(valid_moves)
        
        for move in valid_moves:
            game_copy = fast_copy_game(game)
            game_copy.move(move)
            score = self._evaluate(game_copy)
            
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move
    

    def _backpropagate(self, node, reward):
        current = node
        
        while current:
            current.update(reward)
            current = current.parent


    def _is_terminal(self, game):
        return game.get_game_state() != 0
    

    def get_stats(self):
        return self.stats