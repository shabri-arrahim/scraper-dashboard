#!/usr/bin/env python3
"""
Example script that will fail
This demonstrates error handling and notifications
"""

import time
import sys


def main():
    print("Starting example script that will fail...")
    print("This script is designed to demonstrate error handling")

    for i in range(1, 4):
        print(f"Step {i}/3: Processing...")
        time.sleep(2)

    print("Critical error encountered!")
    print("This is an intentional failure for demonstration")

    # Exit with error code
    sys.exit(1)


if __name__ == "__main__":
    main()
