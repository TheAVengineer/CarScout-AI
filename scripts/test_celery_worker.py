"""
Test Celery Workers
Sends a simple task to test if workers are processing correctly
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workers.pipeline.tasks.parse import parse_listing


print("=" * 60)
print("🧪 Testing Celery Worker")
print("=" * 60)
print("\n📝 Make sure Celery workers are running!")
print("   Run in another terminal: .\\scripts\\start_workers.ps1")
print("\n⏳ Sending test task...")

# Send a simple task
result = parse_listing.delay("test-id-12345")

print(f"✅ Task sent! Task ID: {result.id}")
print(f"📊 Task state: {result.state}")

print("\n⏳ Waiting for result (10 seconds timeout)...")

try:
    output = result.get(timeout=10)
    print(f"✅ SUCCESS! Worker processed the task!")
    print(f"📄 Result: {output}")
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"📊 Final state: {result.state}")
    
    if "timeout" in str(e).lower():
        print("\n💡 Diagnosis:")
        print("   - Workers are running but not processing tasks")
        print("   - Check worker logs for errors")
        print("   - Verify Redis connection")
        print("   - Ensure task is properly registered")
