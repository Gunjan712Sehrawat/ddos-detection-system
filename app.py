"""
Flask Web Application for DDoS Detection System (REQUIRED)
Provides web interface for real-time DDoS attack prediction
"""

from flask import Flask, render_template, request, jsonify
import numpy as np
import pandas as pd
import joblib
import os
from werkzeug.utils import secure_filename
from model_train import HybridRFXGBoost

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = 'uploads'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

model = None
preprocessor_data = None

def load_model_and_preprocessor():
    """Load trained model and preprocessor"""
    global model, preprocessor_data
    try:
        model = HybridRFXGBoost.load_model('models/hybrid_model.pkl')
        preprocessor_data = joblib.load('models/preprocessor.pkl')
        print("✓ Model and preprocessor loaded successfully")
        return True
    except FileNotFoundError:
        print("❌ Model files not found. Train the model first: python model_train.py")
        return False

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    """Handle single prediction request"""
    try:
        features = []
        feature_names = preprocessor_data['feature_columns']
        
        for feature_name in feature_names:
            value = request.form.get(feature_name, 0)
            try:
                features.append(float(value))
            except:
                features.append(0.0)
        
        features_array = np.array(features).reshape(1, -1)
        scaler = preprocessor_data['scaler']
        features_scaled = scaler.transform(features_array)
        
        prediction = model.predict(features_scaled)[0]
        prediction_proba = model.predict_proba(features_scaled)[0]
        confidence = float(max(prediction_proba)) * 100
        
        result = "DDoS Attack" if prediction == 1 else "Benign Traffic"
        alert_class = "danger" if prediction == 1 else "success"
        
        return jsonify({
            'success': True,
            'prediction': result,
            'confidence': confidence,
            'alert_class': alert_class,
            'probabilities': {
                'benign': float(prediction_proba[0]) * 100,
                'ddos': float(prediction_proba[1]) * 100
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/predict_batch', methods=['POST'])
def predict_batch():
    """Handle batch prediction from CSV file"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '' or not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'error': 'Invalid file'}), 400
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        df = pd.read_csv(filepath)
        feature_names = preprocessor_data['feature_columns']
        
        missing = [f for f in feature_names if f not in df.columns]
        if missing:
            return jsonify({'success': False, 'error': f'Missing features: {missing[:5]}'}), 400
        
        X = df[feature_names].values
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        
        scaler = preprocessor_data['scaler']
        X_scaled = scaler.transform(X)
        
        predictions = model.predict(X_scaled)
        predictions_proba = model.predict_proba(X_scaled)
        
        total = len(predictions)
        ddos_count = int(np.sum(predictions == 1))
        benign_count = int(np.sum(predictions == 0))
        
        top_predictions = []
        for i in range(min(10, len(predictions))):
            top_predictions.append({
                'index': i + 1,
                'prediction': 'DDoS Attack' if predictions[i] == 1 else 'Benign Traffic',
                'confidence': float(max(predictions_proba[i])) * 100
            })
        
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'total_samples': total,
            'ddos_count': ddos_count,
            'benign_count': benign_count,
            'ddos_percentage': (ddos_count / total) * 100,
            'top_predictions': top_predictions
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/model_info')
def model_info():
    """Get model information"""
    try:
        return jsonify({
            'model_type': 'Hybrid (Random Forest + XGBoost)',
            'rf_weight': model.rf_weight,
            'xgb_weight': model.xgb_weight,
            'num_features': len(preprocessor_data['feature_columns'])
        })
    except:
        return jsonify({'error': 'Model not loaded'}), 400

if __name__ == '__main__':
    print("\n" + "="*60)
    print("DDOS DETECTION SYSTEM - WEB APPLICATION")
    print("="*60)
    
    if load_model_and_preprocessor():
        print("\n✓ System ready!")
        print("Access at: http://127.0.0.1:5000")
        print("="*60 + "\n")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("\n❌ Failed to load model. Train first: python model_train.py")
