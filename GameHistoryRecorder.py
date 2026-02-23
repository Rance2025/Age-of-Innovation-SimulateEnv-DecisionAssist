import json
import os
from datetime import datetime

def save_game_history(game_args, result=None):
    """
    保存一局游戏结果
    :param game_args: 游戏参数
    :param result: 游戏结果字典（可选）
    """
    # 创建数据字典
    game_record = {
        "timestamp": datetime.now().isoformat(),  # ISO格式时间
        "num_players": game_args['num_players'],
        "setup_mode": game_args['setup_mode'],
        "setup_tile_args": game_args['setup_tile_args'],
        "setup_player_order_args": game_args['setup_player_order_args'],
        "action_mode": game_args['action_mode'],
        "path_length": game_args['path_length'],
        "action_history": game_args['action_history'],
    }
    
    # 如果有结果，添加  
    if result:
        game_record["result"] = result
    
    # 用时间戳创建文件名
    filename = f"game_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join('game_logs', filename)
    
    # 保存文件 - 使用自定义格式化
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('{\n')
        
        # 写入基本字段
        f.write(f'  "timestamp": {json.dumps(game_record["timestamp"], ensure_ascii=False)},\n')
        f.write(f'  "num_players": {game_record["num_players"]},\n')
        f.write(f'  "setup_mode": {json.dumps(game_record["setup_mode"], ensure_ascii=False)},\n')
        
        # 特殊处理 setup_tile_args - 不展开内部列表
        f.write('  "setup_tile_args": ')
        tile_args_str = json.dumps(game_record["setup_tile_args"], ensure_ascii=False)
        f.write(tile_args_str)
        f.write(',\n')
        
        f.write(f'  "setup_player_order_args": {json.dumps(game_record["setup_player_order_args"], ensure_ascii=False)},\n')
        f.write(f'  "action_mode": {json.dumps(game_record["action_mode"], ensure_ascii=False)},\n')
        f.write(f'  "path_length": {game_record["path_length"]},\n')
        
        # 特殊处理 action_history - 每个元组一行，内部不展开
        f.write('  "action_history": [\n')
        for i, action in enumerate(game_record["action_history"]):
            # 将元组转换为列表（JSON支持列表）
            action_list = list(action)
            action_str = json.dumps(action_list, ensure_ascii=False)
            indent = '    '
            f.write(f'{indent}{action_str}')
            if i < len(game_record["action_history"]) - 1:
                f.write(',')
            f.write('\n')
        f.write('  ]')
        
        # 如果有结果，添加结果
        if result:
            f.write(',\n  "result": ')
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        f.write('\n}\n')
    
    print(f"✅ 游戏记录已保存到: {filename}")
    return filename