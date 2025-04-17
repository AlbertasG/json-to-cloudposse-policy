#!/usr/bin/env python3

import json
import sys

def convert_json_to_cloudposse_iam(json_file):
    """
    Reads a JSON file representing an IAM policy and converts it to the
    Terraform/Terragrunt format for the cloudposse/iam-policy module.
    """
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {json_file}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in: {json_file}")
        sys.exit(1)

    if not isinstance(data, dict) or 'Version' not in data or 'Statement' not in data:
        print("Error: Input JSON should be a dictionary with 'Version' and 'Statement' keys.")
        sys.exit(1)

    terraform_policy = [{
        "version": data.get("Version", "2012-10-17"),
        "statements": data.get("Statement", [])
    }]

    # Format the output for better readability
    output = "iam_policy = [\n"
    for policy in terraform_policy:
        output += "  {\n"
        for key, value in policy.items():
            if isinstance(value, list):
                output += f"    {key} = [\n"
                for i, item in enumerate(value):
                    output += "      {\n"
                    for item_key, item_value in item.items():
                        output += f"        {item_key} = \"{item_value}\"\n" if isinstance(item_value, str) else f"        {item_key} = {json.dumps(item_value)}\n"
                    output += "      }"
                    if i < len(value) - 1:
                        output += ",\n"  # Add comma between statements
                    else:
                        output += "\n"
                output += "    ]\n"
            else:
                output += f"    {key} = \"{value}\"\n" if isinstance(value, str) else f"    {key} = {json.dumps(value)}\n"
        output += "  }\n"
    output += "]\n"

    print(output)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: json_to_cloudposse.py <path_to_json_file>")
        sys.exit(1)

    json_file_path = sys.argv[1]
    convert_json_to_cloudposse_iam(json_file_path)