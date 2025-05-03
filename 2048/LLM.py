import copy
import time
import numpy as np
from Greedy_ai import Greedy_AI2048
import os
import json
import gradio as gr

try:
    from dashscope import Generation, save_api_key
    GLOBAL_API_KEY = 'sk-11742ea4a8cc421e949e05c049d86e51'
    save_api_key(GLOBAL_API_KEY)
    Generation.api_key = GLOBAL_API_KEY
    os.environ["DASHSCOPE_API_KEY"] = GLOBAL_API_KEY
    LLM_AVAILABLE = True
except ImportError as e:
    print(f"导入DashScope失败: {e}")
    LLM_AVAILABLE = False

def ensure_api_key():
    try:
        from dashscope import Generation
        if not Generation.api_key:
            Generation.api_key = GLOBAL_API_KEY
        return True
    except:
        return False

class LLM_AI2048(Greedy_AI2048):
    def __init__(self, game=None, model="qwen-max", api_key=None):
        super().__init__(game)
        self.model = model
        self.move_history = []
        self.decision_cache = {}
        self.use_llm = LLM_AVAILABLE
        self.failed_calls = 0
        
        self.prompt_template = """
你是一个2048游戏AI专家。你的任务是分析当前游戏状态并给出最佳移动方向。

当前游戏状态:
{}

游戏规则:
- 可以向上(0)、右(1)、下(2)、左(3)四个方向移动
- 相同数字相邻时会合并为它们的和
- 每次移动后会在空白格子随机出现一个2或4
- 游戏目标是获得2048方块

请分析当前局面并考虑以下策略:
1. 保持最大数字在角落
2. 维持递减序列(大数在角落，周围数字依次减小)
3. 保持足够的空白格子
4. 优先考虑合并大数字的可能性

请给出:
1. 当前局面分析
2. 每个可行方向的优缺点
3. 你推荐的最佳移动方向(0-3)

最终决策(仅需给出数字0-3): 
"""
        if api_key:
            try:
                from dashscope import Generation, save_api_key
                save_api_key(api_key)
                Generation.api_key = api_key
                os.environ["DASHSCOPE_API_KEY"] = api_key
                self.use_llm = True
            except:
                pass

    def get_move(self):
        if not self.game:
            return 0
        
        game_state_text = self._format_game_state()
        
        grid_tuple = tuple(map(tuple, self.game.get_grid()))
        if grid_tuple in self.decision_cache:
            return self.decision_cache[grid_tuple]
        
        if self.failed_calls >= 3:
            self.use_llm = False
            
        if not self.use_llm or self._check_fast_path():
            direction = self._get_best_move_by_evaluation()
            self.move_history.append({
                "state": game_state_text,
                "response": "使用评估函数决策" + ("" if self.use_llm else "(LLM已禁用)"),
                "direction": direction,
                "time": time.time()
            })
            return direction
        
        try:
            ensure_api_key()
            
            prompt = self.prompt_template.format(game_state_text)
            
            response = Generation.call(
                model=self.model,
                prompt=prompt,
                result_format='message',
                max_tokens=800,
                temperature=0.3
            )
            
            content = response.output.choices[0]['message']['content']
            
            direction = self._parse_llm_response(content)
            
            self.move_history.append({
                "state": game_state_text,
                "response": content,
                "direction": direction,
                "time": time.time()
            })
            
            self.decision_cache[grid_tuple] = direction
            
            self.failed_calls = 0
            
            return direction
            
        except Exception as e:
            if self.failed_calls == 0:
                print(f"LLM调用错误: {e}")
            self.failed_calls += 1
            
            direction = self._get_best_move_by_evaluation()
            
            self.move_history.append({
                "state": game_state_text,
                "response": f"LLM调用失败({self.failed_calls}/3): 使用评估函数替代",
                "direction": direction,
                "time": time.time()
            })
            
            return direction
    
    def _format_game_state(self):
        grid = self.game.get_grid()
        score = self.game.get_score()
        
        grid_text = "游戏网格:\n"
        grid_text += "+------+------+------+------+\n"
        for row in grid:
            grid_text += "|"
            for cell in row:
                if cell == 0:
                    grid_text += "      |"
                else:
                    grid_text += f"{cell:^6}|"
            grid_text += "\n+------+------+------+------+\n"
        
        empty_count = sum(cell == 0 for row in grid for cell in row)
        max_tile = max(max(row) for row in grid)
        
        max_positions = []
        for i in range(len(grid)):
            for j in range(len(grid[i])):
                if grid[i][j] == max_tile:
                    max_positions.append((i, j))
        
        mergeable_pairs = self._count_mergeable_pairs()
        
        state_text = f"{grid_text}\n"
        state_text += f"当前分数: {score}\n"
        state_text += f"空格数量: {empty_count}\n"
        state_text += f"最大方块: {max_tile} 位置: {max_positions}\n"
        state_text += f"可合并方块对数: {mergeable_pairs}\n"
        
        state_text += "可行移动方向:\n"
        for direction in range(4):
            direction_name = ["上", "右", "下", "左"][direction]
            game_copy = copy.deepcopy(self.game)
            if game_copy.move(direction):
                state_text += f"- 方向{direction}({direction_name}): 有效\n"
            else:
                state_text += f"- 方向{direction}({direction_name}): 无效\n"
                
        return state_text
    
    def _count_mergeable_pairs(self):
        grid = self.game.get_grid()
        count = 0
        
        for i in range(len(grid)):
            for j in range(len(grid[i])-1):
                if grid[i][j] != 0 and grid[i][j] == grid[i][j+1]:
                    count += 1
        
        for i in range(len(grid)-1):
            for j in range(len(grid[i])):
                if grid[i][j] != 0 and grid[i][j] == grid[i+1][j]:
                    count += 1
                    
        return count
    
    def _parse_llm_response(self, response_text):
        direction = 3
        
        try:
            lines = response_text.strip().split('\n')
            for line in lines[::-1]:
                if "决策" in line or "方向" in line or "移动" in line:
                    for num in ["0", "1", "2", "3"]:
                        if num in line:
                            return int(num)
            
            for direction_str in ["0", "1", "2", "3"]:
                if response_text.strip().endswith(direction_str):
                    return int(direction_str)
            
            direction_words = {
                "上": 0, "上移": 0, "向上": 0,
                "右": 1, "右移": 1, "向右": 1,
                "下": 2, "下移": 2, "向下": 2,
                "左": 3, "左移": 3, "向左": 3
            }
            
            for line in lines[-5:]:
                for word, dir_num in direction_words.items():
                    if word in line:
                        return dir_num
            
            for word, dir_num in direction_words.items():
                if word in response_text:
                    return dir_num
        
        except Exception as e:
            print(f"解析响应出错: {e}")
        
        return direction
    
    def _check_fast_path(self):
        grid = np.array(self.game.get_grid())
        if np.sum(grid == 0) <= 2:
            return True
        
        return False
    
    def _get_best_move_by_evaluation(self):
        valid_moves = []
        scores = []
        
        for direction in range(4):
            game_copy = copy.deepcopy(self.game)
            if game_copy.move(direction):
                valid_moves.append(direction)
                scores.append(super()._evaluate(game_copy))
        
        if not valid_moves:
            return 0
        
        best_idx = scores.index(max(scores))
        return valid_moves[best_idx]
    
    def save_history(self, filename=None):
        if not self.move_history:
            return
        
        if filename is None:
            filename = f"llm_decisions_{int(time.time())}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.move_history, f, ensure_ascii=False, indent=2)
            print(f"决策历史已保存到 {filename}")
        except Exception as e:
            print(f"保存决策历史时出错: {e}")


