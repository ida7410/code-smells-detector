import json
import os
import tempfile
import subprocess


def analyze_code(code_string):

    # temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code_string)
        temp_file = f.name

    try:
        ## bandit
        # run bandit
        bandit_result = subprocess.run(
            ['bandit', '-f', 'json', temp_file],
            capture_output=True,
            text=True
        )

        # parse into json
        try:
            bandit_data = json.loads(bandit_result.stdout)
            security_issues = [
                {
                    'line': issue['line_number'],
                    'severity': issue['issue_severity'],
                    'confidence': issue['issue_confidence'],
                    'code': issue['code'].strip()
                }
                for issue in bandit_data.get('results', [])
            ]
        except:
            security_issues = []


        ## radon
        # run radon
        radon_result = subprocess.run(
            ['radon', 'cc', temp_file, '-s', '-j'],
            capture_output=True,
            text=True
        )

        # parse into json
        try:
            radon_data = json.loads(radon_result.stdout)
            complexity_data = list(radon_data.values())[0] if radon_data else []
            complexity_info = {
                'average_complexity': sum(item['complexity'] for item in complexity_data) / len(complexity_data if complexity_data else 0),
                'functions': [
                    {
                        'name': item['name'],
                        'complexity': item['complexity'],
                        'rank': item['rank'],
                        'line': item['lineno']
                    }
                    for item in complexity_data
                ]
            }
        except Exception as e:
            complexity_info = {'average_complexity': 0, 'functions': []}

        lines = code_string.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]

        return {
            'security': {
                'issues_found': len(security_issues),
                'issues': security_issues
            },
            'complexity': complexity_info,
            'metrics': {
                'total_lines': len(lines),
                'code_lines': len(non_empty_lines)
            }
        }

    finally:
        os.remove(temp_file)


if __name__ == '__main__':
    test_code = """
import os

user_input = "print('hello')"
eval(user_input)

password = 'admin123'

def get_user(user_id):
    query = 'SELECT * FROM users WHERE id = ' + user_id
    return query

def complex_function(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                if x > y:
                    if y > z:
                        return "case1"
                    else:
                        return "case2"
                else:
                    return "case3"
            else:
                return "case4"
        else:
            return "case5"
    else:
        return "case6"   
"""
    result = analyze_code(test_code)
    print(json.dumps(result, indent=2))