import time
import json
import numpy as np
import matplotlib.pyplot as plt
from game import Game2048
from Greedy_ai import Greedy_AI2048
from MCTS_ai import MCTS_AI2048
from utils import get_path


def test_ai_performance(ai_class=Greedy_AI2048, ai_name="Greedy", num_games=10, max_moves=10000, **kwargs):
    """测试AI性能"""
    scores = []
    max_tiles = []
    moves_count = []
    game_durations = []

    for i in range(num_games):
        print(f"Game Running: {i + 1}/{num_games} ")
        game = Game2048()
        ai = ai_class(game, **kwargs)
        
        move_count = 0
        start_time = time.time()

        while game.get_game_state() == 0 and move_count < max_moves:
            move = ai.get_move()
            game.move(move)
            move_count += 1
        
        end_time = time.time()

        # 记录结果
        scores.append(game.get_score())
        max_tiles.append(max(max(row) for row in game.get_grid()))
        moves_count.append(move_count)
        game_durations.append(end_time - start_time)
        
        # 打印当前游戏结果
        print(f"Score: {game.get_score()}, Max Tile: {max(max(row) for row in game.get_grid())}")

    stats = {
        "average_score": float(np.mean(scores)),
        "highest_score": int(np.max(scores)),
        "average_max_tile": float(np.mean(max_tiles)),
        "highest_max_tile": int(np.max(max_tiles)),
        "average_moves": float(np.mean(moves_count)),
        "success_rate_2048": float(sum(1 for max_tile in max_tiles if max_tile >= 2048) / num_games * 100),
        "average_time_to_2048": float(np.mean([game_durations[i] for i in range(num_games) if max_tiles[i] >= 2048])) if any(max_tile >= 2048 for max_tile in max_tiles) else 0,
    }


    results = {
        "ai_name": ai_name,
        "scores": scores,
        "max_tiles": max_tiles,
        "moves_count": moves_count,
        "game_durations": game_durations,
        "stats": stats
    }

    # 打印统计信息
    print(f"\n===== {ai_name} AI Test Results =====")
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    return results

def visualize_results(results):
    """可视化测试结果"""
    # 获取AI名称
    ai_name = results.get("ai_name", "Unknown")
    
    plt.figure(figsize=(15, 10))

    plt.subplot(2, 2, 1)
    plt.hist(results["scores"], bins=10)
    plt.title(f"{ai_name} - Score Distribution")
    plt.xlabel("Score")
    plt.ylabel("Frequency")
    max_score = max(results["scores"]) if results["scores"] else 1000
    plt.xlim(0, max(10000, max_score * 1.2))

    plt.subplot(2, 2, 2)
    plt.hist(results["max_tiles"], bins=[2**i for i in range(1, 13)])
    plt.title(f"{ai_name} - Max Tile Distribution")
    plt.xlabel("Tile Value")
    plt.ylabel("Frequency")
    plt.xscale("log", base=2)

    plt.subplot(2, 2, 3)
    plt.hist(results["moves_count"], bins=10)
    plt.title(f"{ai_name} - Move Count Distribution")
    plt.xlabel("Number of Moves")
    plt.ylabel("Frequency")
    
    plt.subplot(2, 2, 4)
    plt.hist(results["game_durations"], bins=10)
    plt.title(f"{ai_name} - Game Duration Distribution")
    plt.xlabel("Duration (seconds)")
    plt.ylabel("Frequency")

    plt.tight_layout()
    plt.show()


def compare_ai_results(greedy_results, mcts_results):
    """比较两种AI的结果并创建对比图表"""
    plt.figure(figsize=(15, 10))
    
    # 比较平均分数
    plt.subplot(2, 2, 1)
    ai_names = ["Greedy", "MCTS"]
    avg_scores = [
        greedy_results["stats"]["average_score"],
        mcts_results["stats"]["average_score"]
    ]
    plt.bar(ai_names, avg_scores)
    plt.title("Average Score Comparison")
    plt.ylabel("Score")
    
    # 比较平均最大方块
    plt.subplot(2, 2, 2)
    avg_max_tiles = [
        greedy_results["stats"]["average_max_tile"],
        mcts_results["stats"]["average_max_tile"]
    ]
    plt.bar(ai_names, avg_max_tiles)
    plt.title("Average Max Tile Comparison")
    plt.ylabel("Tile Value")
    
    # 比较平均移动次数
    plt.subplot(2, 2, 3)
    avg_moves = [
        greedy_results["stats"]["average_moves"],
        mcts_results["stats"]["average_moves"]
    ]
    plt.bar(ai_names, avg_moves)
    plt.title("Average Moves Comparison")
    plt.ylabel("Number of Moves")
    
    # 比较2048成功率
    plt.subplot(2, 2, 4)
    success_rates = [
        greedy_results["stats"]["success_rate_2048"],
        mcts_results["stats"]["success_rate_2048"]
    ]
    plt.bar(ai_names, success_rates)
    plt.title("2048 Success Rate Comparison (%)")
    plt.ylabel("Success Rate")
    
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    # 设置测试参数
    num_games = 10
    max_moves = 10000
    
    # 测试贪婪搜索AI
    print("\nTesting Greedy AI...")
    greedy_results = test_ai_performance(
        ai_class=Greedy_AI2048, 
        ai_name="Greedy",
        num_games=num_games, 
        max_moves=max_moves
    )
    # visualize_results(greedy_results)
    
    # 测试MCTS AI
    print("\nTesting MCTS AI...")
    mcts_results = test_ai_performance(
        ai_class=MCTS_AI2048, 
        ai_name="MCTS",
        num_games=num_games,
        max_moves=max_moves,
        simulation_time=0.5  # MCTS特定参数
    )
    # visualize_results(mcts_results)
    
    # 合并结果并保存到同一个JSON文件
    combined_results = {
        "greedy": greedy_results,
        "mcts": mcts_results,
        "test_params": {
            "num_games": num_games,
            "max_moves": max_moves,
            "mcts_simulation_time": 0.5
        }
    }

    with open(get_path("test_results.json"), 'w') as f:
        json.dump(combined_results, f, indent=4)
    
    # 可视化比较结果
    compare_ai_results(greedy_results, mcts_results)
    
    # 打印简单比较
    print("\n===== AI Performance Comparison =====")
    print(f"Greedy average score: {greedy_results['stats']['average_score']}")
    print(f"MCTS average score: {mcts_results['stats']['average_score']}")
    print(f"Greedy average max tile: {greedy_results['stats']['average_max_tile']}")
    print(f"MCTS average max tile: {mcts_results['stats']['average_max_tile']}")
    print(f"Greedy success rate (2048): {greedy_results['stats']['success_rate_2048']}%")
    print(f"MCTS success rate (2048): {mcts_results['stats']['success_rate_2048']}%")