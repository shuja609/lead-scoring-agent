"""
Lead Scoring Agent - Feature Engineering Pipeline
Transform raw lead data into ML-ready features
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
import pickle


class FeatureEngineer:
    """Feature engineering pipeline for lead scoring"""
    
    def __init__(self):
        self.preprocessor = None
        self.feature_names = None
        self._is_fitted = False
    
    @staticmethod
    def get_numeric_features() -> List[str]:
        """Return list of numeric feature names"""
        return [
            'age',
            'email_opens',
            'website_visits',
            'content_downloads',
            'days_since_contact'
        ]
    
    @staticmethod
    def get_categorical_features() -> List[str]:
        """Return list of categorical feature names"""
        return ['location', 'industry', 'lead_source']
    
    @staticmethod
    def engineer_derived_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        Create derived features from raw data
        
        Derived features:
        - engagement_intensity: total engagement score
        - recency_weight: inverse of days since contact (recent = higher)
        - interaction_frequency: average interactions per metric
        """
        df = df.copy()
        
        # Engagement intensity (weighted sum of interactions)
        df['engagement_intensity'] = (
            df['email_opens'] * 0.3 +
            df['website_visits'] * 0.4 +
            df['content_downloads'] * 0.3
        )
        
        # Recency weight (more recent = higher weight)
        # Use exponential decay: e^(-days/30)
        df['recency_weight'] = np.exp(-df['days_since_contact'] / 30)
        
        # Interaction frequency (average per action type)
        df['interaction_frequency'] = (
            df['email_opens'] + 
            df['website_visits'] + 
            df['content_downloads']
        ) / 3.0
        
        return df
    
    def create_preprocessor(self) -> ColumnTransformer:
        """
        Create sklearn ColumnTransformer for feature preprocessing
        
        Numeric features: StandardScaler (z-score normalization)
        Categorical features: OneHotEncoder (binary encoding)
        """
        numeric_features = self.get_numeric_features()
        
        # Add derived features to numeric list
        derived_features = [
            'engagement_intensity',
            'recency_weight',
            'interaction_frequency'
        ]
        
        all_numeric = numeric_features + derived_features
        categorical_features = self.get_categorical_features()
        
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', StandardScaler(), all_numeric),
                ('cat', OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore'), 
                 categorical_features)
            ],
            remainder='drop'
        )
        
        return preprocessor
    
    def fit(self, X: pd.DataFrame) -> 'FeatureEngineer':
        """
        Fit the feature engineering pipeline
        
        Args:
            X: DataFrame with raw features
        
        Returns:
            self (for method chaining)
        """
        # Engineer derived features
        X_engineered = self.engineer_derived_features(X)
        
        # Create and fit preprocessor
        self.preprocessor = self.create_preprocessor()
        self.preprocessor.fit(X_engineered)
        
        # Store feature names after transformation
        self._extract_feature_names()
        self._is_fitted = True
        
        return self
    
    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """
        Transform raw features into ML-ready features
        
        Args:
            X: DataFrame with raw features
        
        Returns:
            numpy array of transformed features
        """
        if not self._is_fitted:
            raise ValueError("FeatureEngineer must be fitted before transform")
        
        # Engineer derived features
        X_engineered = self.engineer_derived_features(X)
        
        # Apply preprocessing
        X_transformed = self.preprocessor.transform(X_engineered)
        
        return X_transformed
    
    def fit_transform(self, X: pd.DataFrame) -> np.ndarray:
        """
        Fit and transform in one step
        
        Args:
            X: DataFrame with raw features
        
        Returns:
            numpy array of transformed features
        """
        return self.fit(X).transform(X)
    
    def _extract_feature_names(self) -> None:
        """Extract feature names after transformation"""
        feature_names = []
        
        # Numeric features (original + derived)
        numeric_features = self.get_numeric_features()
        derived_features = [
            'engagement_intensity',
            'recency_weight',
            'interaction_frequency'
        ]
        feature_names.extend(numeric_features + derived_features)
        
        # Categorical features (one-hot encoded)
        cat_encoder = self.preprocessor.named_transformers_['cat']
        for i, feature in enumerate(self.get_categorical_features()):
            categories = cat_encoder.categories_[i][1:]  # Skip first (dropped)
            feature_names.extend([f"{feature}_{cat}" for cat in categories])
        
        self.feature_names = feature_names
    
    def get_feature_names(self) -> List[str]:
        """Get names of all transformed features"""
        if not self._is_fitted:
            raise ValueError("FeatureEngineer must be fitted first")
        return self.feature_names
    
    def prepare_lead_data(self, lead: Dict[str, Any]) -> pd.DataFrame:
        """
        Prepare a single lead for prediction
        
        Args:
            lead: Dictionary with lead data
        
        Returns:
            DataFrame with single row ready for transformation
        """
        # Extract relevant fields
        data = {
            'age': lead['age'],
            'location': lead['location'],
            'industry': lead['industry'],
            'email_opens': lead['email_opens'],
            'website_visits': lead['website_visits'],
            'content_downloads': lead['content_downloads'],
            'days_since_contact': lead['days_since_contact'],
            'lead_source': lead['lead_source']
        }
        
        return pd.DataFrame([data])
    
    def save(self, filepath: str) -> None:
        """Save fitted feature engineer to disk"""
        if not self._is_fitted:
            raise ValueError("Cannot save unfitted FeatureEngineer")
        
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)
    
    @staticmethod
    def load(filepath: str) -> 'FeatureEngineer':
        """Load fitted feature engineer from disk"""
        with open(filepath, 'rb') as f:
            return pickle.load(f)


def create_training_dataframe(leads: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Convert list of lead dictionaries to DataFrame for training
    
    Args:
        leads: List of lead dictionaries with 'converted' field
    
    Returns:
        Tuple of (X: features DataFrame, y: target Series)
    """
    df = pd.DataFrame(leads)
    
    # Separate features and target
    feature_columns = [
        'age', 'location', 'industry', 'email_opens',
        'website_visits', 'content_downloads', 'days_since_contact',
        'lead_source'
    ]
    
    X = df[feature_columns]
    y = df['converted'].astype(int)
    
    return X, y


def main():
    """Test feature engineering pipeline"""
    from app.data_generator import SyntheticDataGenerator
    
    print("Testing Feature Engineering Pipeline...")
    print("=" * 60)
    
    # Generate sample data
    generator = SyntheticDataGenerator(seed=42)
    leads = generator.generate_dataset(size=100)
    
    # Create training data
    X, y = create_training_dataframe(leads)
    print(f"\n✓ Created training data: {X.shape}")
    print(f"✓ Target distribution: {y.value_counts().to_dict()}")
    
    # Initialize and fit feature engineer
    engineer = FeatureEngineer()
    X_transformed = engineer.fit_transform(X)
    
    print(f"\n✓ Transformed features shape: {X_transformed.shape}")
    print(f"✓ Number of features: {len(engineer.get_feature_names())}")
    print(f"\n✓ Feature names:")
    for i, name in enumerate(engineer.get_feature_names()[:10]):
        print(f"   {i+1}. {name}")
    if len(engineer.get_feature_names()) > 10:
        print(f"   ... and {len(engineer.get_feature_names()) - 10} more")
    
    # Test single lead transformation
    test_lead = leads[0]
    X_single = engineer.prepare_lead_data(test_lead)
    X_single_transformed = engineer.transform(X_single)
    
    print(f"\n✓ Single lead transformation: {X_single_transformed.shape}")
    
    print("\n" + "=" * 60)
    print("Feature Engineering Pipeline Test: PASSED ✅")


if __name__ == "__main__":
    main()
