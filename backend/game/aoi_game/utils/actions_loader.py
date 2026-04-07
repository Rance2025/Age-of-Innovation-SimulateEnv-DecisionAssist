"""
DetailedAction JSON 数据加载器
替代原来的 DetailedAction 类，从 JSON 文件加载数据
"""
import json
import os


def _convert_lists_to_tuples(obj):
    """递归地将所有 list 转换为 tuple，确保可哈希性"""
    if isinstance(obj, list):
        return tuple(_convert_lists_to_tuples(item) for item in obj)
    elif isinstance(obj, dict):
        return {k: _convert_lists_to_tuples(v) for k, v in obj.items()}
    return obj


def load_detailed_actions() -> dict:
    """
    从 JSON 文件加载详细行动数据
    
    Returns:
        dict: 以 action_id 为 key 的字典，value 包含 action, args, description
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, 'detailed_actions.json')
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 将字符串 key 转换为整数 key，保持与原来一致
    # 同时将所有的 list 转换为 tuple，确保 args 可以作为字典键使用
    return {int(k): _convert_lists_to_tuples(v) for k, v in data.items()}


# 全局缓存，避免重复读取文件
_all_detailed_actions = None


def get_all_detailed_actions() -> dict[int,dict[str,list|int|str]]:
    """
    获取所有详细行动数据（带缓存）
    
    Returns:
        dict: 以 action_id 为 key 的字典
    """
    global _all_detailed_actions
    if _all_detailed_actions is None:
        _all_detailed_actions = load_detailed_actions()
    return _all_detailed_actions


def get_readable_actions(action_ids: list[int]) -> dict[int, str]:
    """
    将行动ID列表转换为可读的字典 {action_id: description}
    
    Args:
        action_ids: 行动ID列表
        
    Returns:
        dict: 行动ID到描述的字典
    """
    all_actions = get_all_detailed_actions()
    return {
        action_id: all_actions[action_id]['description'] 
        for action_id in action_ids 
        if action_id in all_actions
    }