#!/usr/bin/env python3
"""
Example data processing script
Simulates processing large datasets with progress updates
"""

import time
import random


def process_batch(batch_num, batch_size=100):
    """Simulate processing a batch of data"""
    print(f"Processing batch {batch_num} ({batch_size} items)...")

    for i in range(0, batch_size, 10):
        progress = (i / batch_size) * 100
        print(f"   Progress: {progress:.1f}% ({i}/{batch_size})")
        time.sleep(0.5)

    # Simulate occasional errors
    if random.random() < 0.1:  # 10% chance of error
        print(f"Warning: Minor issue in batch {batch_num}, retrying...")
        time.sleep(1)

    print(f"Batch {batch_num} completed successfully")


def main():
    print("Starting data processor...")
    print("Simulating processing of 5 data batches")

    total_batches = 5

    for batch in range(1, total_batches + 1):
        print(f"\nStarting batch {batch}/{total_batches}")
        process_batch(batch)

        if batch < total_batches:
            print("Brief pause before next batch...")
            time.sleep(2)

    print("\nAll data processing completed!")
    print("Summary: 5 batches processed, 500 total items")


if __name__ == "__main__":
    main()
