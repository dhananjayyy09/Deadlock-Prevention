import numpy as np
from typing import List, Tuple, Dict
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import pickle
import os


class MLDeadlockPredictor:
    """
    Machine Learning-based deadlock prediction using Random Forest.
    Learns from historical deadlock patterns to predict future occurrences.
    """
    
    def __init__(self, model_path: str = "deadlock_model.pkl"):
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.model_path = model_path
        self.is_trained = False
        
        # Try to load existing model
        self.load_model()
    
    def extract_features(self, snapshot) -> np.array:
        """
        Extract numerical features from system snapshot for ML model.
        
        Features:
        1. Number of processes
        2. Number of resources
        3. Total allocated resources
        4. Total requested resources
        5. Resource utilization ratio
        6. Request density (requests per process)
        7. Average resources per process
        8. Max resources held by single process
        9. Number of processes with pending requests
        10. Circular wait indicator (heuristic)
        """
        num_processes = len(snapshot.processes)
        num_resources = len(snapshot.resources)
        
        total_allocated = sum(snapshot.allocation.values())
        total_requested = sum(snapshot.request.values())
        total_capacity = sum(r.total for r in snapshot.resources.values())
        
        utilization = total_allocated / total_capacity if total_capacity > 0 else 0
        request_density = total_requested / num_processes if num_processes > 0 else 0
        avg_resources = total_allocated / num_processes if num_processes > 0 else 0
        
        # Max resources held by single process
        process_allocations = {}
        for (pid, rid), alloc in snapshot.allocation.items():
            process_allocations[pid] = process_allocations.get(pid, 0) + alloc
        max_held = max(process_allocations.values()) if process_allocations else 0
        
        # Processes with pending requests
        processes_requesting = len(set(pid for (pid, rid), req in snapshot.request.items() if req > 0))
        
        # Circular wait indicator: processes both holding and requesting
        both_hold_and_request = 0
        for process in snapshot.processes:
            has_allocation = any(snapshot.allocation.get((process.pid, rid), 0) > 0 
                               for rid in snapshot.resources.keys())
            has_request = any(snapshot.request.get((process.pid, rid), 0) > 0 
                            for rid in snapshot.resources.keys())
            if has_allocation and has_request:
                both_hold_and_request += 1
        
        features = np.array([
            num_processes,
            num_resources,
            total_allocated,
            total_requested,
            utilization,
            request_density,
            avg_resources,
            max_held,
            processes_requesting,
            both_hold_and_request
        ])
        
        return features
    
    def train(self, training_data: List[Tuple], epochs: int = 1):
        """
        Train the model on historical data.
        
        Args:
            training_data: List of (snapshot, has_deadlock) tuples
            epochs: Number of training iterations
        """
        if not training_data:
            print("No training data provided")
            return
        
        # Extract features and labels
        X = []
        y = []
        for snapshot, has_deadlock in training_data:
            features = self.extract_features(snapshot)
            X.append(features)
            y.append(1 if has_deadlock else 0)
        
        X = np.array(X)
        y = np.array(y)
        
        # Normalize features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model.fit(X_scaled, y)
        self.is_trained = True
        
        # Calculate training accuracy
        train_score = self.model.score(X_scaled, y)
        print(f"Training accuracy: {train_score:.2%}")
        
        # Save model
        self.save_model()
    
    def predict_deadlock_probability(self, snapshot) -> float:
        """
        Predict probability of deadlock occurring in current state.
        
        Returns:
            Float between 0 and 1 representing deadlock probability
        """
        if not self.is_trained:
            # Generate synthetic prediction if not trained
            features = self.extract_features(snapshot)
            # Simple heuristic: high utilization + many requests = higher risk
            utilization = features[4]
            request_density = features[5]
            return min((utilization * 0.6 + request_density * 0.4), 1.0)
        
        features = self.extract_features(snapshot)
        features_scaled = self.scaler.transform([features])
        
        # Get probability of deadlock class (class 1)
        proba = self.model.predict_proba(features_scaled)[0][1]
        return proba
    
    def predict_and_explain(self, snapshot) -> Dict:
        """
        Predict deadlock and provide explanation of contributing factors.
        """
        probability = self.predict_deadlock_probability(snapshot)
        features = self.extract_features(snapshot)
        
        # Feature importance (if model is trained)
        feature_names = [
            "num_processes", "num_resources", "total_allocated",
            "total_requested", "utilization", "request_density",
            "avg_resources", "max_held", "processes_requesting",
            "circular_wait_indicator"
        ]
        
        importance = {}
        if self.is_trained:
            for name, importance_val in zip(feature_names, self.model.feature_importances_):
                importance[name] = float(importance_val)
        
        return {
            "probability": probability,
            "risk_level": self._get_risk_level(probability),
            "features": {name: float(val) for name, val in zip(feature_names, features)},
            "feature_importance": importance
        }
    
    def _get_risk_level(self, probability: float) -> str:
        """Convert probability to risk level."""
        if probability < 0.3:
            return "LOW"
        elif probability < 0.6:
            return "MEDIUM"
        elif probability < 0.8:
            return "HIGH"
        else:
            return "CRITICAL"
    
    def save_model(self):
        """Save trained model to disk."""
        with open(self.model_path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler,
                'is_trained': self.is_trained
            }, f)
    
    def load_model(self):
        """Load trained model from disk."""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.model = data['model']
                    self.scaler = data['scaler']
                    self.is_trained = data['is_trained']
                print(f"Model loaded from {self.model_path}")
            except Exception as e:
                print(f"Failed to load model: {e}")
