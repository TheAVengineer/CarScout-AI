#!/usr/bin/env python3
"""
Distribute Workers Optimally Across Market

This script positions workers at different points in the queue
for optimal market coverage instead of all starting at position 0.

Strategy:
- Worker 1: Position 0 (start)
- Worker 2: Position 1/3 (middle-early)
- Worker 3: Position 2/3 (middle-late)
- Worker N: Position N/Total

This ensures fast coverage of the entire market!
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import redis
import json
from configs.settings import settings

def redistribute_workers(num_workers=3):
    """
    Redistribute queue items so workers start at different positions
    
    Args:
        num_workers: Number of workers to distribute (default: 3)
    """
    print(f"🔄 Redistributing queue for {num_workers} workers...")
    print("="*70)
    
    # Connect to Redis (database 0 for scraping queue)
    redis_client = redis.from_url("redis://localhost:6379/0")
    
    # Get all items from queue
    queue_key = "carscout:seeding:queue"
    queue_items = []
    
    # Pop all items
    while True:
        item_json = redis_client.lpop(queue_key)
        if not item_json:
            break
        # Decode if bytes
        if isinstance(item_json, bytes):
            item_json = item_json.decode('utf-8')
        queue_items.append(item_json)
    
    total_items = len(queue_items)
    
    if total_items == 0:
        print("⚠️  Queue is empty! Nothing to redistribute.")
        return
    
    print(f"📊 Found {total_items} brands in queue")
    print("")
    
    # Calculate distribution points
    # For 3 workers: [0, 1/3, 2/3] of queue
    distribution_points = []
    for worker_num in range(num_workers):
        position = int((worker_num / num_workers) * total_items)
        distribution_points.append(position)
    
    print(f"📍 Distribution strategy:")
    for i, pos in enumerate(distribution_points, 1):
        brand_name = json.loads(queue_items[pos])['brand'] if pos < len(queue_items) else "END"
        percentage = (pos / total_items) * 100
        print(f"   Worker {i}: Position {pos}/{total_items} ({percentage:.1f}%) - Starting at '{brand_name}'")
    
    print("")
    
    # Reorder queue for optimal distribution
    # Strategy: Interleave items so each worker gets evenly spaced brands
    reordered_items = []
    
    for worker_num in range(num_workers):
        start_pos = distribution_points[worker_num]
        
        # Each worker takes every Nth item starting from their position
        worker_items = []
        for i in range(start_pos, total_items, num_workers):
            if i < len(queue_items):
                worker_items.append(queue_items[i])
        
        reordered_items.extend(worker_items)
    
    # Push reordered items back to queue (in reverse so LPOP gets them in order)
    for item_json in reversed(reordered_items):
        redis_client.rpush(queue_key, item_json)
    
    print(f"✅ Queue redistributed!")
    print(f"   Total items: {len(reordered_items)}")
    print("")
    
    # Show first few items for each worker
    print(f"🔍 Preview - What each worker will scrape first:")
    print("-"*70)
    
    for worker_num in range(min(num_workers, 3)):  # Show max 3 workers
        print(f"\n🤖 Worker {worker_num + 1}:")
        
        for j in range(min(3, len(reordered_items) // num_workers)):  # Show 3 brands per worker
            idx = worker_num + (j * num_workers)
            if idx < len(reordered_items):
                brand_data = json.loads(reordered_items[idx])
                brand_name = brand_data['brand']
                model_count = brand_data.get('model_count', '?')
                print(f"   {j+1}. {brand_name} ({model_count} models)")
    
    print("")
    print("="*70)
    print("✅ Workers will now start at different positions for optimal coverage!")
    print("")
    print("📌 Next steps:")
    print("   1. Stop current scrapy workers: pkill -f 'scrapy crawl'")
    print("   2. Start workers: ./scripts/start_distributed_seeder.sh balanced 1")
    print("   3. Monitor coverage: docker exec carscout-redis redis-cli LLEN carscout:seeding:queue")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Redistribute worker queue for optimal coverage')
    parser.add_argument('--workers', type=int, default=3, help='Number of workers (default: 3)')
    
    args = parser.parse_args()
    
    redistribute_workers(args.workers)
