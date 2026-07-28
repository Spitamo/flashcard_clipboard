import asyncio
from config import Config
from pipeline.app import run_app

print("main.py started")
def main():
    try:
        cfg = Config()
        asyncio.run(run_app(cfg))
    except KeyboardInterrupt:
        print("Stopping...")
if __name__ == "__main__":
    main()