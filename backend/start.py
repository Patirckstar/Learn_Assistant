import os
import subprocess
import sys

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    env = os.environ.copy()
    
    cmd = [
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--workers", "4",
        "--loop", "uvloop",
        "--proxy-headers",
    ]
    
    print(f"启动命令: {' '.join(cmd)}")
    print("使用 4 个工作进程，支持并发请求处理")
    print("=" * 60)
    
    subprocess.run(cmd, env=env)

if __name__ == "__main__":
    main()
