"""
Simple test script to verify the Peach.keras model can be loaded and used.
Run this from the virtual environment: venv\Scripts\activate && python test_model.py
"""

import os
import sys

# Add the project to the path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Setup Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

import django
django.setup()

from tensorflow import keras
import tensorflow_addons as tfa
import numpy as np

# Test model loading
MODEL_PATH = os.path.join(BASE_DIR, 'Peach.keras')

print(f"Testing model loading from: {MODEL_PATH}")
print(f"Model file exists: {os.path.exists(MODEL_PATH)}")

try:
    # Load model with custom objects for tensorflow-addons optimizers
    model = keras.models.load_model(
        MODEL_PATH,
        custom_objects={'Addons>AdamW': tfa.optimizers.AdamW}
    )
    print("✓ Model loaded successfully!")
    print(f"\nModel summary:")
    model.summary()
    
    print(f"\nModel input shape: {model.input_shape}")
    print(f"Model output shape: {model.output_shape}")
    
    # Test with dummy data
    input_shape = model.input_shape[1:]  # Remove batch dimension
    dummy_input = np.random.rand(1, *input_shape).astype(np.float32)
    
    print(f"\nTesting prediction with dummy input of shape: {dummy_input.shape}")
    prediction = model.predict(dummy_input, verbose=0)
    print(f"Prediction shape: {prediction.shape}")
    print(f"Prediction output: {prediction}")
    print(f"Predicted class: {np.argmax(prediction[0])}")
    
    print("\n✓ Model is working correctly!")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
