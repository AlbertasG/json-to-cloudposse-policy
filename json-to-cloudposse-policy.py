#!/usr/bin/env python3

import json
import sys

def convert_json_to_cloudposse_iam(json_file):
    """
    Reads a JSON file representing an IAM policy and converts it to the
    Terraform/Terragrunt format matching the cloudposse/iam-policy module's variables.tf,
    omitting keys with empty values.
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
        "version": data.get("Version", "2012-10-17") if data.get("Version") else None,
        "statements": []
    }]
    if terraform_policy[0]["version"] is None:
        del terraform_policy[0]["version"]

    for statement in data.get("Statement", []):
        terraform_statement = {}
        if statement.get("Sid"):
            terraform_statement["sid"] = statement["Sid"]
        if statement.get("Effect"):
            terraform_statement["effect"] = statement["Effect"]
        if statement.get("Action"):
            terraform_statement["actions"] = statement["Action"] if isinstance(statement["Action"], list) else [statement["Action"]]
        if statement.get("NotAction"):
            terraform_statement["not_actions"] = statement["NotAction"] if isinstance(statement["NotAction"], list) else [statement["NotAction"]]
        if statement.get("Resource"):
            terraform_statement["resources"] = statement["Resource"] if isinstance(statement["Resource"], list) else [statement["Resource"]]
        if statement.get("NotResource"):
            terraform_statement["not_resources"] = statement["NotResource"] if isinstance(statement["NotResource"], list) else [statement["NotResource"]]

        conditions = []
        if "Condition" in statement:
            for condition_type, condition_map in statement["Condition"].items():
                for variable, values in condition_map.items():
                    conditions.append({
                        "test": condition_type,
                        "variable": variable,
                        "values": values if isinstance(values, list) else [values]
                    })
        if conditions:
            terraform_statement["conditions"] = conditions

        principals = []
        if "Principal" in statement:
            for principal_type, identifiers in statement["Principal"].items():
                principals.append({
                    "type": principal_type,
                    "identifiers": identifiers if isinstance(identifiers, list) else [identifiers]
                })
        if principals:
            terraform_statement["principals"] = principals

        not_principals = []
        if "NotPrincipal" in statement:
            for principal_type, identifiers in statement["NotPrincipal"].items():
                not_principals.append({
                    "type": principal_type,
                    "identifiers": identifiers if isinstance(identifiers, list) else [identifiers]
                })
        if not_principals:
            terraform_statement["not_principals"] = not_principals

        terraform_policy[0]["statements"].append(terraform_statement)

    output = "iam_policy = [\n"
    for policy in terraform_policy:
        output += "  {\n"
        for key, value in policy.items():
            output += f"    {key} = "
            if key == "statements":
                output += "[\n"
                for i, statement in enumerate(value):
                    output += "      {\n"
                    for stmt_key, stmt_value in statement.items():
                        if isinstance(stmt_value, list):
                            output += f"        {stmt_key} = [" + ", ".join([f"\"{item}\"" for item in stmt_value]) + "],\n"
                        elif isinstance(stmt_value, str):
                            output += f"        {stmt_key} = \"{stmt_value}\",\n"
                        elif isinstance(stmt_value, list) and all(isinstance(item, dict) for item in stmt_value):
                            output += f"        {stmt_key} = [\n"
                            for item in stmt_value:
                                output += "          {\n"
                                for item_key, item_value in item.items():
                                    output += f"            {item_key} = "
                                    if isinstance(item_value, list):
                                        output += "[" + ", ".join([f"\"{v}\"" for v in item_value]) + "],\n"
                                    else:
                                        output += f"\"{item_value}\",\n"
                                output = output.rstrip(',\n') + "\n          },\n"
                            output += "        ],\n"
                        elif stmt_value is not None:
                            output += f"        {stmt_key} = {json.dumps(stmt_value)},\n"
                    output = output.rstrip(',\n') + "\n      }"
                    if i < len(value) - 1:
                        output += ",\n"
                    else:
                        output += "\n"
                output += "    ],\n"
            elif value is not None:
                output += f"\"{value}\",\n"
        output = output.rstrip(',\n') + "\n  }\n"
    output += "]\n"

    print(output)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: json_to_cloudposse.py <path_to_json_file>")
        sys.exit(1)

    json_file_path = sys.argv[1]
    convert_json_to_cloudposse_iam(json_file_path)