import json
import os
import traceback

# MUST be set before transformers is imported
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'

MODEL_DIR = '/opt/ml/codebert'  # tokenizer files and config.json only
WEIGHTS_PATH = '/opt/ml/model/code_smell_detector.pth'

# Filled in by _load() on the first request, then reused while the container is warm
_state = {}


def _load():
    """Load the tokenizer and model once per container, on the first request.

    This runs inside the handler rather than at import time on purpose.
    Lambda limits the init phase to 10 seconds; if a heavy import-time load
    overruns it, Lambda aborts the init and starts it again during the first
    invocation, so the load would effectively run twice.
    """
    if _state:
        return _state

    import torch
    import torch.nn as nn
    from transformers import AutoConfig, AutoModel, AutoTokenizer

    class CodeSmellClassifier(nn.Module):
        def __init__(self):
            super().__init__()
            # Build the CodeBERT architecture from its config only. The
            # fine-tuned checkpoint already contains every CodeBERT weight,
            # so loading the pretrained weights first would be wasted work.
            config = AutoConfig.from_pretrained(MODEL_DIR, local_files_only=True)
            self.codebert = AutoModel.from_config(config)
            self.classifier = nn.Linear(768, 2)

        def forward(self, input_ids):
            outputs = self.codebert(input_ids)
            cls_output = outputs.last_hidden_state[:, 0, :]
            return self.classifier(cls_output)

    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, local_files_only=True)

    print("Building model and loading fine-tuned weights...")
    model = CodeSmellClassifier()
    result = model.load_state_dict(torch.load(WEIGHTS_PATH, map_location='cpu'), strict=False)

    # The model starts from random weights, so every learned weight must come
    # from the checkpoint. The only key allowed to be absent is the
    # position_ids buffer, which is a fixed range and not a learned weight.
    missing = [k for k in result.missing_keys if not k.endswith('position_ids')]
    if missing or result.unexpected_keys:
        raise RuntimeError(
            f"Checkpoint does not match the model. Missing: {missing}. "
            f"Unexpected: {list(result.unexpected_keys)}"
        )

    model.eval()
    print("Model ready!")

    _state.update(torch=torch, tokenizer=tokenizer, model=model)
    return _state


def lambda_handler(event, context):
    try:
        body = json.loads(event['body']) if 'body' in event else event
        code = body['code']

        state = _load()
        torch, tokenizer, model = state['torch'], state['tokenizer'], state['model']

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
        # Full traceback goes to CloudWatch; the caller only sees the message
        print(traceback.format_exc())
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }