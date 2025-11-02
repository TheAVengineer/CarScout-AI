"""
Celery Diagnostic Tool
Helps identify why workers aren't processing tasks
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workers.pipeline.celery_app import celery_app
from celery import Celery
from configs.settings import settings
import redis


print("=" * 70)
print("🔍 CELERY DIAGNOSTIC TOOL")
print("=" * 70)

# Test 1: Redis Connection
print("\n1️⃣  Testing Redis connection...")
try:
    r = redis.from_url(settings.CELERY_BROKER_URL)
    r.ping()
    print("  ✅ Redis connection: OK")
    
    # Check queue
    queue_length = r.llen('celery')
    print(f"  📊 Tasks in 'celery' queue: {queue_length}")
    
except Exception as e:
    print(f"  ❌ Redis connection failed: {e}")

# Test 2: Celery Configuration
print("\n2️⃣  Checking Celery configuration...")
print(f"  Broker: {celery_app.conf.broker_url}")
print(f"  Backend: {celery_app.conf.result_backend}")
print(f"  Registered tasks: {len(celery_app.tasks)}")

# Test 3: List registered tasks
print("\n3️⃣  Registered tasks:")
task_list = [task for task in celery_app.tasks.keys() if not task.startswith('celery.')]
for task in sorted(task_list)[:15]:  # Show first 15
    print(f"  • {task}")

# Test 4: Worker status
print("\n4️⃣  Checking worker status...")
try:
    inspect = celery_app.control.inspect()
    
    active = inspect.active()
    if active:
        print(f"  ✅ Active workers: {list(active.keys())}")
        for worker, tasks in active.items():
            print(f"    {worker}: {len(tasks)} tasks running")
    else:
        print("  ⚠️  No active workers found!")
        
    registered = inspect.registered()
    if registered:
        print(f"  ✅ Workers have registered tasks")
        for worker, tasks in registered.items():
            print(f"    {worker}: {len(tasks)} tasks registered")
    else:
        print("  ❌ No workers have registered any tasks!")
        
except Exception as e:
    print(f"  ❌ Cannot inspect workers: {e}")

# Test 5: Send test task
print("\n5️⃣  Sending test task...")
try:
    from workers.pipeline.tasks.parse import parse_listing
    
    result = parse_listing.delay("diagnostic-test-123")
    print(f"  ✅ Task sent: {result.id}")
    print(f"  📊 State: {result.state}")
    
    print("\n  ⏳ Waiting 3 seconds...")
    import time
    time.sleep(3)
    
    print(f"  📊 State after 3s: {result.state}")
    
    if result.state == 'PENDING':
        print("\n  ⚠️  DIAGNOSIS: Task stuck in PENDING")
        print("     This means:")
        print("     1. Workers are NOT picking up tasks from the queue")
        print("     2. Possible causes:")
        print("        - Workers not running")
        print("        - Workers listening to wrong queue")
        print("        - Task not properly registered")
        print("        - Redis connection issue")
    
except Exception as e:
    print(f"  ❌ Error sending task: {e}")

print("\n" + "=" * 70)
print("💡 RECOMMENDATIONS:")
print("=" * 70)

print("""
If tasks are stuck in PENDING:

1. Make sure workers are running:
   .\scripts\start_workers.ps1

2. Restart workers after code changes:
   - Press Ctrl+C to stop
   - Run start_workers.ps1 again

3. Check worker logs for errors

4. Verify Redis is running:
   docker ps | findstr carscout-redis

5. Test Redis directly:
   docker exec -it carscout-redis redis-cli ping
""")
