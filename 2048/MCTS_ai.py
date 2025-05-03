from utils import *
from Greedy_ai import Greedy_AI2048
import copy
import time
import random
import numpy as np

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
        """获取未尝试的移动"""
        valid_moves = []
        for direction in range(4):
            game_copy = copy.deepcopy(self.game)
            if game_copy.move(direction):
                valid_moves.append(direction)
        return valid_moves
    
    def add_child(self, move):
        """添加子节点"""
        game_copy = copy.deepcopy(self.game)
        game_copy.move(move)
        child = MCTSNode(game_copy, self, move)
        self.untried_moves.remove(move)
        self.children[move] = child
        return child
    
    def update(self, score):
        """更新节点信息"""
        self.visits += 1
        self.score += score
    
    def fully_expanded(self):
        """是否已完全扩展"""
        return len(self.untried_moves) == 0
    
    def best_child(self, exploration_weight=1.0):
        """根据UCB选择最佳子节点"""
        if not self.children:
            return None
            
        best_score = float('-inf')
        best_child = None
        
        for child in self.children.values():
            # 未访问节点优先
            if child.visits == 0:
                return child
                
            # UCB计算
            exploit = child.score / child.visits
            explore = exploration_weight * np.sqrt(2 * np.log(self.visits) / child.visits)
            ucb = exploit + explore
            
            if ucb > best_score:
                best_score = ucb
                best_child = child
                
        return best_child


class MCTS_AI2048(Greedy_AI2048):
    """MCTS实现"""
    
    def __init__(self, game=None, simulation_time=0.2):
        super().__init__(game)
        self.simulation_time = simulation_time
        self.stats = {"simulations": 0, "greedy_used": 0, "mcts_used": 0}
    
    def get_move(self):
        """结合贪婪搜索与MCTS的决策"""
        if not self.game:
            return random.randint(0, 3)
        
        # 第一步：直接使用贪婪搜索找到基准移动
        depth = 3
        greedy_move, _ = self._look_ahead(self.game, depth)
        
        if greedy_move is None:
            greedy_move = random.randint(0, 3)
        
        # 第二步：使用MCTS进行搜索
        root = MCTSNode(self.game)
        
        # 特殊情况快速处理
        if len(root.untried_moves) <= 1:
            self.stats["greedy_used"] += 1
            return greedy_move
        
        # 标准MCTS搜索
        mcts_move = self._mcts_search(root)
        
        # 第三步：评估和比较两种移动
        if mcts_move == greedy_move:
            # 两者一致，直接使用
            self.stats["greedy_used"] += 1
            return greedy_move
        
        # 两者不一致，比较质量
        greedy_game = copy.deepcopy(self.game)
        greedy_game.move(greedy_move)
        greedy_score = self._evaluate(greedy_game)
        
        mcts_game = copy.deepcopy(self.game)
        mcts_game.move(mcts_move)
        mcts_score = self._evaluate(mcts_game)
        
        # 选择评分更高的移动，保证性能不低于贪婪搜索
        if mcts_score >= greedy_score:
            self.stats["mcts_used"] += 1
            return mcts_move
        else:
            self.stats["greedy_used"] += 1
            return greedy_move
    
    def _mcts_search(self, root):
        """执行标准MCTS搜索过程"""
        start_time = time.time()
        iteration = 0
        
        while time.time() - start_time < self.simulation_time:
            # 1. 选择
            node = self._select(root)
            
            # 2. 扩展
            if node.untried_moves and not self._is_terminal(node.game):
                node = self._expand(node)
            
            # 3. 模拟
            reward = self._simulate(node)
            
            # 4. 回溯
            self._backpropagate(node, reward)
            
            iteration += 1
        
        self.stats["simulations"] += iteration
        
        # 选择访问次数最多的移动
        if not root.children:
            return random.choice(root.untried_moves) if root.untried_moves else 0
        
        best_visits = -1
        best_move = None
        
        for move, child in root.children.items():
            if child.visits > best_visits:
                best_visits = child.visits
                best_move = move
        
        return best_move
    
    def _select(self, node):
        """选择阶段 - 使用UCB下降树"""
        current = node
        
        while not self._is_terminal(current.game) and current.fully_expanded():
            child = current.best_child(exploration_weight=0.7)  # 降低探索权重，偏好利用
            if not child:
                break
            current = child
        
        return current
    
    def _expand(self, node):
        """扩展阶段 - 使用评估函数指导扩展"""
        if not node.untried_moves:
            return node
        
        # 使用评估函数选择扩展方向
        best_score = float('-inf')
        best_moves = []
        
        for move in node.untried_moves:
            game_copy = copy.deepcopy(node.game)
            if game_copy.move(move):
                score = self._evaluate(game_copy)
                
                if score > best_score:
                    best_score = score
                    best_moves = [move]
                elif score == best_score:
                    best_moves.append(move)
        
        # 从最佳移动中随机选择
        expand_move = random.choice(best_moves) if best_moves else random.choice(node.untried_moves)
        return node.add_child(expand_move)
    
    def _simulate(self, node):
        """模拟阶段 - 使用贪婪AI的评估函数指导w'w'w'wwwww"""
        game = copy.deepcopy(node.game)
        
        # 保存初始状态评估
        initial_eval = self._evaluate(game)
        
        # 快速模拟，限制步数
        depth = 5
        steps = 0
        
        while game.get_game_state() == 0 and steps < depth:
            # 获取有效移动
            valid_moves = []
            for direction in range(4):
                temp_game = copy.deepcopy(game)
                if temp_game.move(direction):
                    valid_moves.append(direction)
            
            if not valid_moves:
                break
            
            
            best_move = random.choice(valid_moves)
            best_score = float('-inf')
            
            for direction in valid_moves:
                temp_game = copy.deepcopy(game)
                temp_game.move(direction)
                score = self._evaluate(temp_game)
                
                if score > best_score:
                    best_score = score
                    best_move = direction
            
            # 执行移动
            game.move(best_move)
            
            # 添加随机方块
            empty_cells = []
            for i in range(4):
                for j in range(4):
                    if game.grid[i][j] == 0:
                        empty_cells.append((i, j))
            
            if empty_cells:
                i, j = random.choice(empty_cells)
                game.grid[i][j] = 2 if random.random() < 0.9 else 4
            
            steps += 1
        
        # 计算奖励 - 使用评估函数
        final_eval = self._evaluate(game)
        reward = final_eval - initial_eval
        
        # 特殊状态奖励调整
        if game.get_game_state() == 1:  # 胜利
            reward += 10000
        elif game.get_game_state() == 2 and steps < 3:  # 快速失败
            reward -= 1000
        
        return reward
    
    def _backpropagate(self, node, reward):
        """回溯阶段 - 更新节点统计信息"""
        current = node
        
        while current:
            current.update(reward)
            current = current.parent
    
    def _is_terminal(self, game):
        """检查游戏是否结束"""
        return game.get_game_state() != 0
    
    def get_stats(self):
        """获取统计信息"""
        return self.stats