"""
Complete Pipeline Execution Script
Runs preprocessing, model comparison, and hybrid model training
"""

import os
from preprocessing import DataPreprocessor
from model_comparison import ModelComparator
from model_train import HybridRFXGBoost, plot_results

def main():
    print("\n" + "="*60)
    print("DDOS DETECTION SYSTEM - COMPLETE PIPELINE")
    print("="*60)
    
    dataset_path = 'data/Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv'
    
    if not os.path.exists(dataset_path):
        print(f"\n❌ Dataset not found at {dataset_path}")
        print("Download from: https://www.unb.ca/cic/datasets/ids-2017.html")
        return
    
    # Step 1: Preprocessing
    print("\n[STEP 1] Data Preprocessing...")
    preprocessor = DataPreprocessor()
    X_train, X_test, y_train, y_test = preprocessor.preprocess(dataset_path)
    preprocessor.save_preprocessor()
    
    # Step 2: Model Comparison
    print("\n[STEP 2] Model Comparison...")
    comparator = ModelComparator()
    comparator.compare_all_models(X_train, X_test, y_train, y_test)
    comparator.plot_comparison()
    comparator.save_comparison_report()
    
    # Step 3: Hybrid Model Training
    print("\n[STEP 3] Hybrid Model Training...")
    hybrid = HybridRFXGBoost(rf_weight=0.5, xgb_weight=0.5)
    hybrid.fit(X_train, y_train)
    results = hybrid.evaluate(X_test, y_test)
    plot_results(results)
    hybrid.save_model()
    
    print("\n" + "="*60)
    print("✓ PIPELINE COMPLETE!")
    print("="*60)
    print("\nGenerated files:")
    print("  - models/hybrid_model.pkl")
    print("  - models/preprocessor.pkl")
    print("  - models/model_comparison.png")
    print("  - models/hybrid_model_results.png")
    print("\nRun web app: python app.py")

if __name__ == "__main__":
    main()
