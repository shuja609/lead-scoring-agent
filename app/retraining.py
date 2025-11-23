"""
Lead Scoring Agent - Automatic Retraining System
Background task for model retraining and deployment
"""

import threading
import time
from typing import Optional
from datetime import datetime
import pandas as pd

from app.database import db
from app.model import ModelTrainer, retrain_model
from app.features import create_training_dataframe
from app.config import settings
from app.workflow import clear_model_cache


class RetrainingManager:
    """Manages automatic model retraining"""
    
    def __init__(self):
        self.is_retraining = False
        self.last_check_time = None
        self.last_retrain_time = None
        self.retrain_lock = threading.Lock()
    
    def check_and_retrain(self) -> Optional[dict]:
        """
        Check if retraining is needed and execute if so
        
        Returns:
            Dictionary with retraining results or None
        """
        with self.retrain_lock:
            if self.is_retraining:
                return {
                    'status': 'already_retraining',
                    'message': 'Retraining already in progress'
                }
            
            self.last_check_time = datetime.utcnow().isoformat()
            
            # Check feedback count
            feedback_count = db.get_feedback_count()
            threshold = settings.retraining_threshold
            
            if feedback_count < threshold:
                return {
                    'status': 'insufficient_feedback',
                    'feedback_count': feedback_count,
                    'threshold': threshold,
                    'message': f'Need {threshold - feedback_count} more feedback samples'
                }
            
            # Get current model
            current_model_data = ModelTrainer.load_from_database()
            if current_model_data is None:
                return {
                    'status': 'error',
                    'message': 'No current model found'
                }
            
            _, _, current_metadata = current_model_data
            current_auc = current_metadata['auc_score']
            current_version = current_metadata['version']
            
            # Start retraining
            self.is_retraining = True
            try:
                result = self._execute_retraining(
                    feedback_count, current_version, current_auc
                )
                self.last_retrain_time = datetime.utcnow().isoformat()
                return result
            finally:
                self.is_retraining = False
    
    def _execute_retraining(
        self, feedback_count: int, current_version: str, current_auc: float
    ) -> dict:
        """
        Execute the retraining process
        
        Args:
            feedback_count: Number of feedback samples
            current_version: Current model version
            current_auc: Current model AUC score
        
        Returns:
            Dictionary with retraining results
        """
        print(f"\n{'='*70}")
        print(f"🔄 AUTOMATIC RETRAINING TRIGGERED")
        print(f"{'='*70}")
        print(f"Feedback samples: {feedback_count}")
        print(f"Current model: {current_version} (AUC: {current_auc:.4f})")
        print(f"Threshold: {settings.retraining_threshold}")
        
        # Get all feedback data
        feedback_leads = db.get_feedback_leads()
        
        if len(feedback_leads) == 0:
            return {
                'status': 'error',
                'message': 'No feedback data available'
            }
        
        print(f"\nLoaded {len(feedback_leads)} feedback samples from database")
        
        # Convert to DataFrame for training
        feedback_df = pd.DataFrame(feedback_leads)
        
        # Rename actual_outcome to converted for training
        if 'actual_outcome' in feedback_df.columns:
            feedback_df['converted'] = feedback_df['actual_outcome']
        
        # Retrain model
        new_trainer = retrain_model(feedback_df, current_auc)
        
        if new_trainer is None:
            # Model did not improve sufficiently
            return {
                'status': 'no_improvement',
                'feedback_count': feedback_count,
                'current_version': current_version,
                'current_auc': current_auc,
                'message': f'New model did not meet improvement threshold ({settings.accuracy_improvement_threshold})'
            }
        
        # Model improved - deploy new version
        new_version = self._generate_version(current_version)
        new_auc = new_trainer.metrics['auc_score']
        
        print(f"\n{'='*70}")
        print(f"✅ MODEL IMPROVED - DEPLOYING NEW VERSION")
        print(f"{'='*70}")
        print(f"New version: {new_version}")
        print(f"AUC improvement: {current_auc:.4f} → {new_auc:.4f} ({new_auc - current_auc:+.4f})")
        
        # Deactivate old model
        db.deactivate_all_models()
        
        # Save new model
        new_trainer.save_to_database(new_version)
        
        # Clear model cache to force reload
        clear_model_cache()
        
        # Update system metrics
        db.update_system_metric('last_retraining', datetime.utcnow().isoformat())
        db.update_system_metric('model_version', new_version)
        
        print(f"\n✅ Deployment complete!\n")
        
        return {
            'status': 'success',
            'old_version': current_version,
            'new_version': new_version,
            'old_auc': current_auc,
            'new_auc': new_auc,
            'improvement': new_auc - current_auc,
            'feedback_count': feedback_count,
            'timestamp': datetime.utcnow().isoformat(),
            'message': f'Model upgraded from {current_version} to {new_version}'
        }
    
    def _generate_version(self, current_version: str) -> str:
        """
        Generate new version number
        
        Args:
            current_version: Current version string (e.g., "1.0")
        
        Returns:
            New version string (e.g., "1.1")
        """
        try:
            major, minor = current_version.split('.')
            new_minor = int(minor) + 1
            return f"{major}.{new_minor}"
        except Exception:
            # Fallback to timestamp-based version
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            return f"1.{timestamp}"
    
    def trigger_background_retraining(self) -> None:
        """Trigger retraining in a background thread"""
        def _background_task():
            result = self.check_and_retrain()
            if result:
                status = result.get('status')
                if status == 'success':
                    print(f"✅ Background retraining completed: {result.get('new_version')}")
                elif status == 'no_improvement':
                    print(f"⚠️  Background retraining: No improvement")
                elif status == 'insufficient_feedback':
                    print(f"ℹ️  Background retraining: Insufficient feedback ({result.get('feedback_count')}/{result.get('threshold')})")
        
        thread = threading.Thread(target=_background_task, daemon=True)
        thread.start()
    
    def get_status(self) -> dict:
        """
        Get current retraining status
        
        Returns:
            Dictionary with status information
        """
        feedback_count = db.get_feedback_count()
        threshold = settings.retraining_threshold
        
        return {
            'is_retraining': self.is_retraining,
            'feedback_count': feedback_count,
            'retraining_threshold': threshold,
            'ready_for_retraining': feedback_count >= threshold,
            'last_check_time': self.last_check_time,
            'last_retrain_time': self.last_retrain_time
        }


# Global retraining manager instance
retraining_manager = RetrainingManager()
