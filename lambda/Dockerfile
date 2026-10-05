FROM public.ecr.aws/lambda/python:3.11

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Save only the CodeBERT tokenizer and config during build (not at runtime).
# The pretrained weights are not needed: the fine-tuned checkpoint below
# already contains every CodeBERT weight.
RUN python -c "from transformers import AutoTokenizer, AutoConfig; \
    AutoTokenizer.from_pretrained('microsoft/codebert-base').save_pretrained('/opt/ml/codebert'); \
    AutoConfig.from_pretrained('microsoft/codebert-base').save_pretrained('/opt/ml/codebert')"

# Copy model file
COPY code_smell_detector.pth /opt/ml/model/

# Copy Lambda function
COPY lambda_function.py ${LAMBDA_TASK_ROOT}

CMD ["lambda_function.lambda_handler"]