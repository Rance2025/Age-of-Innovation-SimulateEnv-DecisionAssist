from functools import wraps

def generatorize(func):
    """
    装饰器：确保函数返回生成器
    - 如果函数已经是生成器，直接返回
    - 如果函数是普通函数，包装为生成器
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        # 如果已经是生成器，yield from 它
        if hasattr(result, '__iter__') and hasattr(result, '__next__'):
            yield from result
        else:
            # 普通返回值，转为空生成器
            return
            yield  # 使函数成为生成器
    return wrapper