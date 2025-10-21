"""
Clear all pending tasks from Celery queues
"""
import redis

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=1)

# Get all keys
keys = r.keys('*')
print(f"Found {len(keys)} keys in Redis")

# Clear all queues
for key in keys:
    key_str = key.decode('utf-8')
    print(f"Deleting: {key_str}")
    r.delete(key)

print("\n✅ All queues cleared!")
print("Restart your workers now.")
