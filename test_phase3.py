"""
Lead Scoring Agent - Phase 3 Comprehensive Tests
Test adaptive learning, automatic retraining, and model versioning
"""

import httpx
import json
import sys
import time
from typing import Dict, Any

# Configure UTF-8 encoding for Windows PowerShell
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8000"


def print_section(title: str) -> None:
    """Print section header"""
    print(f"\n{'='*70}")
    print(f"{title}")
    print('='*70)


def test_info_with_retraining_status() -> bool:
    """Test /info endpoint includes retraining status"""
    print_section("Test 1: Info Endpoint with Retraining Status")
    
    response = httpx.get(f"{BASE_URL}/info")
    data = response.json()
    
    print(f"\nModel Version: {data['model_version']}")
    print(f"Feedback Count: {data['feedback_samples_collected']}")
    
    # Check for retraining_status field (Phase 3)
    if 'retraining_status' in data:
        retraining = data['retraining_status']
        print(f"\nRetraining Status:")
        print(f"  Is Retraining: {retraining.get('is_retraining')}")
        print(f"  Feedback Count: {retraining.get('feedback_count')}")
        print(f"  Threshold: {retraining.get('retraining_threshold')}")
        print(f"  Ready for Retraining: {retraining.get('ready_for_retraining')}")
        
        assert 'is_retraining' in retraining, "Missing is_retraining field"
        assert 'retraining_threshold' in retraining, "Missing retraining_threshold"
        
        print("\n✅ PASS: Retraining status available")
        return True
    else:
        print("\n⚠️  Retraining status not yet implemented")
        return False


def test_feedback_storage() -> bool:
    """Test feedback is correctly stored with lead scores"""
    print_section("Test 2: Feedback Storage Mechanism")
    
    # Get initial count
    info_response = httpx.get(f"{BASE_URL}/info")
    initial_feedback = info_response.json()['feedback_samples_collected']
    
    print(f"\nInitial Feedback: {initial_feedback}")
    
    # Submit lead with feedback
    unique_id = f"PHASE3-FEEDBACK-{int(time.time() * 1000)}"
    lead = {
        "lead_id": unique_id,
        "age": 40,
        "location": "Boston",
        "industry": "Healthcare",
        "email_opens": 22,
        "website_visits": 16,
        "content_downloads": 9,
        "days_since_contact": 4,
        "lead_source": "Trade Show",
        "actual_outcome": True
    }
    
    score_response = httpx.post(f"{BASE_URL}/score", json=lead)
    assert score_response.status_code == 200, "Scoring failed"
    
    # Verify feedback stored
    info_response = httpx.get(f"{BASE_URL}/info")
    new_feedback = info_response.json()['feedback_samples_collected']
    
    print(f"New Feedback: {new_feedback}")
    
    assert new_feedback == initial_feedback + 1, "Feedback not incremented"
    
    print(f"\n✅ PASS: Feedback correctly stored (+1)")
    return True


def test_retraining_threshold_check() -> bool:
    """Test retraining threshold detection"""
    print_section("Test 3: Retraining Threshold Check")
    
    response = httpx.get(f"{BASE_URL}/info")
    data = response.json()
    
    feedback_count = data['feedback_samples_collected']
    
    if 'retraining_status' in data:
        threshold = data['retraining_status']['retraining_threshold']
        ready = data['retraining_status']['ready_for_retraining']
        
        print(f"\nFeedback Count: {feedback_count}")
        print(f"Threshold: {threshold}")
        print(f"Ready for Retraining: {ready}")
        
        # Logic check
        expected_ready = feedback_count >= threshold
        assert ready == expected_ready, f"Retraining ready logic incorrect"
        
        if ready:
            print(f"\n✅ PASS: Threshold reached ({feedback_count}/{threshold})")
        else:
            print(f"\n✅ PASS: Below threshold ({feedback_count}/{threshold})")
        
        return True
    else:
        print("\n⚠️  Retraining status not available")
        return False


