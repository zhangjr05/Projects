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
        # 初始化继承自贪婪AI的所有属性
        super().__init__(game)
        self.model = None
        self.scaler = None
        self.model_path = model_path if model_path else get_path("models/2048_model.pkl")
        self.load_or_create_model()
        
        # 统计信息
        self.stats = {
            "predictions": 0,
            "high_probability_paths": 0,
            "low_probability_paths": 0
        }
        
        # 决策缓存，提高性能
        self.decision_cache = {}
        
    def load_or_create_model(self):
        """加载已训练的模型或创建新模型"""
        try:
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
                self.model = model_data['model']
                self.scaler = model_data['scaler']
            print("成功加载2048概率预测模型")
        except (FileNotFoundError, EOFError):
            print("未找到模型文件，创建新的随机森林模型")
            # 使用防过拟合参数创建随机森林
            self.model = RandomForestClassifier(
                n_estimators=150,        # 增加树数量提高稳定性
                max_depth=15,            # 限制树深度避免过拟合
                min_samples_split=10,    # 分裂节点所需最小样本
                min_samples_leaf=4,      # 叶节点最小样本
                max_features='sqrt',     # 限制每棵树使用的特征数
                bootstrap=True,          # 使用bootstrap采样
                random_state=42
            )
            self.scaler = StandardScaler()
    
    def save_model(self):
        """保存模型到文件"""
        model_dir = os.path.dirname(self.model_path)
        os.makedirs(model_dir, exist_ok=True)
        
        with open(self.model_path, 'wb') as f:
            pickle.dump({'model': self.model, 'scaler': self.scaler}, f)
        print(f"模型已保存至 {self.model_path}")
    
    def extract_features(self, game):
        """从游戏状态提取特征，用于机器学习"""
        grid = game.get_grid()
        flat_grid = [cell for row in grid for cell in row]
        
        # 使用贪婪AI的评估分数作为主要特征
        greedy_eval = self._evaluate(game)
        
        # 基本特征
        max_tile = max(flat_grid)
        empty_count = flat_grid.count(0)
        score = game.get_score()
        
        # 合并潜力特征
        merge_potential = 0
        # 水平方向
        for i in range(4):
            for j in range(3):
                if grid[i][j] != 0 and grid[i][j] == grid[i][j+1]:
                    merge_potential += 1
        # 垂直方向
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
        
        # 合并特征向量
        features = [
            greedy_eval,           # 贪婪评估得分
            max_tile,              # 最大方块值 
            empty_count,           # 空格数量
            score / 10000,         # 归一化分数
            merge_potential,       # 合并潜力
            max_in_corner,         # 最大块是否在角落
            # 不同数量级的方块数量
            sum(1 for x in flat_grid if x >= 128),
            sum(1 for x in flat_grid if x >= 256),
            sum(1 for x in flat_grid if x >= 512),
            sum(1 for x in flat_grid if x >= 1024)
        ]
        
        return np.array(features).reshape(1, -1)
    
    def predict_probability(self, game):
        """预测当前状态达到2048的概率"""
        # 检查缓存
        grid_tuple = tuple(tuple(row) for row in game.get_grid())
        if grid_tuple in self.decision_cache and not isinstance(self.decision_cache[grid_tuple], tuple):
            return self.decision_cache[grid_tuple]
        
        # 检查明显高概率情况
        grid = game.get_grid()
        max_tile = max(max(row) for row in grid)
        if max_tile >= 1024:
            probability = 0.95
            self.decision_cache[grid_tuple] = probability
            return probability
        
        # 提取特征
        features = self.extract_features(game)
        
        # 模型未训练情况下使用启发式规则
        if not hasattr(self.model, 'classes_'):
            probability = self._heuristic_probability(game)
            self.decision_cache[grid_tuple] = probability
            return probability
        
        # 使用训练好的模型预测
        try:
            self.stats["predictions"] += 1
            
            # 标准化特征
            if self.scaler is not None:
                try:
                    features = self.scaler.transform(features)
                except:
                    return self._heuristic_probability(game)
            
            # 获取到达2048的概率
            if len(self.model.classes_) > 1:
                proba = self.model.predict_proba(features)[0][1]
            else:
                proba = self._heuristic_probability(game)
                
            # 缓存结果
            self.decision_cache[grid_tuple] = float(proba)
            return float(proba)
        except:
            probability = self._heuristic_probability(game)
            self.decision_cache[grid_tuple] = probability
            return probability
    
    def _heuristic_probability(self, game):
        """基于贪婪评估的启发式概率估计"""
        grid = game.get_grid()
        max_tile = max(max(row) for row in grid)
        empty_count = sum(row.count(0) for row in grid)
        
        # 基于最大值的基础概率
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
        
        # 使用贪婪评估函数增强概率判断
        eval_score = self._evaluate(game)
        
        # 归一化评估分数 (大致范围为0-100)
        normalized_eval = min(1.0, max(0.0, eval_score / 100.0))
        
        # 组合概率
        final_probability = 0.7 * base_probability + 0.3 * normalized_eval
        
        # 空格调整
        if empty_count <= 2:
            final_probability *= 0.7  # 空格太少，减少概率
        
        return max(0.0, min(1.0, final_probability))
    
    def get_move(self):
        """获取最佳移动，结合ML概率预测和贪婪评估"""
        if not self.game:
            return None
        
        # 检查决策缓存
        grid_tuple = tuple(tuple(row) for row in self.game.get_grid())
        if grid_tuple in self.decision_cache and isinstance(self.decision_cache[grid_tuple], tuple):
            return self.decision_cache[grid_tuple][0]
        
        # 获取当前状态达到2048的概率
        base_probability = self.predict_probability(self.game)
        
        # 根据概率动态调整搜索深度
        if base_probability > 0.7:
            depth = 4  # 高概率情况下增加搜索深度
            self.stats["high_probability_paths"] += 1
        elif base_probability < 0.3:
            depth = 2  # 低概率情况下减少搜索深度
            self.stats["low_probability_paths"] += 1
        else:
            depth = 3  # 默认搜索深度
        
        # 使用ML增强的搜索确定最佳移动
        best_move, _ = self._ml_enhanced_look_ahead(self.game, depth, base_probability)
        
        # 如果没有找到有效移动，尝试贪婪评估
        if best_move is None:
            for direction in range(4):
                game_copy = copy.deepcopy(self.game)
                if game_copy.move(direction):
                    best_move = direction
                    break
        
        # 如果仍没有有效移动，随机选择
        if best_move is None:
            best_move = random.randint(0, 3)
        
        # 缓存决策
        self.decision_cache[grid_tuple] = (best_move, base_probability)
        
        return best_move
    
    def _ml_enhanced_look_ahead(self, game, depth, base_probability):
        """结合ML概率预测和贪婪评估的增强搜索"""
        if depth == 0:
            # 叶子节点：使用贪婪评估并结合概率预测
            eval_score = self._evaluate(game)
            probability = self.predict_probability(game)
            
            # 根据概率调整评估分数
            ml_factor = 1.0 + (probability - base_probability) * 2.0
            return None, eval_score * ml_factor
        
        best_score = -float('inf')
        best_move = None
        
        # 搜索所有可能的移动方向
        directions = range(4)
        if getattr(self, '_is_root_call', True) and depth > 3:
            self._is_root_call = False
            directions = tqdm(directions, desc="搜索移动方向", leave=False)
        
        for direction in directions:
            game_copy = copy.deepcopy(game)
            if game_copy.move(direction):
                # 第一层深度使用当前评估加概率调整
                if depth == 1:
                    eval_score = self._evaluate(game_copy)
                    probability = self.predict_probability(game_copy)
                    
                    ml_factor = 1.0 + (probability - base_probability) * 2.0
                    move_score = eval_score * ml_factor
                else:
                    # 更深层的递归搜索
                    empty_cells = [(i, j) for i in range(GRID_SIZE) for j in range(GRID_SIZE) 
                                 if game_copy.grid[i][j] == 0]
                    if empty_cells:
                        # 根据状态潜力决定采样点数量
                        samples = min(4, len(empty_cells)) if self.predict_probability(game_copy) > 0.6 else min(2, len(empty_cells))
                        
                        scores = []
                        sample_cells = random.sample(empty_cells, samples) if len(empty_cells) > samples else empty_cells
                        
                        # 模拟新方块的生成
                        for value in (TWO, FOUR):
                            for cell in sample_cells:
                                game_sim = copy.deepcopy(game_copy)
                                game_sim.grid[cell[0]][cell[1]] = value
                                _, score = self._ml_enhanced_look_ahead(game_sim, depth - 1, base_probability)
                                scores.append(score)
                        
                        move_score = sum(scores) / len(scores) if scores else 0
                    else:
                        move_score = self._evaluate(game_copy)
                
                if move_score > best_score:
                    best_score = move_score
                    best_move = direction
        
        # 重置根调用标记
        if depth > 3:
            self._is_root_call = True
            
        return best_move, best_score
    
    def collect_training_data(self, num_games=100, max_moves=1000):
        """收集训练数据，使用贪婪AI确保高质量样本"""
        from game import Game2048
        
        X = []  # 特征
        y = []  # 标签 (是否达到2048)
        
        total_samples = 0
        
        for i in tqdm(range(num_games), desc="收集训练数据"):
            game = Game2048()
            states = []
            
            move_count = 0
            with tqdm(total=max_moves, desc=f"游戏 {i+1}/{num_games}", leave=False) as pbar:
                while game.get_game_state() == 0 and move_count < max_moves:
                    states.append(copy.deepcopy(game))
                    
                    # 使用贪婪AI策略
                    ai = Greedy_AI2048(game)
                    move = ai.get_move()
                    game.move(move)
                    move_count += 1
                    pbar.update(1)
                    
                    if move_count % 100 == 0:
                        pbar.set_description(f"游戏 {i+1}/{num_games} - 最大值: {max(max(row) for row in game.get_grid())}")
                
                max_tile = max(max(row) for row in game.get_grid())
                pbar.set_description(f"游戏 {i+1}/{num_games} 完成 - 最大值: {max_tile}")
            
            # 检查是否达到2048
            reached_2048 = any(max(max(row) for row in state.get_grid()) >= 2048 for state in states)
            
            # 为每个状态提取特征和添加标签
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
        """训练预测模型"""
        if X is None or y is None:
            print("收集训练数据中...")
            X, y = self.collect_training_data(num_games, max_moves)
        
        if len(X) == 0:
            print("没有收集到训练数据")
            return False
        
        print(f"开始训练模型，使用 {len(X)} 个训练样本")
        
        # 清空决策缓存
        self.decision_cache = {}
        
        # 检查成功率并平衡数据集(防止过拟合)
        success_rate = sum(y) / len(y)
        print(f"样本成功率: {success_rate:.2%}")
        
        # 如果数据极度不平衡，进行欠采样
        if success_rate < 0.1 or success_rate > 0.9:
            print("数据不平衡，进行采样平衡...")
            pos_indices = np.where(y == 1)[0]
            neg_indices = np.where(y == 0)[0]
            
            # 确保每类至少有100个样本
            min_samples = min(len(pos_indices), len(neg_indices))
            min_samples = max(100, min_samples)
            
            if len(pos_indices) > min_samples and len(neg_indices) > min_samples:
                # 随机采样平衡数据集
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
        
        # 训练模型 - 使用防过拟合参数
        print("训练随机森林分类器...")
        with tqdm(total=100, desc="模型训练进度") as pbar:
            self.model = RandomForestClassifier(
                n_estimators=150,        # 增加树数量提高稳定性
                max_depth=15,            # 限制树深度避免过拟合
                min_samples_split=10,    # 分裂节点所需最小样本
                min_samples_leaf=4,      # 叶节点最小样本
                max_features='sqrt',     # 限制每棵树使用的特征数
                bootstrap=True,          # 使用bootstrap采样
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
        """获取统计信息"""
        return self.stats


# 测试代码
if __name__ == "__main__":
    import time
    from game import Game2048
    
    print("创建ML增强AI实例...")
    game = Game2048()
    ai = ML_Enhanced_AI2048(game)
    
    # 训练模型 - 使用优化参数
    if not hasattr(ai.model, 'classes_'):
        print("训练模型中...")
        ai.train_model(num_games=500, max_moves=3000)
    
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
    print(f"\n游戏结束! 最终分数: {game.get_score()}, 最大数字: {max_tile}, 移动次数: {move_count}")
    print(f"AI统计: {ai.stats}")