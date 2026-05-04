import onnxruntime as ort
import numpy as np



session = ort.InferenceSession("model_artifacts/xgboost_model.onnx")

input_name = session.get_inputs()[0].name
output_name = session.get_outputs()[0].name

print(input_name, output_name)