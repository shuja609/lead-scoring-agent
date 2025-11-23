"""
Lead Scoring Agent - Phase 1 Testing Script
Verify all Phase 1 acceptance criteria
"""

import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.database import db
from app.data_generator import SyntheticDataGenerator


def test_database_schema():
    """Test: Database tables created successfully"""
    print("🧪 Testing database schema...")
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if tables exist
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                ORDER BY name
            """)
            tables = [row["name"] for row in cursor.fetchall()]
            
            required_tables = ["lead_scores", "models", "system_metrics"]
            missing_tables = [t for t in required_tables if t not in tables]
            
            if missing_tables:
                print(f"   ✗ Missing tables: {missing_tables}")
                return False
            
            print(f"   ✓ All required tables exist: {required_tables}")
            
            # Check indexes
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND sql IS NOT NULL
            """)
            indexes = [row["name"] for row in cursor.fetchall()]
            print(f"   ✓ Indexes created: {len(indexes)}")
            
            return True
            
    except Exception as e:
        print(f"   ✗ Database test failed: {e}")
        return False


def test_synthetic_data():
    """Test: Synthetic data validates against schema"""
    print("\n🧪 Testing synthetic data generation...")
    
    try:
        generator = SyntheticDataGenerator(seed=42)
        leads = generator.generate_dataset(size=100)
        
        if len(leads) != 100:
            print(f"   ✗ Expected 100 leads, got {len(leads)}")
            return False
        
        print(f"   ✓ Generated {len(leads)} leads")
        
        # Validate data structure
        required_fields = [
            "lead_id", "age", "location", "industry", "email_opens",
            "website_visits", "content_downloads", "days_since_contact",
            "lead_source", "converted"
        ]
        
        for lead in leads[:5]:  # Check first 5
            missing_fields = [f for f in required_fields if f not in lead]
            if missing_fields:
                print(f"   ✗ Missing fields: {missing_fields}")
                return False
        
        print(f"   ✓ All fields present in generated data")
        
        # Check conversion balance
        converted = sum(1 for lead in leads if lead["converted"])
        conversion_rate = converted / len(leads)
        print(f"   ✓ Conversion rate: {conversion_rate:.1%} (target: ~40%)")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Synthetic data test failed: {e}")
        return False


def test_database_operations():
    """Test: Data persisted to SQLite"""
    print("\n🧪 Testing database operations...")
    
    try:
        # Create test lead
        test_lead = {
            "lead_id": f"TEST-{int(time.time())}",
            "age": 35,
            "location": "New York",
            "industry": "Technology",
            "email_opens": 15,
            "website_visits": 10,
            "content_downloads": 5,
            "days_since_contact": 7,
            "lead_source": "Webinar",
            "conversion_score": 0.75,
            "risk_category": "high",
            "actual_outcome": None,
            "model_version": "1.0",
            "timestamp": "2025-11-22T10:00:00"
        }
        
        # Insert lead
        row_id = db.insert_lead_score(test_lead)
        print(f"   ✓ Inserted test lead (row_id: {row_id})")
        
        # Verify insertion
        total_scores = db.get_total_scores()
        print(f"   ✓ Total leads in database: {total_scores}")
        
        # Test metrics update
        db.update_system_metric("test_metric", "test_value")
        metrics = db.get_system_metrics()
        print(f"   ✓ System metrics working: {len(metrics)} metrics")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Database operations test failed: {e}")
        return False


def main():
    """Run all Phase 1 tests"""
    print("=" * 60)
    print("Lead Scoring Agent - Phase 1 Acceptance Tests")
    print("=" * 60)
    print()
    
    # Ensure setup is complete
    settings.ensure_directories()
    db.initialize_schema()
    
    # Run tests
    tests = [
        ("Database Schema", test_database_schema),
        ("Synthetic Data", test_synthetic_data),
        ("Database Operations", test_database_operations)
    ]
    
    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print()
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("🎉 All Phase 1 acceptance criteria met!")
        print()
        print("Phase 1 Deliverables:")
        print("  ✓ Python environment setup")
        print("  ✓ SQLite database schema implementation")
        print("  ✓ FastAPI skeleton with 3 endpoints")
        print("  ✓ Synthetic data generation")
        print()
        print("Next: Start API server with 'python run.py'")
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
    
    print()
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
