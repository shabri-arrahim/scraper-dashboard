#!/usr/bin/env python3
"""
Example script that counts from 1 to 20 with delays
This demonstrates a long-running script with regular output
"""

import time
import random

def main():
    print("🚀 Starting counter script...")
    print("This script will count from 1 to 20 with random delays")
    
    for i in range(1, 21):
        # Random delay between 1-3 seconds
        delay = random.uniform(1, 3)
        
        print(f"📊 Count: {i}/20")
        
        if i % 5 == 0:
            print(f"✅ Milestone reached: {i}")
        
        time.sleep(delay)
    
    print("🎉 Counter script completed successfully!")

if __name__ == "__main__":
    main()