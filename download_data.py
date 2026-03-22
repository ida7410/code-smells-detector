from datasets import load_dataset
import json
import os

print("Downloading Python code samples from Hugging Face...")
print("This might take a few minutes...\n")

# Download a small subset - just 10,000 examples to start
dataset = load_dataset("code_search_net", "python", split="train[:10000]")

print(f"Downloaded {len(dataset)} code samples!")

# Save to a simple format we can explore
print("\nSaving to local files...")
os.makedirs("dataset/python_samples", exist_ok=True)

# Save first 100 as individual files so we can look at them
for i in range(100):
    code = dataset[i]['func_code_string']
    with open(f"dataset/python_samples/sample_{i}.py", 'w', encoding='utf-8') as f:
        f.write(code)

# Save all metadata as JSON for later
with open("dataset/all_samples.json", 'w', encoding='utf-8') as f:
    json.dump([
        {
            'code': item['func_code_string'],
            'docstring': item['func_documentation_string'],
            'name': item['func_name']
        }
        for item in dataset
    ], f)

print("\n✅ Complete!")
print(f"- Saved 100 sample files to: dataset/python_samples/")
print(f"- Saved all 10,000 samples to: dataset/all_samples.json")