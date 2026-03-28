"""
一键启动前后端服务
"""
import subprocess
import sys
import os
import time
import signal
import atexit

# 全局进程列表
processes = []
_cleanup_done = False

def cleanup():
    """清理所有子进程"""
    global _cleanup_done
    if _cleanup_done:
        return
    _cleanup_done = True

    print("\n正在停止所有服务...")
    for p in processes:
        try:
            if sys.platform == 'win32':
                # 强制终止进程树，确保端口被释放
                import ctypes
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.OpenProcess(1, False, p.pid)
                kernel32.TerminateProcess(handle, -1)
                kernel32.CloseHandle(handle)
            else:
                os.killpg(os.getpgid(p.pid), signal.SIGTERM)
        except:
            pass
    print("服务已停止")
    # 等待端口释放
    time.sleep(1)

def start_backend(host='127.0.0.1', port=5001, player_count=3):
    """启动后端服务"""
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
    images_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend', 'images')

    env = os.environ.copy()
    env['PYTHONPATH'] = backend_dir

    cmd = [
        sys.executable, '-c',
        f'''
import sys
sys.path.insert(0, r"{backend_dir}")
from app import GamePanelAPI
api = GamePanelAPI(host="{host}", port={port}, player_count={player_count}, static_folder=r"{images_dir}")
print(f"后端服务启动在 http://{host}:{port}")
api.run(debug=False, use_reloader=False)
'''
    ]

    if sys.platform == 'win32':
        process = subprocess.Popen(cmd, env=env, stdout=sys.stdout, stderr=sys.stderr)
    else:
        process = subprocess.Popen(cmd, env=env, preexec_fn=os.setsid)

    return process

def start_frontend(host='127.0.0.1', port=5050):
    """启动前端 Vue 开发服务器"""
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend')

    # 先检查 node_modules 是否存在
    node_modules = os.path.join(frontend_dir, 'node_modules')
    if not os.path.exists(node_modules):
        print("首次运行，正在安装依赖...")
        # 运行 npm install
        install_cmd = ['npm', 'install']
        try:
            subprocess.run(install_cmd, cwd=frontend_dir, check=True, shell=True)
            print("依赖安装完成")
        except subprocess.CalledProcessError as e:
            print(f"依赖安装失败: {e}")
            print("请手动运行: cd frontend && npm install")
            sys.exit(1)

    # 启动 Vite 开发服务器
    cmd = ['npm', 'run', 'dev']
    env = os.environ.copy()

    if sys.platform == 'win32':
        process = subprocess.Popen(cmd, cwd=frontend_dir, env=env, shell=True, stdout=sys.stdout, stderr=sys.stderr)
    else:
        process = subprocess.Popen(cmd, cwd=frontend_dir, env=env, shell=True, preexec_fn=os.setsid)

    return process

def main():
    import argparse

    parser = argparse.ArgumentParser(description='一键启动游戏面板前后端服务')
    parser.add_argument('--backend-host', default='127.0.0.1', help='后端主机地址 (默认: 127.0.0.1)')
    parser.add_argument('--backend-port', type=int, default=5001, help='后端端口号 (默认: 5001)')
    parser.add_argument('--frontend-host', default='127.0.0.1', help='前端主机地址 (默认: 127.0.0.1)')
    parser.add_argument('--frontend-port', type=int, default=5050, help='前端端口号 (默认: 5050)')
    parser.add_argument('--players', type=int, default=3, help='玩家数量 (默认: 3)')

    args = parser.parse_args()

    # 注册清理函数
    atexit.register(cleanup)

    print("=" * 60)
    print("游戏面板服务启动器")
    print("=" * 60)

    # 启动后端
    print("\n[1/2] 正在启动后端服务...")
    backend_process = start_backend(args.backend_host, args.backend_port, args.players)
    processes.append(backend_process)
    time.sleep(2)

    # 启动前端
    print("[2/2] 正在启动前端服务...")
    frontend_process = start_frontend(args.frontend_host, args.frontend_port)
    processes.append(frontend_process)
    time.sleep(1)

    print("\n" + "=" * 60)
    print("所有服务已启动!")
    print("=" * 60)
    print(f"前端访问: http://{args.frontend_host}:{args.frontend_port}")
    print(f"后端API:  http://{args.backend_host}:{args.backend_port}")
    print("=" * 60)
    print("按 Ctrl+C 停止所有服务")
    print("=" * 60)

    try:
        # 等待用户中断
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n收到停止信号...")
        cleanup()
        sys.exit(0)

if __name__ == "__main__":
    main()
