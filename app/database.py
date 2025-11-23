"""
Lead Scoring Agent - Database Layer
SQLite schema and operations for persistence
"""

import sqlite3
import pickle
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

from app.config import settings


class Database:
    """SQLite database manager for lead scoring agent"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.database_path
        self._ensure_database_exists()
    
    def _ensure_database_exists(self) -> None:
        """Create database directory if it doesn't exist"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def initialize_schema(self) -> None:
        """Create all database tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Table 1: lead_scores - Primary storage for leads and scores
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lead_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id TEXT UNIQUE NOT NULL,
                    age INTEGER,
                    location TEXT,
                    industry TEXT,
                    email_opens INTEGER,
                    website_visits INTEGER,
                    content_downloads INTEGER,
                    days_since_contact INTEGER,
                    lead_source TEXT,
                    conversion_score REAL NOT NULL,
                    risk_category TEXT NOT NULL,
                    actual_outcome INTEGER,
                    model_version TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_lead_id 
                ON lead_scores(lead_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON lead_scores(timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_actual_outcome 
                ON lead_scores(actual_outcome)
            """)
            
            # Table 2: models - Model version management
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS models (
                    version TEXT PRIMARY KEY,
                    model_blob BLOB NOT NULL,
                    auc_score REAL,
                    precision_top20 REAL,
                    recall_top20 REAL,
                    training_samples INTEGER,
                    training_timestamp TEXT NOT NULL,
                    active INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table 3: system_metrics - Aggregate statistics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    metric_key TEXT PRIMARY KEY,
                    metric_value TEXT NOT NULL,
                    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Initialize system metrics if empty
            cursor.execute("SELECT COUNT(*) as count FROM system_metrics")
            if cursor.fetchone()["count"] == 0:
                now = datetime.utcnow().isoformat()
                metrics = [
                    ("total_scores", "0", now),
                    ("feedback_count", "0", now),
                    ("last_training", "never", now)
                ]
                cursor.executemany(
                    "INSERT INTO system_metrics (metric_key, metric_value, last_updated) VALUES (?, ?, ?)",
                    metrics
                )
    
    def insert_lead_score(self, lead_data: Dict[str, Any]) -> int:
        """Insert or update a lead score record (upsert on lead_id)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO lead_scores (
                    lead_id, age, location, industry, email_opens, 
                    website_visits, content_downloads, days_since_contact,
                    lead_source, conversion_score, risk_category, 
                    actual_outcome, model_version, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lead_data["lead_id"],
                lead_data["age"],
                lead_data["location"],
                lead_data["industry"],
                lead_data["email_opens"],
                lead_data["website_visits"],
                lead_data["content_downloads"],
                lead_data["days_since_contact"],
                lead_data["lead_source"],
                lead_data["conversion_score"],
                lead_data["risk_category"],
                lead_data.get("actual_outcome"),
                lead_data["model_version"],
                lead_data["timestamp"]
            ))
            return cursor.lastrowid
    
    def update_lead_outcome(self, lead_id: str, actual_outcome: bool) -> bool:
        """Update actual conversion outcome for a lead"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE lead_scores 
                SET actual_outcome = ? 
                WHERE lead_id = ?
            """, (1 if actual_outcome else 0, lead_id))
            return cursor.rowcount > 0
    
    def get_feedback_count(self) -> int:
        """Get count of leads with actual outcomes"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM lead_scores 
                WHERE actual_outcome IS NOT NULL
            """)
            return cursor.fetchone()["count"]
    
    def get_training_data(self) -> List[Dict[str, Any]]:
        """Retrieve all leads with actual outcomes for training"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT lead_id, age, location, industry, email_opens,
                       website_visits, content_downloads, days_since_contact,
                       lead_source, actual_outcome
                FROM lead_scores
                WHERE actual_outcome IS NOT NULL
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_feedback_leads(self) -> List[Dict[str, Any]]:
        """Retrieve all leads with actual outcomes (alias for get_training_data)"""
        return self.get_training_data()
    
    def save_model(self, version: str, model_obj: Any, metrics: Dict[str, Any]) -> None:
        """Save a trained model to database"""
        model_blob = pickle.dumps(model_obj)
        timestamp = datetime.utcnow().isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO models (
                    version, model_blob, auc_score, precision_top20,
                    recall_top20, training_samples, training_timestamp, active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                version,
                model_blob,
                metrics.get("auc_score"),
                metrics.get("precision_top20"),
                metrics.get("recall_top20"),
                metrics.get("training_samples"),
                timestamp,
                1 if metrics.get("active", False) else 0
            ))
    
    def get_active_model(self) -> Optional[tuple]:
        """Retrieve the active model and its metadata"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT version, model_blob, auc_score, training_timestamp
                FROM models
                WHERE active = 1
                ORDER BY training_timestamp DESC
                LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                model_obj = pickle.loads(row["model_blob"])
                return (model_obj, dict(row))
            return None
    
    def set_active_model(self, version: str) -> None:
        """Mark a model version as active (deactivates others)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Deactivate all models
            cursor.execute("UPDATE models SET active = 0")
            # Activate specified version
            cursor.execute(
                "UPDATE models SET active = 1 WHERE version = ?",
                (version,)
            )
    
    def deactivate_all_models(self) -> None:
        """Deactivate all models"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE models SET active = 0")
    
    def get_total_scores(self) -> int:
        """Get total number of leads scored"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM lead_scores")
            return cursor.fetchone()["count"]
    
    def update_system_metric(self, key: str, value: str) -> None:
        """Update a system metric value"""
        timestamp = datetime.utcnow().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO system_metrics (metric_key, metric_value, last_updated)
                VALUES (?, ?, ?)
            """, (key, value, timestamp))
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Retrieve all system metrics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT metric_key, metric_value FROM system_metrics")
            return {row["metric_key"]: row["metric_value"] for row in cursor.fetchall()}
    
    def get_model_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the active model"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT version, auc_score, precision_top20, recall_top20,
                       training_samples, training_timestamp
                FROM models
                WHERE active = 1
                ORDER BY training_timestamp DESC
                LIMIT 1
            """)
            row = cursor.fetchone()
            return dict(row) if row else None


# Global database instance
db = Database()
