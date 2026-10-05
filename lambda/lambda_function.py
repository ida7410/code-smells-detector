import json
import os

# MUST set these BEFORE importing transformers
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'

import torch
from transformers import AutoTokenizer, AutoModel
import torch.nn as nn


# Model definition
class CodeSmellClassifier(nn.Module):
    def __init__(self):
        super(CodeSmellClassifier, self).__init__()
        self.codebert = AutoModel.from_pretrained("/opt/ml/codebert", local_files_only=True)
        self.classifier = nn.Linear(768, 2)

    def forward(self, input_ids):
        outputs = self.codebert(input_ids)
        cls_output = outputs.last_hidden_state[:, 0, :]
        logits = self.classifier(cls_output)
        return logits


# Load once at cold start
print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained("/opt/ml/codebert", local_files_only=True)
print("Loading model...")
model = CodeSmellClassifier()
print("Loading weights...")
model.load_state_dict(torch.load('/opt/ml/model/code_smell_detector.pth', map_location='cpu'), strict=False)
model.eval()
print("Model ready!")


def lambda_handler(event, context):
    try:
        body = json.loads(event['body']) if 'body' in event else event
        code = body['code']

        tokens = tokenizer.encode(
            code,
            truncation=True,
            max_length=512,
            padding='max_length',
            return_tensors='pt'
        )

        with torch.no_grad():
            outputs = model(tokens)
            probabilities = torch.softmax(outputs, dim=1)
            predicted_class = torch.argmax(probabilities, dim=1).item()
            confidence = probabilities[0][predicted_class].item()

        prediction = "clean" if predicted_class == 0 else "smell"

        return {
            'statusCode': 200,
            'body': json.dumps({
                'prediction': prediction,
                'confidence': round(confidence, 4)
            })
        }

    except Exception as e:
        import traceback
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'traceback': traceback.format_exc()
            })
        }