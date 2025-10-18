#!/usr/bin/env python
"""
Health check script for CarScout AI services
Verifies all components are running and accessible
"""
import sys
import requests
import psycopg2
import redis
from urllib.parse import urlparse


def check_api():
    """Check if API is running"""
    print("🌐 Checking API...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is healthy")
            return True
        else:
            print(f"⚠️  API returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ API is not accessible")
        return False
    except Exception as e:
        print(f"❌ API check failed: {e}")
        return False


def check_postgres():
    """Check PostgreSQL connection"""
    print("\n🗄️  Checking PostgreSQL...")
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="carscout",
            password="carscout_dev",
            database="carscout"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result[0] == 1:
            print("✅ PostgreSQL is connected")
            return True
        else:
            print("⚠️  PostgreSQL returned unexpected result")
            return False
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False


def check_redis():
    """Check Redis connection"""
    print("\n🔴 Checking Redis...")
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis is connected")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False


def check_celery():
    """Check Celery workers"""
    print("\n⚙️  Checking Celery workers...")
    try:
        # Check if Flower is accessible
        response = requests.get("http://localhost:5555/api/workers", timeout=5)
        if response.status_code == 200:
            workers = response.json()
            print(f"✅ Found {len(workers)} Celery workers")
            for worker_name, worker_data in workers.items():
                status = "🟢" if worker_data.get("status") else "🔴"
                print(f"   {status} {worker_name}")
            return len(workers) > 0
        else:
            print("⚠️  Flower API returned unexpected status")
            return False
    except requests.exceptions.ConnectionError:
        print("⚠️  Flower is not accessible (workers may still be running)")
        return None
    except Exception as e:
        print(f"❌ Celery check failed: {e}")
        return False


def check_prometheus():
    """Check Prometheus"""
    print("\n📊 Checking Prometheus...")
    try:
        response = requests.get("http://localhost:9090/-/healthy", timeout=5)
        if response.status_code == 200:
            print("✅ Prometheus is healthy")
            return True
        else:
            print(f"⚠️  Prometheus returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Prometheus is not accessible")
        return False
    except Exception as e:
        print(f"❌ Prometheus check failed: {e}")
        return False


def check_extensions():
    """Check PostgreSQL extensions"""
    print("\n🔌 Checking PostgreSQL extensions...")
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="carscout",
            password="carscout_dev",
            database="carscout"
        )
        cursor = conn.cursor()
        
        # Check for required extensions
        extensions = ["uuid-ossp", "pg_trgm", "vector"]
        for ext in extensions:
            cursor.execute(
                "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = %s)",
                (ext,)
            )
            exists = cursor.fetchone()[0]
            status = "✅" if exists else "❌"
            print(f"   {status} {ext}")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Extension check failed: {e}")
        return False


def check_tables():
    """Check if main tables exist"""
    print("\n📋 Checking database tables...")
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="carscout",
            password="carscout_dev",
            database="carscout"
        )
        cursor = conn.cursor()
        
        # Check for key tables
        tables = [
            "source", "listing_raw", "listing_normalized", 
            "brand_model", "user", "plan", "score"
        ]
        
        for table in tables:
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = %s
                )
                """,
                (table,)
            )
            exists = cursor.fetchone()[0]
            status = "✅" if exists else "❌"
            print(f"   {status} {table}")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Table check failed: {e}")
        return False


def main():
    """Run all health checks"""
    print("🏥 CarScout AI - Health Check")
    print("==============================\n")
    
    checks = [
        ("API", check_api),
        ("PostgreSQL", check_postgres),
        ("Redis", check_redis),
        ("Celery", check_celery),
        ("Prometheus", check_prometheus),
        ("Extensions", check_extensions),
        ("Tables", check_tables),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} check crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Health Check Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result is True)
    total = len(results)
    
    for name, result in results:
        if result is True:
            status = "✅"
        elif result is False:
            status = "❌"
        else:
            status = "⚠️ "
        print(f"{status} {name}")
    
    print()
    print(f"Result: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All systems operational!")
        return 0
    elif passed > total / 2:
        print("⚠️  Some services are down")
        return 1
    else:
        print("❌ Critical systems are down")
        return 2


if __name__ == "__main__":
    sys.exit(main())
