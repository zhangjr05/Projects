import numpy as np
import copy
import pickle
import random
import os
import time
from tqdm import tqdm
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from Greedy_ai import Greedy_AI2048
from utils import *

class ML_Enhanced_AI2048(Greedy_AI2048):
    """结合机器学习方法和贪婪策略的2048 AI"""
    def __init__(self, game=None, model_path=None):
        """初始化ML增强AI实例，加载模型和设置统计信息。"""
        super().__init__(game)
        self.model = None
        self.scaler = None
        self.model_path = model_path if model_path else get_path("models/2048_model.pkl")
        self.load_or_create_model()
        
        self.stats = {
            "predictions": 0,
            "high_probability_paths": 0,
            "low_probability_paths": 0,
            "ml_decisions": 0,
            "greedy_decisions": 0
        }
        
        self.decision_cache = {}
        
    def load_or_create_model(self):
        """加载现有模型或创建新的随机森林模型"""
        try:
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
                self.model = model_data['model']
                self.scaler = model_data['scaler']
            print("成功加载2048概率预测模型")
        except (FileNotFoundError, EOFError):
            print("未找到模型文件，创建新的随机森林模型")
            self.model = RandomForestClassifier(
                n_estimators=150,        
                max_depth=15,            
                min_samples_split=10,    
                min_samples_leaf=4,      
                max_features='sqrt',     
                bootstrap=True,          
                random_state=42
            )
            self.scaler = StandardScaler()
    
    def save_model(self):
        """保存训练好的模型到指定路径"""
        model_dir = os.path.dirname(self.model_path)
        os.makedirs(model_dir, exist_ok=True)
        
        with open(self.model_path, 'wb') as f:
            pickle.dump({'model': self.model, 'scaler': self.scaler}, f)
        print(f"模型已保存至 {self.model_path}")
    
    def extract_features(self, game):
        """从当前游戏状态提取特征，用于模型预测"""
        grid = game.get_grid()
        flat_grid = [cell for row in grid for cell in row]
        
        # 基础评估特征
        greedy_eval = self._evaluate(game)
        
        # 基本特征
        max_tile = max(flat_grid)
        empty_count = flat_grid.count(0)
        score = game.get_score()
        
        # 合并潜力特征
        merge_potential = 0
        for i in range(4):
            for j in range(3):
                if grid[i][j] != 0 and grid[i][j] == grid[i][j+1]:
                    merge_potential += 1
        for j in range(4):
            for i in range(3):
                if grid[i][j] != 0 and grid[i][j] == grid[i+1][j]:
                    merge_potential += 1
        
        # 最大方块位置特征
        max_in_corner = 0
        if max_tile > 0:
            corners = [(0,0), (0,3), (3,0), (3,3)]
            for i, j in corners:
                if grid[i][j] == max_tile:
                    max_in_corner = 1
                    break
        
        # 单调性特征 (值沿某个方向递减)
        monotonicity = 0
        
        # 检查水平单调性 (左到右)
        for i in range(4):
            for j in range(3):
                if grid[i][j] > 0 and grid[i][j+1] > 0:
                    if grid[i][j] >= grid[i][j+1]:
                        monotonicity += 1
        
        # 检查垂直单调性 (上到下)
        for j in range(4):
            for i in range(3):
                if grid[i][j] > 0 and grid[i+1][j] > 0:
                    if grid[i][j] >= grid[i+1][j]:
                        monotonicity += 1
        
        # 平滑度特征 (相邻方块的值差异)
        smoothness = 0
        for i in range(4):
            for j in range(4):
                if grid[i][j] > 0:
                    # 计算与相邻方块的值差异
                    neighbors = []
                    if j > 0 and grid[i][j-1] > 0:
                        neighbors.append(abs(np.log2(grid[i][j]) - np.log2(grid[i][j-1])))
                    if j < 3 and grid[i][j+1] > 0:
                        neighbors.append(abs(np.log2(grid[i][j]) - np.log2(grid[i][j+1])))
                    if i > 0 and grid[i-1][j] > 0:
                        neighbors.append(abs(np.log2(grid[i][j]) - np.log2(grid[i-1][j])))
                    if i < 3 and grid[i+1][j] > 0:
                        neighbors.append(abs(np.log2(grid[i][j]) - np.log2(grid[i+1][j])))
                    
                    if neighbors:
                        smoothness += sum(neighbors) / len(neighbors)
        
        # 蛇形路径特征
        snake_pattern = 0
        
        # 检查蛇形路径模式 (按照Z字形排列大数)
        expected_pattern = [
            [(0,0), (0,1), (0,2), (0,3)], 
            [(1,3), (1,2), (1,1), (1,0)],
            [(2,0), (2,1), (2,2), (2,3)],
            [(3,3), (3,2), (3,1), (3,0)]
        ]
        
        # 扁平化为一维序列
        flat_pattern = [cell for row in expected_pattern for cell in row]
        
        # 获取非零方块及其坐标
        non_zero_cells = []
        for i in range(4):
            for j in range(4):
                if grid[i][j] > 0:
                    non_zero_cells.append(((i, j), grid[i][j]))
        
        # 按值排序，最大的在前
        non_zero_cells.sort(key=lambda x: x[1], reverse=True)
        
        # 检查前8个最大方块是否按蛇形模式排列
        for i, ((r, c), _) in enumerate(non_zero_cells[:min(8, len(non_zero_cells))]):
            if (r, c) == flat_pattern[i]:
                snake_pattern += 1
        
        # 合并特征向量
        features = [
            greedy_eval,           # 贪婪评估得分
            max_tile,              # 最大方块值 
            empty_count,           # 空格数量
            score / 10000,         # 归一化分数
            merge_potential,       # 合并潜力
            max_in_corner,         # 最大块是否在角落
            monotonicity / 24.0,   # 单调性 (归一化)
            5.0 - min(5.0, smoothness),  # 平滑度 (反向，越平滑越好)
            snake_pattern / 8.0,   # 蛇形模式得分 (归一化)
            sum(1 for x in flat_grid if x >= 128) / 16.0,
            sum(1 for x in flat_grid if x >= 256) / 16.0,
            sum(1 for x in flat_grid if x >= 512) / 16.0,
            sum(1 for x in flat_grid if x >= 1024) / 16.0
        ]
        
        return np.array(features).reshape(1, -1)
    
    def predict_probability(self, game):
        """预测当前状态下达到2048的概率"""
        grid_tuple = tuple(tuple(row) for row in game.get_grid())
        if grid_tuple in self.decision_cache and not isinstance(self.decision_cache[grid_tuple], tuple):
            return self.decision_cache[grid_tuple]
        
        grid = game.get_grid()
        max_tile = max(max(row) for row in grid)
        if max_tile >= 1024:
            probability = 0.95
            self.decision_cache[grid_tuple] = probability
            return probability
        
        features = self.extract_features(game)
        
        if not hasattr(self.model, 'classes_'):
            probability = self._heuristic_probability(game)
            self.decision_cache[grid_tuple] = probability
            return probability
        
        try:
            self.stats["predictions"] += 1
            
            if self.scaler is not None:
                try:
                    features = self.scaler.transform(features)
                except:
                    return self._heuristic_probability(game)
            
            if len(self.model.classes_) > 1:
                proba = self.model.predict_proba(features)[0][1]
                
                # 混合启发式规则和ML预测
                heuristic_prob = self._heuristic_probability(game)
                
                # 信任度加权 - 以最大方块值作为模型可信度指标
                if max_tile >= 512:
                    trust_ml = 0.8  # 高度信任ML
                elif max_tile >= 256:
                    trust_ml = 0.7  # 较信任ML
                else:
                    trust_ml = 0.5  # 平等混合
                    
                final_proba = trust_ml * proba + (1 - trust_ml) * heuristic_prob
                self.decision_cache[grid_tuple] = float(final_proba)
                return float(final_proba)
            else:
                proba = self._heuristic_probability(game)
                self.decision_cache[grid_tuple] = proba
                return proba
        except:
            probability = self._heuristic_probability(game)
            self.decision_cache[grid_tuple] = probability
            return probability
    
    def _heuristic_probability(self, game):
        """基于启发式规则计算达到2048的概率"""
        grid = game.get_grid()
        max_tile = max(max(row) for row in grid)
        empty_count = sum(row.count(0) for row in grid)
        
        if max_tile >= 1024:
            base_probability = 0.95
        elif max_tile >= 512:
            base_probability = 0.7
        elif max_tile >= 256:
            base_probability = 0.4
        elif max_tile >= 128:
            base_probability = 0.2
        else:
            base_probability = 0.1
        
        eval_score = self._evaluate(game)
        normalized_eval = min(1.0, max(0.0, eval_score / 100.0))
        
        final_probability = 0.7 * base_probability + 0.3 * normalized_eval
        
        if empty_count <= 2:
            final_probability *= 0.7
        
        return max(0.0, min(1.0, final_probability))
    
    def get_move(self):
        """根据ML增强策略和贪婪策略选择下一步移动"""
        if not self.game:
            return None

        grid = self.game.get_grid()
        max_tile = max(max(row) for row in grid)
        grid_tuple = tuple(tuple(row) for row in grid)
        if grid_tuple in self.decision_cache and isinstance(self.decision_cache[grid_tuple], tuple):
            return self.decision_cache[grid_tuple][0]

        greedy_move = super().get_move()
        base_probability = self.predict_probability(self.game)

        if max_tile >= 1024:
            depth = 1
        elif max_tile >= 512:
            depth = 2
        elif base_probability > 0.7:
            depth = 3
            self.stats["high_probability_paths"] += 1
        elif base_probability < 0.3:
            depth = 2
            self.stats["low_probability_paths"] += 1
        else:
            depth = 3

        if max_tile >= 512:
            best_move = greedy_move
            self.stats["greedy_decisions"] += 1
        else:
            ml_move, ml_score = self._ml_enhanced_look_ahead(self.game, depth, base_probability)
            if ml_move is None:
                best_move = greedy_move
                self.stats["greedy_decisions"] += 1
            else:
                greedy_game = copy.deepcopy(self.game)
                greedy_game.move(greedy_move)
                greedy_score = self._evaluate(greedy_game)

                ml_threshold = 0.9 if max_tile >= 256 else 0.8
                if ml_score >= greedy_score * ml_threshold:
                    best_move = ml_move
                    self.stats["ml_decisions"] += 1
                else:
                    best_move = greedy_move
                    self.stats["greedy_decisions"] += 1

        self.decision_cache[grid_tuple] = (best_move, base_probability)
        return best_move

    def _ml_enhanced_look_ahead(self, game, depth, base_probability):
        """优化采样数，避免高分爆炸"""
        if depth == 0:
            eval_score = self._evaluate(game)
            probability = self.predict_probability(game)
            ml_factor = 1.0 + (probability - base_probability) * 2.5
            return None, eval_score * ml_factor

        best_score = -float('inf')
        best_move = None

        for direction in range(4):
            game_copy = copy.deepcopy(game)
            if game_copy.move(direction):
                if depth == 1:
                    eval_score = self._evaluate(game_copy)
                    probability = self.predict_probability(game_copy)
                    ml_factor = 1.0 + (probability - base_probability) * 2.5
                    move_score = eval_score * ml_factor
                else:
                    empty_cells = [(i, j) for i in range(GRID_SIZE) for j in range(GRID_SIZE) if game_copy.grid[i][j] == 0]
                    # 限制采样数
                    samples = min(2, len(empty_cells))
                    if samples > 0:
                        sample_cells = random.sample(empty_cells, samples)
                        scores = []
                        for value, prob in [(TWO, 0.9), (FOUR, 0.1)]:
                            for cell in sample_cells:
                                game_sim = copy.deepcopy(game_copy)
                                game_sim.grid[cell[0]][cell[1]] = value
                                _, score = self._ml_enhanced_look_ahead(game_sim, depth - 1, base_probability)
                                scores.append(score * prob)
                        move_score = sum(scores)
                    else:
                        move_score = self._evaluate(game_copy)
                if move_score > best_score:
                    best_score = move_score
                    best_move = direction
        return best_move, best_score
    
    def collect_training_data(self, num_games=500, max_moves=3000):
        """通过模拟游戏收集训练数据"""
        from game import Game2048
        
        X = []
        y = []
        total_samples = 0
        
        for i in tqdm(range(num_games), desc="收集训练数据"):
            game = Game2048()
            states = []
            
            move_count = 0
            
            # 决定本局使用的AI策略
            strategy = "greedy"
            if i % 5 == 0:  # 每5局用1局随机移动增加样本多样性
                strategy = "semi_random"
            
            with tqdm(total=max_moves, desc=f"游戏 {i+1}/{num_games}", leave=False) as pbar:
                while game.get_game_state() == 0 and move_count < max_moves:
                    states.append(copy.deepcopy(game))
                    
                    # 根据选择的策略决定移动
                    if strategy == "greedy":
                        ai = Greedy_AI2048(game)
                        move = ai.get_move()
                    else:
                        # 70%贪婪, 30%随机
                        if random.random() < 0.7:
                            ai = Greedy_AI2048(game)
                            move = ai.get_move()
                        else:
                            # 随机选择有效移动
                            valid_moves = []
                            for direction in range(4):
                                game_copy = copy.deepcopy(game)
                                if game_copy.move(direction):
                                    valid_moves.append(direction)
                            
                            move = random.choice(valid_moves) if valid_moves else random.randint(0, 3)
                    
                    game.move(move)
                    move_count += 1
                    pbar.update(1)
                    
                    if move_count % 100 == 0:
                        max_tile = max(max(row) for row in game.get_grid())
                        pbar.set_description(f"游戏 {i+1}/{num_games} - 最大值: {max_tile}")
                
                max_tile = max(max(row) for row in game.get_grid())
                pbar.set_description(f"游戏 {i+1}/{num_games} 完成 - 最大值: {max_tile}")
            
            final_max_tile = max(max(row) for row in game.get_grid())
            reached_2048 = final_max_tile >= 2048
            
            # 处理完整游戏状态(保留决策路径)
            with tqdm(total=len(states), desc="处理游戏状态", leave=False) as pbar:
                for state in states:
                    features = self.extract_features(state)
                    X.append(features[0])
                    y.append(1 if reached_2048 else 0)
                    pbar.update(1)
            
            total_samples += len(states)
            tqdm.write(f"游戏 {i+1}/{num_games} 完成: 最大值={max_tile}, 成功达到2048={reached_2048}, 累计样本数={total_samples}")
        
        return np.array(X), np.array(y)
    
    def train_model(self, X=None, y=None, num_games=500, max_moves=3000):
        """训练随机森林模型并保存"""
        if X is None or y is None:
            print("收集训练数据中...")
            X, y = self.collect_training_data(num_games, max_moves)
        
        if len(X) == 0:
            print("没有收集到训练数据")
            return False
        
        print(f"开始训练模型，使用 {len(X)} 个训练样本")
        
        # 清空决策缓存
        self.decision_cache = {}
        
        # 检查成功率并平衡数据集
        success_rate = sum(y) / len(y)
        print(f"原始样本成功率: {success_rate:.2%}")
        
        # 平衡数据集
        if success_rate < 0.1 or success_rate > 0.9:
            print("数据不平衡，进行采样平衡...")
            pos_indices = np.where(y == 1)[0]
            neg_indices = np.where(y == 0)[0]
            
            min_samples = min(len(pos_indices), len(neg_indices))
            min_samples = max(100, min_samples)
            
            if len(pos_indices) > min_samples and len(neg_indices) > min_samples:
                if len(pos_indices) > len(neg_indices):
                    pos_indices = np.random.choice(pos_indices, len(neg_indices), replace=False)
                else:
                    neg_indices = np.random.choice(neg_indices, len(pos_indices), replace=False)
                
                balanced_indices = np.concatenate([pos_indices, neg_indices])
                X = X[balanced_indices]
                y = y[balanced_indices]
                print(f"平衡后样本数: {len(X)}, 成功率: {sum(y)/len(y):.2%}")
        
        # 标准化特征
        print("特征标准化...")
        with tqdm(total=100, desc="特征标准化进度") as pbar:
            pbar.update(10)
            self.scaler = StandardScaler().fit(X)
            pbar.update(40)
            X_scaled = self.scaler.transform(X)
            pbar.update(50)
        
        # 训练模型
        print("训练随机森林分类器...")
        with tqdm(total=100, desc="模型训练进度") as pbar:
            self.model = RandomForestClassifier(
                n_estimators=150,        
                max_depth=15,            
                min_samples_split=10,    
                min_samples_leaf=4,      
                max_features='sqrt',     
                bootstrap=True,          
                random_state=42
            )
            
            pbar.update(20)
            self.model.fit(X_scaled, y)
            pbar.update(80)
        
        # 计算准确率
        accuracy = self.model.score(X_scaled, y)
        print(f"模型训练完成，训练集准确率: {accuracy:.2f}")
        
        # 查看特征重要性
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
            print("\n特征重要性:")
            for i, imp in enumerate(importances):
                print(f"特征 {i}: {imp:.4f}")
        
        # 保存模型
        print("保存模型...")
        self.save_model()
        
        return True
    
    def get_stats(self):
        """获取AI运行的统计信息"""
        return self.stats


