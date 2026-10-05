import json

import requests

from code_analyzer import analyze_code
from fix_suggester import get_fix_suggestions


def calculate_quality_score(smell_result, analysis):
    score = 100

    # Deduct for code smells
    if smell_result['prediction'] == 'smell':
        score -= 20 * smell_result['confidence']

    # Deduct for security issues
    for issue in analysis['security']['issues']:
        if issue['severity'] == 'HIGH':
            score -= 15
        elif issue['severity'] == 'MEDIUM':
            score -= 10
        else:
            score -= 5

    # Deduct for complexity
    avg_complexity = analysis['complexity']['average_complexity']
    if avg_complexity > 10:
        score -= 20
    elif avg_complexity > 5:
        score -= 10

    return max(0, round(score, 1))


def run_full_analysis(code):
    print("Step 1/3: Detecting code smells...")
    smell_response = requests.post(
        "https://4fl5hk5s98.execute-api.ca-central-1.amazonaws.com/predict",
        json={"code": code}
    )
    smell_result = smell_response.json()
    print(f"  ✓ Prediction: {smell_result['prediction']} (confidence: {smell_result['confidence']:.2%})")

    print("\nStep 2/3: Analyzing security and complexity...")
    analysis = analyze_code(code)
    print(f"  ✓ Security issues: {analysis['security']['issues_found']}")
    print(f"  ✓ Average complexity: {analysis['complexity']['average_complexity']:.1f}")

    # Step 3: AI Fix Suggestions
    print("\nStep 3/3: Generating AI fix suggestions...")
    suggestions = get_fix_suggestions(
        code,
        smell_result,
        analysis['security'],
        analysis['complexity']
    )
    print(f"  ✓ Generated {len(suggestions['fixes'])} fix suggestions")
    print(f"  ✓ Cost: ${suggestions['cost']['estimated_usd']:.6f}")

    # Combine all results
    final_report = {
        "code_smell": smell_result,
        "security": analysis['security'],
        "complexity": analysis['complexity'],
        "metrics": analysis['metrics'],
        "ai_suggestions": suggestions,
        "summary": {
            "total_issues": (
                    analysis['security']['issues_found'] +
                    (1 if smell_result['prediction'] == 'smell' else 0)
            ),
            "overall_quality": calculate_quality_score(smell_result, analysis)
        }
    }

    return final_report


# Test the full pipeline
if __name__ == "__main__":
    test_code = """
def process_payment(card_number, amount):
    api_key = 'sk-1234567890abcdef'  # Hardcoded secret

    if card_number:
        if len(card_number) > 0:
            if card_number.isdigit():
                if len(card_number) == 16:
                    if amount > 0:
                        if amount < 10000:
                            query = "INSERT INTO payments VALUES ('" + card_number + "', " + str(amount) + ")"
                            eval(query)
                            return True
    return False
"""

    print("=" * 70)
    print("CODE QUALITY ANALYSIS")
    print("=" * 70)
    print()

    report = run_full_analysis(test_code)

    print("\n" + "=" * 70)
    print("FINAL REPORT")
    print("=" * 70)
    print(json.dumps(report, indent=2))

    print("\n" + "=" * 70)
    print(f"Overall Quality Score: {report['summary']['overall_quality']}/100")
    print("=" * 70)