#!/usr/bin/env python3
import sys

from src.pipelines.training import main as train_main
from src.utils.logger import setup_logger


def main():
    setup_logger()
    results = train_main()
    return 0 if results.get("status") == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
