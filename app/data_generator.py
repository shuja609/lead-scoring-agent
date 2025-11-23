"""
Lead Scoring Agent - Synthetic Data Generator
Generate realistic training data using Faker
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from faker import Faker

fake = Faker()


class SyntheticDataGenerator:
    """Generate realistic lead data for training"""
    
    # Predefined categories for consistency
    LOCATIONS = [
        "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
        "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose",
        "Austin", "Seattle", "Denver", "Boston", "Miami"
    ]
    
    INDUSTRIES = [
        "Technology", "Healthcare", "Finance", "Retail", "Manufacturing",
        "Education", "Real Estate", "Consulting", "Media", "Telecommunications"
    ]
    
    LEAD_SOURCES = [
        "Webinar", "Cold Call", "Referral", "Advertisement", 
        "Organic", "Trade Show", "Email Campaign"
    ]
    
    def __init__(self, seed: int = 42):
        """Initialize generator with optional seed for reproducibility"""
        Faker.seed(seed)
        random.seed(seed)
    
    def _generate_engagement_pattern(self, will_convert: bool) -> Dict[str, int]:
        """
        Generate realistic engagement metrics based on conversion likelihood
        Converted leads tend to have higher engagement
        """
        if will_convert:
            # Higher engagement for converted leads
            email_opens = random.randint(10, 30)
            website_visits = random.randint(8, 20)
            content_downloads = random.randint(3, 10)
            days_since_contact = random.randint(1, 30)
        else:
            # Lower engagement for non-converted leads
            email_opens = random.randint(0, 15)
            website_visits = random.randint(0, 10)
            content_downloads = random.randint(0, 5)
            days_since_contact = random.randint(1, 90)
        
        return {
            "email_opens": email_opens,
            "website_visits": website_visits,
            "content_downloads": content_downloads,
            "days_since_contact": days_since_contact
        }
    
    def _generate_demographics(self) -> Dict[str, Any]:
        """Generate demographic information"""
        return {
            "age": random.randint(22, 65),
            "location": random.choice(self.LOCATIONS),
            "industry": random.choice(self.INDUSTRIES)
        }
    
    def generate_lead(self, lead_id: str = None, converted: bool = None) -> Dict[str, Any]:
        """
        Generate a single synthetic lead
        
        Args:
            lead_id: Optional specific lead ID (auto-generated if None)
            converted: Optional conversion outcome (random if None)
        
        Returns:
            Dictionary with complete lead data
        """
        if lead_id is None:
            lead_id = f"LEAD-{fake.uuid4()[:8].upper()}"
        
        if converted is None:
            # 40% conversion rate for balanced dataset
            converted = random.random() < 0.40
        
        demographics = self._generate_demographics()
        engagement = self._generate_engagement_pattern(converted)
        
        return {
            "lead_id": lead_id,
            "age": demographics["age"],
            "location": demographics["location"],
            "industry": demographics["industry"],
            "email_opens": engagement["email_opens"],
            "website_visits": engagement["website_visits"],
            "content_downloads": engagement["content_downloads"],
            "days_since_contact": engagement["days_since_contact"],
            "lead_source": random.choice(self.LEAD_SOURCES),
            "converted": converted
        }
    
    def generate_dataset(self, size: int = 1000) -> List[Dict[str, Any]]:
        """
        Generate a complete synthetic dataset
        
        Args:
            size: Number of leads to generate (default 1000)
        
        Returns:
            List of lead dictionaries
        """
        leads = []
        
        # Generate balanced dataset (40% converted, 60% not converted)
        converted_count = int(size * 0.40)
        not_converted_count = size - converted_count
        
        # Generate converted leads
        for i in range(converted_count):
            lead = self.generate_lead(
                lead_id=f"LEAD-CONV-{i+1:04d}",
                converted=True
            )
            leads.append(lead)
        
        # Generate non-converted leads
        for i in range(not_converted_count):
            lead = self.generate_lead(
                lead_id=f"LEAD-NCON-{i+1:04d}",
                converted=False
            )
            leads.append(lead)
        
        # Shuffle to mix converted and non-converted
        random.shuffle(leads)
        
        return leads
    
    def save_to_csv(self, leads: List[Dict[str, Any]], filename: str = "synthetic_leads.csv") -> None:
        """
        Save generated leads to CSV file
        
        Args:
            leads: List of lead dictionaries
            filename: Output CSV filename
        """
        import csv
        
        if not leads:
            return
        
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=leads[0].keys())
            writer.writeheader()
            writer.writerows(leads)
    
    @staticmethod
    def get_feature_names() -> List[str]:
        """Return list of feature names for ML pipeline"""
        return [
            "age", "location", "industry", "email_opens",
            "website_visits", "content_downloads", "days_since_contact",
            "lead_source"
        ]
    
    @staticmethod
    def get_categorical_features() -> List[str]:
        """Return list of categorical feature names"""
        return ["location", "industry", "lead_source"]
    
    @staticmethod
    def get_numeric_features() -> List[str]:
        """Return list of numeric feature names"""
        return [
            "age", "email_opens", "website_visits", 
            "content_downloads", "days_since_contact"
        ]


def main():
    """Generate and save synthetic dataset"""
    print("Generating synthetic lead dataset...")
    generator = SyntheticDataGenerator(seed=42)
    leads = generator.generate_dataset(size=1000)
    
    # Save to CSV
    generator.save_to_csv(leads, "data/synthetic_leads.csv")
    
    # Print statistics
    converted = sum(1 for lead in leads if lead["converted"])
    print(f"✓ Generated {len(leads)} leads")
    print(f"✓ Converted: {converted} ({converted/len(leads)*100:.1f}%)")
    print(f"✓ Not Converted: {len(leads)-converted} ({(len(leads)-converted)/len(leads)*100:.1f}%)")
    print(f"✓ Saved to data/synthetic_leads.csv")


if __name__ == "__main__":
    main()
