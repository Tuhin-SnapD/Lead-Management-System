"""
Machine Learning Service for Lead Scoring

This module provides machine learning-based lead scoring functionality
using scikit-learn to predict lead conversion probability.
"""

import os
import pickle
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
from django.conf import settings
from django.utils import timezone
from django.db.models import Q, Count, Avg

from .models import Lead, LeadInteraction, Category, MLTrainingSession

logger = logging.getLogger(__name__)


class LeadScoringService:
    """
    Service for machine learning-based lead scoring.
    """
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.label_encoders = {}
        self.model_path = os.path.join(settings.ML_MODEL_PATH, 'lead_scoring_model.pkl')
        self.scaler_path = os.path.join(settings.ML_MODEL_PATH, 'lead_scoring_scaler.pkl')
        self.encoders_path = os.path.join(settings.ML_MODEL_PATH, 'lead_scoring_encoders.pkl')
        
    def prepare_features(self, leads: List[Lead]) -> pd.DataFrame:
        """
        Prepare features for machine learning model.
        
        Args:
            leads: List of Lead objects
            
        Returns:
            DataFrame with features
        """
        features = []
        
        for lead in leads:
            # Basic lead features
            lead_data = {
                'age': lead.age,
                'interaction_count': lead.interaction_count,
                'lead_score': lead.lead_score,
                'days_since_created': (timezone.now() - lead.date_added).days,
                'days_since_last_contact': (
                    (timezone.now() - lead.last_contacted).days 
                    if lead.last_contacted else 999
                ),
                'has_follow_up': 1 if lead.follow_up_date else 0,
                'is_snoozed': 1 if lead.is_snoozed else 0,
            }
            
            # Categorical features
            lead_data['engagement_level'] = lead.engagement_level
            lead_data['source'] = lead.source or 'unknown'
            lead_data['has_agent'] = 1 if lead.agent else 0
            lead_data['has_category'] = 1 if lead.category else 0
            
            # Interaction features
            interactions = lead.interactions.all()
            lead_data['total_interactions'] = interactions.count()
            lead_data['positive_interactions'] = interactions.filter(outcome='positive').count()
            lead_data['negative_interactions'] = interactions.filter(outcome='negative').count()
            lead_data['avg_interaction_duration'] = interactions.aggregate(
                avg_duration=Avg('duration_minutes')
            )['avg_duration'] or 0
            
            features.append(lead_data)
        
        return pd.DataFrame(features)
    
    def prepare_target(self, leads: List[Lead]) -> np.ndarray:
        """
        Prepare target variable (conversion) for training.
        
        Args:
            leads: List of Lead objects
            
        Returns:
            Array of target values (1 for converted, 0 for not converted)
        """
        targets = []
        for lead in leads:
            # Consider a lead converted if it's in a category with 'converted' in the name
            is_converted = (
                lead.category and 
                'converted' in lead.category.name.lower()
            )
            targets.append(1 if is_converted else 0)
        
        return np.array(targets)
    
    def encode_categorical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Encode categorical features using LabelEncoder.
        
        Args:
            df: DataFrame with features
            
        Returns:
            DataFrame with encoded features
        """
        categorical_columns = ['engagement_level', 'source']
        
        for column in categorical_columns:
            if column in df.columns:
                le = LabelEncoder()
                df[column] = le.fit_transform(df[column].astype(str))
                self.label_encoders[column] = le
        
        return df
    
    def train_model(self, organisation_id: int) -> Dict[str, float]:
        """
        Train the lead scoring model for a specific organization.
        
        Args:
            organisation_id: ID of the organization
            
        Returns:
            Dictionary with training metrics
        """
        try:
            # Get leads for the organization
            leads = Lead.objects.filter(
                organisation_id=organisation_id
            ).prefetch_related('interactions', 'category', 'agent')
            
            if len(leads) < 50:
                logger.warning(f"Insufficient data for training: {len(leads)} leads")
                return {'error': 'Insufficient data for training (minimum 50 leads required)'}
            
            # Prepare features and target
            X = self.prepare_features(leads)
            y = self.prepare_target(leads)
            
            # Encode categorical features
            X = self.encode_categorical_features(X)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            self.scaler = StandardScaler()
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            )
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            y_pred = self.model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Save model
            self.save_model()
            
            # Record training session
            MLTrainingSession.objects.create(
                organisation_id=organisation_id,
                accuracy=accuracy,
                training_samples=len(X_train),
                test_samples=len(X_test),
                status='success'
            )
            
            logger.info(f"Model trained successfully with accuracy: {accuracy:.3f}")
            
            return {
                'accuracy': accuracy,
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'feature_importance': dict(zip(X.columns, self.model.feature_importances_))
            }
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            
            # Record failed training session
            try:
                MLTrainingSession.objects.create(
                    organisation_id=organisation_id,
                    accuracy=0.0,
                    training_samples=0,
                    test_samples=0,
                    status='failed',
                    error_message=str(e)
                )
            except:
                pass  # Don't let recording failure break the main error handling
            
            return {'error': str(e)}
    
    def predict_lead_score(self, lead: Lead) -> float:
        """
        Predict lead score for a single lead.
        
        Args:
            lead: Lead object
            
        Returns:
            Predicted lead score (0-100)
        """
        try:
            if self.model is None:
                self.load_model()
            
            if self.model is None:
                # Fallback to simple scoring if no model available
                return self._simple_lead_score(lead)
            
            # Prepare features for the lead
            features = self.prepare_features([lead])
            features = self.encode_categorical_features(features)
            
            # Scale features
            if self.scaler:
                features_scaled = self.scaler.transform(features)
            else:
                features_scaled = features
            
            # Predict probability
            conversion_probability = self.model.predict_proba(features_scaled)[0][1]
            
            # Convert to 0-100 score
            score = conversion_probability * 100
            
            return round(score, 2)
            
        except Exception as e:
            logger.error(f"Error predicting lead score: {str(e)}")
            return self._simple_lead_score(lead)
    
    def _simple_lead_score(self, lead: Lead) -> float:
        """
        Simple lead scoring algorithm as fallback.
        
        Args:
            lead: Lead object
            
        Returns:
            Simple lead score (0-100)
        """
        score = 0.0
        
        # Base score from age (younger leads might be more likely to convert)
        if lead.age < 30:
            score += 20
        elif lead.age < 50:
            score += 15
        else:
            score += 10
        
        # Interaction count
        score += min(lead.interaction_count * 5, 30)
        
        # Engagement level
        if lead.engagement_level == 'high':
            score += 25
        elif lead.engagement_level == 'medium':
            score += 15
        else:
            score += 5
        
        # Has agent assigned
        if lead.agent:
            score += 10
        
        # Recent activity
        if lead.last_contacted:
            days_since_contact = (timezone.now() - lead.last_contacted).days
            if days_since_contact <= 7:
                score += 15
            elif days_since_contact <= 30:
                score += 10
        
        return min(score, 100.0)
    
    def save_model(self) -> None:
        """Save the trained model and related objects."""
        try:
            os.makedirs(settings.ML_MODEL_PATH, exist_ok=True)
            
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            
            with open(self.scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
            
            with open(self.encoders_path, 'wb') as f:
                pickle.dump(self.label_encoders, f)
                
            logger.info("Model saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
    
    def load_model(self) -> bool:
        """
        Load the trained model and related objects.
        
        Returns:
            True if model loaded successfully, False otherwise
        """
        try:
            if not os.path.exists(self.model_path):
                return False
            
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            
            with open(self.scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            
            with open(self.encoders_path, 'rb') as f:
                self.label_encoders = pickle.load(f)
            
            logger.info("Model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            return False
    
    def update_all_lead_scores(self, organisation_id: int) -> int:
        """
        Update lead scores for all leads in an organization.
        
        Args:
            organisation_id: ID of the organization
            
        Returns:
            Number of leads updated
        """
        leads = Lead.objects.filter(organisation_id=organisation_id)
        updated_count = 0
        
        for lead in leads:
            try:
                new_score = self.predict_lead_score(lead)
                lead.update_lead_score(new_score)
                updated_count += 1
            except Exception as e:
                logger.error(f"Error updating score for lead {lead.id}: {str(e)}")
        
        logger.info(f"Updated scores for {updated_count} leads")
        return updated_count


# Global instance
lead_scoring_service = LeadScoringService() 