# enable_bridge_pos_dict = {
#     (0, 2) : ((1, 0), (2, 2)) ,
#     (0, 8) : ((1, 6),) ,
#     (0, 11) : ((1, 12),) ,
#     (1, 0) : ((0, 2),) ,
#     (1, 3) : ((2, 2),) ,
#     (1, 6) : ((0, 8),) ,
#     (1, 10) : ((2, 12), (3, 10)) ,
#     (1, 12) : ((0, 11),) ,
#     (2, 2) : ((0, 2), (1, 3)) ,
#     (2, 4) : ((3, 2),) ,
#     (2, 6) : ((3, 7),) ,
#     (2, 9) : ((3, 7), (4, 9), (3, 10)) ,
#     (2, 12) : ((1, 10),) ,
#     (3, 2) : ((2, 4),) ,
#     (3, 4) : ((4, 3), (5, 4)) ,
#     (3, 5) : ((4, 7), (5, 5)) ,
#     (3, 7) : ((2, 6), (2, 9)) ,
#     (3, 10) : ((1, 10), (2, 9)) ,
#     (4, 2) : ((6, 2),) ,
#     (4, 3) : ((3, 4), (5, 4), (6, 3)) ,
#     (4, 7) : ((3, 5), (5, 5)) ,
#     (4, 9) : ((2, 9),) ,
#     (5, 0) : ((6, 2),) ,
#     (5, 4) : ((3, 4), (4, 3), (6, 3)) ,
#     (5, 5) : ((3, 5), (4, 7)) ,
#     (5, 7) : ((6, 6), (7, 7)) ,
#     (5, 8) : ((7, 8),) ,
#     (5, 10) : ((7, 10),) ,
#     (5, 11) : ((7, 11),) ,
#     (6, 0) : ((7, 1), (8, 0)) ,
#     (6, 2) : ((4, 2), (5, 0)) ,
#     (6, 3) : ((4, 3), (5, 4), (7, 4)) ,
#     (6, 6) : ((5, 7),) ,
#     (7, 1) : ((6, 0),) ,
#     (7, 2) : ((8, 4),) ,
#     (7, 4) : ((6, 3),) ,
#     (7, 7) : ((5, 7),) ,
#     (7, 8) : ((5, 8),) ,
#     (7, 10) : ((5, 10),) ,
#     (7, 11) : ((5, 11),) ,
#     (8, 0) : ((6, 0),) ,
#     (8, 4) : ((7, 2),) ,
# }
# new_dict = {}

# for key, values in enable_bridge_pos_dict.items():
#     for value in values:
#         if key[0] > value[0] or (key[0] == value[0] and key[1] > value[1]):
#             new_key, new_value = value, key
#         else:
#             new_key, new_value = key, value
#         new_dict[(new_key, new_value)] = False

# for key, value in new_dict.items():
#     print(f'{key}: {value},')
# print(len(new_dict))
# new_dict = {
#     ((0, 2), (1, 0)): -1,
#     ((0, 2), (2, 2)): -1,
#     ((0, 8), (1, 6)): -1,
#     ((0, 11), (1, 12)): -1,
#     ((1, 3), (2, 2)): -1,
#     ((1, 10), (2, 12)): -1,
#     ((1, 10), (3, 10)): -1,
#     ((2, 4), (3, 2)): -1,
#     ((2, 6), (3, 7)): -1,
#     ((2, 9), (3, 7)): -1,
#     ((2, 9), (4, 9)): -1,
#     ((2, 9), (3, 10)): -1,
#     ((3, 4), (4, 3)): -1,
#     ((3, 4), (5, 4)): -1,
#     ((3, 5), (4, 7)): -1,
#     ((3, 5), (5, 5)): -1,
#     ((4, 2), (6, 2)): -1,
#     ((4, 3), (5, 4)): -1,
#     ((4, 3), (6, 3)): -1,
#     ((4, 7), (5, 5)): -1,
#     ((5, 0), (6, 2)): -1,
#     ((5, 4), (6, 3)): -1,
#     ((5, 7), (6, 6)): -1,
#     ((5, 7), (7, 7)): -1,
#     ((5, 8), (7, 8)): -1,
#     ((5, 10), (7, 10)): -1,
#     ((5, 11), (7, 11)): -1,
#     ((6, 0), (7, 1)): -1,
#     ((6, 0), (8, 0)): -1,
#     ((6, 3), (7, 4)): -1,
#     ((7, 2), (8, 4)): -1,
# }
# def tran(pos):
#     return chr(ord('A') + pos[0])+str(pos[1]+1)
# for id,key in enumerate(new_dict.keys()):
#     print(f'\t  {232+id}: ', end='')
#     print('{',end='')
#     print(f"'action': 'build_bridge', 'args': {key}, \t'description': '建立连接{tran(key[0])}与{tran(key[1])}的桥梁'",end='')
#     print('},')
# class MyClass:
#     def my_method(self):
#         pass

# obj = MyClass()
# bound_method = obj.my_method

# print(type(bound_method))
# print(type(MyClass.my_method))
# print(bound_method is MyClass.my_method)
# print(bound_method == MyClass.my_method)
# print(bound_method is MyClass().my_method)
# print(bound_method == MyClass().my_method)
# print(bound_method is obj.my_method)
# print(bound_method == obj.my_method)

# import sys
# import subprocess
# import os

# print("=== Python环境诊断 ===")
# print(f"Python可执行文件: {sys.executable}")
# print(f"Python版本: {sys.version}")
# print(f"当前工作目录: {os.getcwd()}")

# # 检查pip的位置
# try:
#     pip_path = subprocess.check_output([sys.executable, "-m", "pip", "--version"]).decode()
#     print(f"Pip信息: {pip_path}")
# except Exception as e:
#     print(f"无法找到pip: {e}")

# # 检查已安装的包
# print("\n=== 已安装的包 ===")
# try:
#     installed_packages = subprocess.check_output([sys.executable, "-m", "pip", "list"]).decode()
#     print(installed_packages)
# except Exception as e:
#     print(f"无法获取包列表: {e}")

# # 检查Flask是否在Python路径中
# print("\n=== 检查Flask ===")
# try:
#     import flask
#     print(f"✅ Flask已安装: {flask.__version__}")
#     print(f"Flask路径: {flask.__file__}")
# except ImportError as e:
#     print(f"❌ Flask未安装: {e}")
    
# # 检查sys.path
# print("\n=== Python路径 ===")
# for path in sys.path:
#     print(path)
# for shovel_times in range(4):
#     for i in range(1,8):
#         native_terrain_id = i
#         for j in range(1,8):
#             current_terrain_id = j
#             factor = 1 if current_terrain_id >= native_terrain_id else -1
#             if abs(current_terrain_id - native_terrain_id) > 3:
#                 new_terrain_id = (current_terrain_id + factor * shovel_times - 1) % 7 + 1 
#             else:
#                 new_terrain_id = current_terrain_id - factor * shovel_times

#             if new_terrain_id==8:
#                 print(i,j,shovel_times)
# from time import time
# print(time())

def interactive_generator():
    """支持双向通信的生成器"""
    print("生成器启动")
    a = [1,5,6]
    received = yield a
    print(f"收到: {received}")
    received = yield f"处理: {received}"
    print(f"收到: {received}")
    yield "完成"

gen = interactive_generator()

# 第一次必须发送 None 或使用 next()
first = gen.send(None)  # 或 next(gen)
print(f"生成器说: {first}")

second = gen.send("Hello")
print(f"生成器说: {second}")

third = gen.send("World")
print(f"生成器说: {third}")