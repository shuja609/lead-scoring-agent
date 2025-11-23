"""
Lead Scoring Agent - ML Model Training
Train and evaluate Logistic Regression model
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    roc_auc_score,
    precision_score,
    recall_score,
    classification_report,
    roc_curve
)
import pickle
from datetime import datetime

from app.features import FeatureEngineer, create_training_dataframe
from app.data_generator import SyntheticDataGenerator
from app.database import db
from app.config import settings


class ModelTrainer:
    """Train and evaluate lead scoring model"""
    
    def __init__(self):
        self.model = None
        self.feature_engineer = None
        self.metrics = {}
        self.training_timestamp = None
    
    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Dict[str, Any]:
        """
        Train Logistic Regression model
        
        Args:
            X: Feature DataFrame
            y: Target Series
            test_size: Test set proportion
            random_state: Random seed
        
        Returns:
            Dictionary of evaluation metrics
        """
        print(f"\n📊 Training model on {len(X)} samples...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        print(f"   Train set: {len(X_train)} samples")
        print(f"   Test set: {len(X_test)} samples")
        
        # Initialize feature engineer
        self.feature_engineer = FeatureEngineer()
        X_train_transformed = self.feature_engineer.fit_transform(X_train)
        X_test_transformed = self.feature_engineer.transform(X_test)
        
        print(f"   Features: {X_train_transformed.shape[1]} dimensions")
        
        # Train Logistic Regression
        self.model = LogisticRegression(
            max_iter=1000,
            random_state=random_state,
            class_weight='balanced'  # Handle class imbalance
        )
        
        self.model.fit(X_train_transformed, y_train)
        print("   ✓ Model trained")
        
        # Predictions
        y_pred = self.model.predict(X_test_transformed)
        y_pred_proba = self.model.predict_proba(X_test_transformed)[:, 1]
        
        # Calculate metrics
        auc_score = roc_auc_score(y_test, y_pred_proba)
        
        # Precision and Recall at top 20%
        threshold_20 = np.percentile(y_pred_proba, 80)  # Top 20%
        y_pred_top20 = (y_pred_proba >= threshold_20).astype(int)
        
        precision_top20 = precision_score(y_test, y_pred_top20, zero_division=0)
        recall_top20 = recall_score(y_test, y_pred_top20, zero_division=0)
        
        # Cross-validation score
        cv_scores = cross_val_score(
            self.model, X_train_transformed, y_train,
            cv=5, scoring='roc_auc'
        )
        
        self.metrics = {
            'auc_score': float(auc_score),
            'precision_top20': float(precision_top20),
            'recall_top20': float(recall_top20),
            'cv_mean_auc': float(cv_scores.mean()),
            'cv_std_auc': float(cv_scores.std()),
            'training_samples': len(X_train),
            'test_samples': len(X_test),
            'n_features': X_train_transformed.shape[1]
        }
        
        self.training_timestamp = datetime.utcnow().isoformat()
        
        # Print results
        print(f"\n   📈 Model Performance:")
        print(f"      AUC Score: {auc_score:.4f}")
        print(f"      CV Mean AUC: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
        print(f"      Precision @ Top 20%: {precision_top20:.4f}")
        print(f"      Recall @ Top 20%: {recall_top20:.4f}")
        
        # Target check
        target_auc = settings.target_auc
        if auc_score >= target_auc:
            print(f"      ✅ Target AUC ({target_auc}) achieved!")
        else:
            print(f"      ⚠️  Below target AUC ({target_auc})")
        
        return self.metrics
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict conversion probability for leads
        
        Args:
            X: Feature DataFrame
        
        Returns:
            Array of probabilities
        """
        if self.model is None or self.feature_engineer is None:
            raise ValueError("Model must be trained before prediction")
        
        X_transformed = self.feature_engineer.transform(X)
        return self.model.predict_proba(X_transformed)[:, 1]
    
    def predict_single(self, lead: Dict[str, Any]) -> float:
        """
        Predict conversion probability for a single lead
        
        Args:
            lead: Dictionary with lead data
        
        Returns:
            Conversion probability (0-1)
        """
        X = self.feature_engineer.prepare_lead_data(lead)
        return float(self.predict_proba(X)[0])
    
    def save_to_database(self, version: str) -> None:
        """
        Save model and feature engineer to database
        
        Args:
            version: Model version string
        """
        if self.model is None or self.feature_engineer is None:
            raise ValueError("Model must be trained before saving")
        
        # Package model with feature engineer
        model_package = {
            'model': self.model,
            'feature_engineer': self.feature_engineer,
            'metrics': self.metrics,
            'training_timestamp': self.training_timestamp
        }
        
        # Save to database
        db.save_model(
            version=version,
            model_obj=model_package,
            metrics={
                'auc_score': self.metrics['auc_score'],
                'precision_top20': self.metrics['precision_top20'],
                'recall_top20': self.metrics['recall_top20'],
                'training_samples': self.metrics['training_samples'],
                'active': True
            }
        )
        
        # Set as active model
        db.set_active_model(version)
        
        # Update system metrics
        db.update_system_metric('last_training', self.training_timestamp)
        
        print(f"\n   ✓ Model saved to database (version: {version})")
    
    @staticmethod
    def load_from_database() -> Optional[Tuple[Any, FeatureEngineer, Dict[str, Any]]]:
        """
        Load active model from database
        
        Returns:
            Tuple of (model, feature_engineer, metadata) or None
        """
        result = db.get_active_model()
        if result is None:
            return None
        
        model_package, metadata = result
        
        return (
            model_package['model'],
            model_package['feature_engineer'],
            {
                'version': metadata['version'],
                'auc_score': metadata['auc_score'],
                'training_timestamp': metadata['training_timestamp']
            }
        )