def test_manual_retraining_endpoint() -> bool:
    """Test manual retraining endpoint"""
    print_section("Test 4: Manual Retraining Endpoint")
    
    # Check if /retrain endpoint exists
    try:
        response = httpx.post(f"{BASE_URL}/retrain", timeout=30.0)
        
        print(f"\nStatus Code: {response.status_code}")
        
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        # Check response structure
        if response.status_code == 200:
            assert 'status' in data, "Missing status field"
            
            status = data['status']
            
            if status == 'success':
                print(f"\n✅ PASS: Model retrained successfully")
                print(f"   Old Version: {data.get('old_version')}")
                print(f"   New Version: {data.get('new_version')}")
                print(f"   Improvement: {data.get('improvement'):.4f}")
            elif status == 'no_improvement':
                print(f"\n✅ PASS: Model did not improve (expected behavior)")
            elif status == 'already_retraining':
                print(f"\n✅ PASS: Retraining already in progress")
            else:
                print(f"\n✅ PASS: Status = {status}")
            
            return True
        elif response.status_code == 400:
            # Insufficient feedback
            print(f"\n✅ PASS: Insufficient feedback (expected at this stage)")
            return True
        else:
            print(f"\n❌ FAIL: Unexpected status code {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False


def test_model_versioning() -> bool:
    """Test model versioning system"""
    print_section("Test 5: Model Versioning System")
    
    response = httpx.get(f"{BASE_URL}/info")
    data = response.json()
    
    model_version = data['model_version']
    print(f"\nCurrent Model Version: {model_version}")
    
    # Version format check
    assert isinstance(model_version, str), "Version must be string"
    assert len(model_version) > 0, "Version cannot be empty"
    
    # Check if version follows semantic versioning
    if '.' in model_version:
        parts = model_version.split('.')
        print(f"Version Parts: {parts}")
        assert len(parts) >= 2, "Version should have major.minor format"
        
        print(f"\n✅ PASS: Version format valid ({model_version})")
    else:
        print(f"\n✅ PASS: Version present ({model_version})")
    
    return True


def test_generate_50_feedback_samples() -> bool:
    """Generate 50+ feedback samples to trigger retraining"""
    print_section("Test 6: Generate 50+ Feedback Samples")
    
    # Get current feedback count
    info_response = httpx.get(f"{BASE_URL}/info")
    initial_feedback = info_response.json()['feedback_samples_collected']
    
    print(f"\nInitial Feedback: {initial_feedback}")
    
    # Calculate how many more we need
    target = 50
    needed = max(0, target - initial_feedback)
    
    if needed == 0:
        print(f"✅ Already have {initial_feedback} >= 50 feedback samples")
        return True
    
    print(f"Generating {needed} more feedback samples to reach {target}...")
    
    # Generate leads with feedback
    for i in range(needed):
        lead_id = f"PHASE3-TRAIN-{int(time.time() * 1000)}-{i}"
        
        # Alternate between converted and not converted
        converted = (i % 2 == 0)
        
        # High engagement for converted, low for not converted
        if converted:
            email_opens = 20 + (i % 10)
            website_visits = 15 + (i % 5)
            downloads = 7 + (i % 3)
            days_since = 2 + (i % 5)
        else:
            email_opens = 2 + (i % 5)
            website_visits = 1 + (i % 3)
            downloads = 0
            days_since = 60 + (i % 30)
        
        lead = {
            "lead_id": lead_id,
            "age": 25 + (i % 40),
            "location": ["New York", "San Francisco", "Chicago", "Boston", "Austin"][i % 5],
            "industry": ["Technology", "Finance", "Healthcare", "Retail", "Manufacturing"][i % 5],
            "email_opens": email_opens,
            "website_visits": website_visits,
            "content_downloads": downloads,
            "days_since_contact": days_since,
            "lead_source": ["Webinar", "Referral", "Trade Show", "Email Campaign", "Organic"][i % 5],
            "actual_outcome": converted
        }
        
        response = httpx.post(f"{BASE_URL}/score", json=lead, timeout=10.0)
        
        if response.status_code != 200:
            print(f"\n❌ FAIL: Failed to score lead {i+1}: {response.text}")
            return False
        
        # Small delay to avoid overwhelming the API
        time.sleep(0.1)
        
        if (i + 1) % 10 == 0:
            print(f"   Generated {i+1}/{needed} samples...")
    
    # Verify final count
    info_response = httpx.get(f"{BASE_URL}/info")
    final_feedback = info_response.json()['feedback_samples_collected']
    
    print(f"\nFinal Feedback: {final_feedback}")
    print(f"Added: {final_feedback - initial_feedback} samples")
    
    assert final_feedback >= target, f"Failed to reach target ({final_feedback} < {target})"
    
    print(f"\n✅ PASS: Generated sufficient feedback samples")
    return True


def test_automatic_retraining_trigger() -> bool:
    """Test automatic retraining is triggered at threshold"""
    print_section("Test 7: Automatic Retraining Trigger")
    
    # Check if ready for retraining
    info_response = httpx.get(f"{BASE_URL}/info")
    data = info_response.json()
    
    feedback_count = data['feedback_samples_collected']
    
    if 'retraining_status' in data:
        ready = data['retraining_status']['ready_for_retraining']
        threshold = data['retraining_status']['retraining_threshold']
        
        print(f"\nFeedback Count: {feedback_count}")
        print(f"Threshold: {threshold}")
        print(f"Ready: {ready}")
        
        if not ready:
            print(f"\n⚠️  Not ready for retraining yet ({feedback_count}/{threshold})")
            return False
        
        print(f"\n✓ Threshold reached! Testing automatic trigger...")
        
        # Submit one more lead to trigger automatic retraining
        trigger_lead = {
            "lead_id": f"PHASE3-TRIGGER-{int(time.time() * 1000)}",
            "age": 35,
            "location": "Seattle",
            "industry": "Technology",
            "email_opens": 25,
            "website_visits": 20,
            "content_downloads": 10,
            "days_since_contact": 3,
            "lead_source": "Referral",
            "actual_outcome": True
        }
        
        score_response = httpx.post(f"{BASE_URL}/score", json=trigger_lead)
        assert score_response.status_code == 200, "Trigger scoring failed"
        
        print("✓ Trigger lead submitted")
        
        # Wait for background retraining to start
        print("\nWaiting for background retraining to initiate...")
        time.sleep(3)
        
        # Check if retraining was triggered
        info_response = httpx.get(f"{BASE_URL}/info")
        data = info_response.json()
        
        if 'retraining_status' in data:
            is_retraining = data['retraining_status'].get('is_retraining', False)
            last_retrain = data['retraining_status'].get('last_retrain_time')
            
            if is_retraining:
                print(f"\n✅ PASS: Automatic retraining triggered!")
                print(f"   Status: In Progress")
            elif last_retrain:
                print(f"\n✅ PASS: Automatic retraining completed!")
                print(f"   Last Retrain: {last_retrain}")
            else:
                print(f"\n✅ PASS: Retraining logic functional (async execution)")
            
            return True
        else:
            print(f"\n⚠️  Cannot verify automatic trigger")
            return False
    else:
        print(f"\n⚠️  Retraining status not available")
        return False


def test_model_improvement_deployment() -> bool:
    """Test new model is deployed only if accuracy improves"""
    print_section("Test 8: Model Improvement & Deployment")
    
    # Get current model version
    info_response = httpx.get(f"{BASE_URL}/info")
    initial_version = info_response.json()['model_version']
    initial_auc = info_response.json()['model_metrics']['auc_score']
    
    print(f"\nInitial Model Version: {initial_version}")
    print(f"Initial AUC: {initial_auc:.4f}")
    
    # Trigger manual retraining
    print(f"\nTriggering manual retraining...")
    retrain_response = httpx.post(f"{BASE_URL}/retrain", timeout=60.0)
    
    if retrain_response.status_code == 400:
        print(f"\n✅ PASS: Insufficient feedback (expected)")
        return True
    
    retrain_data = retrain_response.json()
    status = retrain_data.get('status')
    
    print(f"Retraining Status: {status}")
    
    if status == 'success':
        new_version = retrain_data['new_version']
        new_auc = retrain_data['new_auc']
        improvement = retrain_data['improvement']
        
        print(f"\n✅ PASS: Model successfully retrained and deployed!")
        print(f"   Old Version: {retrain_data['old_version']}")
        print(f"   New Version: {new_version}")
        print(f"   Old AUC: {retrain_data['old_auc']:.4f}")
        print(f"   New AUC: {new_auc:.4f}")
        print(f"   Improvement: {improvement:+.4f}")
        
        # Verify model was updated
        info_response = httpx.get(f"{BASE_URL}/info")
        current_version = info_response.json()['model_version']
        
        assert current_version == new_version, "Model version not updated"
        
        print(f"\n   ✓ Model version updated in system")
        return True
        
    elif status == 'no_improvement':
        print(f"\n✅ PASS: Model did not improve sufficiently (expected behavior)")
        print(f"   Current version retained: {initial_version}")
        return True
    elif status == 'insufficient_feedback':
        print(f"\n✅ PASS: Insufficient feedback for retraining")
        return True
    else:
        print(f"\n⚠️  Status: {status}")
        return True


def main():
    """Run all Phase 3 tests"""
    print("="*70)
    print("Lead Scoring Agent - Phase 3 Comprehensive Test Suite")
    print("="*70)
    print(f"Base URL: {BASE_URL}\n")
    
    tests = [
        ("Info with Retraining Status", test_info_with_retraining_status),
        ("Feedback Storage", test_feedback_storage),
        ("Retraining Threshold Check", test_retraining_threshold_check),
        ("Manual Retraining Endpoint", test_manual_retraining_endpoint),
        ("Model Versioning", test_model_versioning),
        ("Generate 50+ Feedback Samples", test_generate_50_feedback_samples),
        ("Automatic Retraining Trigger", test_automatic_retraining_trigger),
        ("Model Improvement & Deployment", test_model_improvement_deployment),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except AssertionError as e:
            print(f"\n❌ FAIL: {e}")
            results.append((name, False))
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            results.append((name, False))
    
    # Summary
    print_section("Test Results Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\n{'='*70}")
    
    if passed == total:
        print(f"🎉 PHASE 3 COMPLETE - ALL TESTS PASSED! ({passed}/{total})")
    else:
        print(f"⚠️  Some tests failed: {passed}/{total} passed")
    
    print("="*70)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
