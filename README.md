# Code Smell Detector

A fine-tuned CodeBERT classifier that flags Python functions likely to have code-quality problems, served as a serverless REST API on AWS Lambda. A local analysis pipeline combines the model's prediction with security scanning, complexity metrics, and LLM-generated fix suggestions to produce a 0 to 100 quality score.

## How it works

1. **Smell prediction.** The code is sent to the deployed model, which returns `clean` or `smell` with a confidence.
2. **Static analysis.** [Bandit](https://bandit.readthedocs.io/) reports security issues and [Radon](https://radon.readthedocs.io/) reports cyclomatic complexity per function.
3. **Fix suggestions.** GPT-4o-mini receives the code and the findings and returns prioritized fixes as structured JSON, along with the token cost of the request.
4. **Quality score.** The score starts at 100 and loses points for a predicted smell (up to 20, scaled by confidence), for each security issue (15 high, 10 medium, 5 low), and for high average complexity (10 above 5, 20 above 10).

## Repository layout

| Path | Purpose |
|---|---|
| `download_data.py` | Downloads the dataset from Hugging Face |
| `explore_and_baseline.ipynb` | Data exploration, labelling rules, Random Forest baseline, CodeBERT classifier definition |
| `lambda/lambda_function.py` | Lambda handler that loads the model and serves predictions |
| `lambda/Dockerfile` | Container image for the Lambda function |
| `lambda/requirements.txt` | Pinned dependencies for the image (CPU-only PyTorch) |
| `pipeline.py` | Runs the full analysis and prints the report |
| `code_analyzer.py` | Bandit and Radon wrappers |
| `fix_suggester.py` | GPT-4o-mini fix suggestions |
| `test_code_smell_detector.py` | Small script that calls the deployed API |
| `complex_code.py`, `vulnerable_code.py` | Deliberately bad sample inputs |

## Data and labels

The dataset is the first 10,000 Python functions from [CodeSearchNet](https://huggingface.co/datasets/code_search_net).

There are no human-written smell labels. Each function is labelled by three rule-based heuristics, and counts as a smell if any rule fires:

- **Long function:** more than 50 lines
- **Deep nesting:** indentation deeper than 16 spaces (more than four levels)
- **Magic numbers:** more than 10 numeric literals

This labels 3,227 functions as smells and 6,773 as clean.

## Model

- **Base:** `microsoft/codebert-base`
- **Head:** a single linear layer (768 to 2) on the `[CLS]` token
- **Input:** up to 512 tokens, truncated and padded
- **Output:** `clean` or `smell`, with the softmax probability as confidence

The fine-tuned weights (`code_smell_detector.pth`, about 500 MB) are too large for GitHub and are not stored in this repository.

## API

`POST /predict`

Request:

```json
{ "code": "def f(x):\n    if x > 0:\n        if x > 1:\n            return True" }
```

Response:

```json
{ "prediction": "smell", "confidence": 0.98 }
```

Example:

```bash
curl -X POST https://<api-id>.execute-api.ca-central-1.amazonaws.com/predict \
  -H "Content-Type: application/json" \
  -d '{"code": "def f(x):\n    return x"}'
```

## Deployment

The model runs as a container image on AWS Lambda behind API Gateway, with the image stored in ECR.

- **Offline by design.** The base CodeBERT model and the fine-tuned weights are baked into the image, and the handler sets `TRANSFORMERS_OFFLINE=1`, so nothing is downloaded at runtime.
- **Loaded once per container.** The model loads at import time, so warm requests skip the load.
- **CPU-only PyTorch.** The image installs `torch==2.0.1+cpu` to keep its size down.

Build and push (the image must target `linux/amd64` for Lambda):

```bash
cd lambda
docker buildx build --platform linux/amd64 --provenance=false -t code-smell-detector .
docker tag code-smell-detector:latest <registry>/code-smell-detector:latest
docker push <registry>/code-smell-detector:latest
```

## Running the pipeline locally

```bash
pip install -r requirements.txt
```

Set your OpenAI key as an environment variable, then run the pipeline.

macOS, Linux, or Git Bash:

```bash
export OPENAI_API_KEY=your-key
python pipeline.py
```

Windows PowerShell:

```powershell
$env:OPENAI_API_KEY = "your-key"
python pipeline.py
```

## Limitations

- **Weak labels.** The model is trained on rule-generated labels, so it learns to approximate those three rules. It is not validated against human judgments of code quality.
- **Cold starts.** The first request after the function has been idle can exceed API Gateway's 30-second limit while the model loads. Later requests return quickly.
- **Function-level only.** Inputs longer than 512 tokens are truncated.