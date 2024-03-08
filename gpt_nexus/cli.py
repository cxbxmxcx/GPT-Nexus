# gpt_nexus/cli.py
import argparse
from gpt_nexus.main import run

def main():
    parser = argparse.ArgumentParser(description="CLI for GPT Nexus App")
    parser.add_argument('command', help="The command to run")

    args = parser.parse_args()

    if args.command == 'run':
        run()
    else:
        print(f"Unknown command: {args.command}")

if __name__ == "__main__":
    main()
