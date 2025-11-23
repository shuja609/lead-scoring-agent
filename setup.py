"""
Lead Scoring Agent - Setup and Initialization Script
Run this script to set up the project environment
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.database import db
from app.data_generator import SyntheticDataGenerator


def main():
    """Initialize the lead scoring agent"""
    print("=" * 60)
    print("Lead Scoring Agent - Setup & Initialization")
    print("=" * 60)
    print()
    
    # Step 1: Create directories
    print("📁 Creating directories...")
    settings.ensure_directories()
    print(f"   ✓ Created: {settings.database_dir}")
    print()
    
    # Step 2: Initialize database
    print("📊 Initializing database schema...")
    db.initialize_schema()
    print(f"   ✓ Database initialized: {settings.database_path}")
    print(f"   ✓ Tables created: lead_scores, models, system_metrics")
    print()
    
    # Step 3: Generate synthetic data
    print("🎲 Generating synthetic training data...")
    generator = SyntheticDataGenerator(seed=42)
    leads = generator.generate_dataset(size=1000)
    
    # Save to CSV
    csv_path = settings.database_dir / "synthetic_leads.csv"
    generator.save_to_csv(leads, str(csv_path))
    
    converted = sum(1 for lead in leads if lead["converted"])
    print(f"   ✓ Generated {len(leads)} synthetic leads")
    print(f"   ✓ Converted: {converted} ({converted/len(leads)*100:.1f}%)")
    print(f"   ✓ Not Converted: {len(leads)-converted} ({(len(leads)-converted)/len(leads)*100:.1f}%)")
    print(f"   ✓ Saved to: {csv_path}")
    print()
    
    # Step 4: Verify setup
    print("✅ Verification...")
    try:
        total_scores = db.get_total_scores()
        metrics = db.get_system_metrics()
        print(f"   ✓ Database connection: OK")
        print(f"   ✓ System metrics initialized: {len(metrics)} metrics")
        print()
    except Exception as e:
        print(f"   ✗ Database verification failed: {e}")
        return False
    
    print("=" * 60)
    print("🚀 Setup Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Review .env.example and create .env if needed")
    print("  2. Start the API server:")
    print("     python run.py")
    print("  3. Access API documentation:")
    print(f"     http://{settings.api_host}:{settings.api_port}/docs")
    print()
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