# 测试代码
if __name__ == "__main__":
    """测试ML增强AI的训练和游戏表现"""
    import time
    from game import Game2048
    
    print("创建ML增强AI实例...")
    game = Game2048()
    ai = ML_Enhanced_AI2048(game)
    
    # 训练模型
    if not hasattr(ai.model, 'classes_'):
        print("训练模型中...")
        ai.train_model(num_games=50, max_moves=2000)
    
    # 运行测试游戏
    print("\n开始游戏测试...")
    game = Game2048()
    ai.game = game
    
    move_count = 0
    max_moves = 1500
    
    with tqdm(total=max_moves, desc="游戏进度") as pbar:
        while game.get_game_state() == 0 and move_count < max_moves:
            move = ai.get_move()
            game.move(move)
            move_count += 1
            
            pbar.update(1)
            if move_count % 10 == 0:
                max_tile = max(max(row) for row in game.get_grid())
                pbar.set_description(f"游戏进度 - 移动: {move_count}, 分数: {game.get_score()}, 最大值: {max_tile}")
            
            time.sleep(0.01)
    
    # 打印结果
    max_tile = max(max(row) for row in game.get_grid())
    reached_2048 = max_tile >= 2048
    print(f"\n游戏结束! 最终分数: {game.get_score()}, 最大数字: {max_tile}, 移动次数: {move_count}")
    print(f"成功达到2048: {reached_2048}")
    print(f"AI统计: {ai.stats}")