def train_initial_model(save_to_db: bool = True) -> ModelTrainer:
    """
    Train initial model on synthetic data
    
    Args:
        save_to_db: Whether to save model to database
    
    Returns:
        Trained ModelTrainer instance
    """
    print("=" * 60)
    print("Training Initial Lead Scoring Model")
    print("=" * 60)
    
    # Generate synthetic training data
    print("\n🎲 Generating synthetic training data...")
    generator = SyntheticDataGenerator(seed=42)
    leads = generator.generate_dataset(size=1000)
    print(f"   ✓ Generated {len(leads)} leads")
    
    # Create training dataframe
    X, y = create_training_dataframe(leads)
    print(f"   ✓ Conversion rate: {y.mean():.1%}")
    
    # Train model
    trainer = ModelTrainer()
    metrics = trainer.train(X, y)
    
    # Save to database
    if save_to_db:
        version = f"{settings.model_version}"
        trainer.save_to_database(version)
    
    print("\n" + "=" * 60)
    print("Model Training Complete! ✅")
    print("=" * 60)
    
    return trainer


def retrain_model(feedback_data: pd.DataFrame, current_auc: float) -> Optional[ModelTrainer]:
    """
    Retrain model with feedback data
    
    Args:
        feedback_data: DataFrame with actual outcomes
        current_auc: Current model's AUC score
    
    Returns:
        New ModelTrainer if improved, None otherwise
    """
    print("=" * 60)
    print("Retraining Model with Feedback")
    print("=" * 60)
    
    print(f"\n📊 Feedback samples: {len(feedback_data)}")
    print(f"   Current AUC: {current_auc:.4f}")
    
    # Prepare features and target
    X, y = create_training_dataframe(feedback_data.to_dict('records'))
    
    # Train new model
    trainer = ModelTrainer()
    metrics = trainer.train(X, y)
    
    # Check if improved
    improvement = metrics['auc_score'] - current_auc
    improvement_threshold = settings.accuracy_improvement_threshold
    
    print(f"\n   Improvement: {improvement:+.4f}")
    print(f"   Threshold: {improvement_threshold:.4f}")
    
    if improvement >= improvement_threshold:
        print(f"   ✅ Model improved! Deploying new version...")
        return trainer
    else:
        print(f"   ⚠️  Insufficient improvement. Keeping current model.")
        return None


def main():
    """Train and test initial model"""
    # Train model
    trainer = train_initial_model(save_to_db=True)
    
    # Test prediction on sample lead
    print("\n" + "=" * 60)
    print("Testing Prediction")
    print("=" * 60)
    
    test_lead = {
        'age': 35,
        'location': 'New York',
        'industry': 'Technology',
        'email_opens': 20,
        'website_visits': 15,
        'content_downloads': 7,
        'days_since_contact': 5,
        'lead_source': 'Webinar'
    }
    
    score = trainer.predict_single(test_lead)
    print(f"\nTest Lead Score: {score:.4f}")
    
    # Load from database and test
    print("\n" + "=" * 60)
    print("Testing Database Load")
    print("=" * 60)
    
    loaded = ModelTrainer.load_from_database()
    if loaded:
        model, feature_engineer, metadata = loaded
        print(f"\n✓ Loaded model version: {metadata['version']}")
        print(f"✓ AUC Score: {metadata['auc_score']:.4f}")
        print(f"✓ Trained: {metadata['training_timestamp']}")
    
    print("\n" + "=" * 60)
    print("All Tests Passed! ✅")
    print("=" * 60)


if __name__ == "__main__":
    main()
