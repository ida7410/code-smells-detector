import json

from openai import OpenAI

def get_fix_suggestions(code, smell_result, security_result, complexity_result):
    client = OpenAI()
    prompt = f"""
You are an expert code reviewer. Analyze this Python code and provide specific, actionable fix suggestions.

CODE:
```python
{code}
```

ANALYSIS RESULTS:

1. Code Smell Detection:
   - Prediction: {smell_result['prediction']}
   - Confidence: {smell_result['confidence']}

2. Security Issues Found: {security_result['issues_found']}
{json.dumps(security_result['issues'], indent=2) if security_result['issues'] else 'None'}

3. Complexity Metrics:
   - Average Complexity: {complexity_result['average_complexity']:.1f}
   - Functions: {json.dumps(complexity_result['functions'], indent=2)}

Please provide:
1. A brief summary of the main issues (2-3 sentences)
2. Top 3-5 specific fixes, each with:
   - What to fix
   - Why it's important
   - How to fix it (be specific)

Format your response as JSON:
{{
  "summary": "brief overview",
  "fixes": [
    {{
      "priority": "high/medium/low",
      "issue": "what's wrong",
      "why": "why it matters",
      "how": "specific fix suggestion"
    }}
  ]
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system",
             "content": "You are an expert code reviewer who provides clear, actionable suggestions."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        response_format={"type": "json_object"}
    )

    suggestions = json.loads(response.choices[0].message.content)

    # Add cost info
    suggestions['cost'] = {
        'tokens': response.usage.total_tokens,
        'estimated_usd': response.usage.total_tokens * 0.0000015
    }

    return suggestions


if __name__ == "__main__":
    # Test code with multiple issues
    test_code = """
def process_user(user_id):
    password = 'admin123'
    query = 'SELECT * FROM users WHERE id = ' + user_id

    if user_id:
        if len(user_id) > 0:
            if user_id.isdigit():
                if int(user_id) > 0:
                    eval(query)
                    return True
    return False
"""

    # Simulate analysis results
    smell_result = {"prediction": "smell", "confidence": 0.95}

    security_result = {
        "issues_found": 3,
        "issues": [
            {"line": 2, "severity": "LOW", "issue": "Hardcoded password"},
            {"line": 3, "severity": "MEDIUM", "issue": "SQL injection risk"},
            {"line": 9, "severity": "HIGH", "issue": "Use of eval()"}
        ]
    }

    complexity_result = {
        "average_complexity": 5,
        "functions": [
            {"name": "process_user", "complexity": 5, "rank": "B"}
        ]
    }

    print("Generating fix suggestions...\n")
    suggestions = get_fix_suggestions(test_code, smell_result, security_result, complexity_result)

    print(json.dumps(suggestions, indent=2))