def create_gradio_interface():
    ensure_api_key()
    
    from game import Game2048
    
    global_state = {
        "game": None,
        "ai": None,
        "game_history": [],
        "move_count": 0,
        "running": False,
    }
    
    def initialize_game():
        global_state["game"] = Game2048()
        global_state["ai"] = LLM_AI2048(
            game=global_state["game"]
        )
        global_state["game_history"] = [copy.deepcopy(global_state["game"].get_grid())]
        global_state["move_count"] = 0
        global_state["running"] = False
        return format_grid(global_state["game"].get_grid()), "游戏已初始化，当前分数: 0", ""
    
    def format_grid(grid):
        html = """
        <style>
        .game-container {
            width: 100%;
            max-width: 450px;
            margin: 0 auto;
            padding: 15px;
            background: #bbada0;
            border-radius: 8px;
            position: relative;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            grid-gap: 15px;
            margin-bottom: 10px;
        }
        .cell {
            aspect-ratio: 1/1;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 32px;
            font-weight: bold;
            border-radius: 5px;
            transition: all 0.1s ease;
            box-shadow: 0 0 5px rgba(0,0,0,0.1);
        }
        .cell-2 { background: #eee4da; color: #776e65; }
        .cell-4 { background: #ede0c8; color: #776e65; }
        .cell-8 { background: #f2b179; color: #f9f6f2; }
        .cell-16 { background: #f59563; color: #f9f6f2; }
        .cell-32 { background: #f67c5f; color: #f9f6f2; }
        .cell-64 { background: #f65e3b; color: #f9f6f2; }
        .cell-128 { background: #edcf72; color: #f9f6f2; font-size: 28px; }
        .cell-256 { background: #edcc61; color: #f9f6f2; font-size: 28px; }
        .cell-512 { background: #edc850; color: #f9f6f2; font-size: 28px; }
        .cell-1024 { background: #edc53f; color: #f9f6f2; font-size: 24px; }
        .cell-2048 { background: #edc22e; color: #f9f6f2; font-size: 24px; }
        .cell-0 { background: #cdc1b4; }
        </style>
        
        <div class="game-container">
        <div class="grid">
        """
        
        for row in grid:
            for cell in row:
                value = cell if cell > 0 else ""
                html += f'<div class="cell cell-{cell}">{value}</div>'
        
        html += """
        </div>
        </div>
        """
        return html
    
    def format_thoughts(thoughts):
        if not thoughts:
            return ""
        
        md = f"## 移动 #{global_state['move_count']}\n\n"
        md += f"**方向:** {['上', '右', '下', '左'][thoughts['direction']]} (代码:{thoughts['direction']})\n\n"
        md += "**LLM分析:**\n\n"
        md += f"```\n{thoughts['response']}\n```"
        return md
    
    def make_move():
        if global_state["game"] is None:
            initialize_game()
        
        if global_state["game"].get_game_state() != 0:
            return format_grid(global_state["game"].get_grid()), f"游戏结束，最终分数: {global_state['game'].get_score()}", ""
        
        start_time = time.time()
        direction = global_state["ai"].get_move()
        decision_time = time.time() - start_time
        
        moved = global_state["game"].move(direction)
        global_state["move_count"] += 1
        global_state["game_history"].append(copy.deepcopy(global_state["game"].get_grid()))
        
        thoughts = None
        if global_state["ai"].move_history and len(global_state["ai"].move_history) > 0:
            thoughts = global_state["ai"].move_history[-1]
        
        thoughts_md = format_thoughts(thoughts)
        
        status = global_state["game"].get_game_state()
        status_text = "进行中"
        if status == 1:
            status_text = "胜利！"
        elif status == 2:
            status_text = "失败"
        
        return format_grid(global_state["game"].get_grid()), f"移动 #{global_state['move_count']}: {'上右下左'[direction]}，分数={global_state['game'].get_score()}，状态={status_text}", thoughts_md
    
    def auto_play():
        global_state["running"] = True
        
        if global_state["game"] is None:
            initialize_game()
        
        result = format_grid(global_state["game"].get_grid()), f"自动游戏开始，分数: {global_state['game'].get_score()}", ""
        yield result
        
        moves_without_update = 0
        max_moves_without_update = 3
        
        while global_state["running"] and global_state["game"] and global_state["game"].get_game_state() == 0:
            grid_html, status, thoughts_md = make_move()
            
            moves_without_update += 1
            if moves_without_update >= max_moves_without_update:
                yield grid_html, status, thoughts_md
                moves_without_update = 0
                time.sleep(0.5)
        
        final_score = global_state["game"].get_score() if global_state["game"] else 0
        return format_grid(global_state["game"].get_grid()), f"游戏结束，最终分数: {final_score}", ""
    
    def stop_auto_play():
        global_state["running"] = False
        
        if global_state["game"] is None:
            return "", "游戏未初始化", ""
        
        return format_grid(global_state["game"].get_grid()), f"自动游戏已停止，分数: {global_state['game'].get_score()}", ""
    
    def save_results():
        if global_state["game"] is None:
            return "游戏未初始化"
        
        if global_state["ai"]:
            global_state["ai"].save_history()
            return f"游戏历史已保存，共{global_state['move_count']}步，最终分数: {global_state['game'].get_score()}"
        return "AI未初始化，无法保存历史"
    
    def set_api_key(key):
        try:
            from dashscope import Generation, save_api_key
            save_api_key(key)
            Generation.api_key = key
            os.environ["DASHSCOPE_API_KEY"] = key
            return f"API密钥已保存: {key[:5]}****"
        except Exception as e:
            return f"API密钥设置失败: {str(e)}"
    
    with gr.Blocks(title="LLM玩2048") as demo:
        gr.Markdown("# 🤖 通义千问玩2048")
        gr.Markdown("使用大语言模型来玩2048游戏")
        
        with gr.Row():
            api_input = gr.Textbox(
                label="通义千问API密钥", 
                placeholder="输入API密钥后点击设置",
                type="password"
            )
            api_button = gr.Button("设置API密钥")
            api_status = gr.Textbox(label="API状态")
        
        with gr.Row():
            with gr.Column(scale=3):
                grid_display = gr.HTML()
                status_text = gr.Textbox(label="状态")
                
                with gr.Row():
                    init_button = gr.Button("初始化游戏")
                    move_button = gr.Button("执行一步")
                    auto_button = gr.Button("自动运行")
                    stop_button = gr.Button("停止")
                    save_button = gr.Button("保存历史")
                
                save_status = gr.Textbox(label="保存状态")
                
            with gr.Column(scale=4):
                thoughts_display = gr.Markdown()
        
        api_button.click(set_api_key, inputs=[api_input], outputs=[api_status])
        init_button.click(initialize_game, inputs=[], outputs=[grid_display, status_text, thoughts_display])
        move_button.click(make_move, inputs=[], outputs=[grid_display, status_text, thoughts_display])
        auto_button.click(auto_play, inputs=[], outputs=[grid_display, status_text, thoughts_display])
        stop_button.click(stop_auto_play, inputs=[], outputs=[grid_display, status_text, thoughts_display])
        save_button.click(save_results, inputs=[], outputs=[save_status])
        
        demo.load(lambda: gr.update(value=GLOBAL_API_KEY or ""), outputs=[api_input])
    
    return demo

def create_llm_ai(game, api_key=None):
    if api_key:
        try:
            from dashscope import save_api_key, Generation
            save_api_key(api_key)
            Generation.api_key = api_key
            os.environ["DASHSCOPE_API_KEY"] = api_key
        except ImportError:
            pass
    
    ai = LLM_AI2048(game)
    return ai

if __name__ == "__main__":
    ensure_api_key()
    demo = create_gradio_interface()
    demo.launch()