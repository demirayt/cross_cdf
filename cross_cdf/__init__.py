"""
Function which validates a given cdf against the metadata information stored in metadata_cdf.json 
"""

import pdb
import re
import json
import pdb
import jsonschema
import argparse
import pandas as pd

# Basic type checking utility
def check_type(value, allowed_types):
    if "number" in allowed_types and isinstance(value, (int, float)):
        return True
    if "string" in allowed_types and isinstance(value, str):
        return True
    if "array" in allowed_types and isinstance(value, list):
        return True
    if "object" in allowed_types and isinstance(value, dict):
        return True
    return False

def validate_row(index, row, metadata):
    """
    Validate a single row from the CDF against the metadata JSON.

    Args:
        row (dict): One row from the CDF as a dictionary.
        metadata (dict): Loaded metadata from JSON.

    Raises:
        ValueError: If any validation fails.
    """
    errors = []
    category = row["Category"]
    variable = row["VariableName"]
    subcat = row["VariableContext"] if not pd.isna(row["VariableContext"]) else ""
    raw_value = str(row["Value"]).strip()

    if category not in metadata["parameters"]:
        errors.append((index, f"❌ Category '{category}' not found."))
        return False

    if variable not in metadata["parameters"][category]:
        available = ", ".join(metadata["parameters"][category].keys())
        errors.append((index, f"❌ Variable '{variable}' not found in category '{category}'. Available: {available}"))
        return False

    param = metadata["parameters"][category][variable]
    expected_types = param.get("types", [])
    raw_contexts = param.get("VariableContext", [])
    context_defs = metadata.get("$contextDefs", {})
    known_subs = resolve_variable_context(raw_contexts, context_defs)
    if subcat not in known_subs:
        errors.append((index, f"❌ VariableContext '{subcat}' not listed for {category} → {variable}. Available: {known_subs}"))

    try:
        parsed = json.loads(raw_value)
    except Exception:
        parsed = raw_value

    # Check if value matches any allowed type
    valid = False
    for typ in expected_types:
        typ_name = typ.replace("$defs:", "")
        if typ in ("number", "string", "array", "object") and check_type(parsed, [typ]):
            valid = True
            break
        elif typ_name in metadata.get("$defs", {}):
            if isinstance(parsed, dict):
                try:
                    jsonschema.validate(instance=parsed, schema=metadata["$defs"][typ_name])
                    valid = True
                    break
                except jsonschema.exceptions.ValidationError as ve:
                    errors.append((index, f"❌ Object value error for {category} → {variable}: {ve.message}. Value: {raw_value}"))
                except jsonschema.exceptions.ValidationError:
                    continue

    if not valid:
        errors.append((index, f"❌ Value type mismatch for {category} → {variable}. Value: {raw_value}, expected types: {expected_types}"))

    unit = row["unit"] if not pd.isna(row["unit"]) else ""
    raw_units = param.get("units", [])
    units_defs = metadata.get("$unitDefs", {})
    known_units = resolve_variable_context(raw_units, units_defs)
    if unit and unit not in known_units:
        errors.append((index, f"❌ Units '{unit}' not listed for {category} → {variable}. Available: {known_units}"))

    try:
        parsed = json.loads(raw_value)
    except Exception:
        parsed = raw_value

    if not errors:
        print("✅ All rows passed validation.")
    else:
        for idx, msg in errors:
            print(f"Row {idx+2}: {msg}")

    return True

def resolve_variable_context(raw_contexts, context_defs):
    resolved = []
    if isinstance(raw_contexts, str):
        raw_contexts = [raw_contexts]

    for context in raw_contexts:
        if isinstance(context, str) and context.startswith("$refs:"):
            ref_name = context.replace("$refs:", "")
            resolved.extend(context_defs.get(ref_name, []))
        elif isinstance(context, str):
            try:
                # Attempt to parse as a list of refs like '["$refs:Ref1", "$refs:Ref2"]'
                parsed = json.loads(context)
                if isinstance(parsed, list):
                    for item in parsed:
                        if isinstance(item, str) and item.startswith("$refs:"):
                            ref_name = item.replace("$refs:", "")
                            resolved.extend(context_defs.get(ref_name, []))
                        else:
                            resolved.append(item)
                else:
                    resolved.append(context)
            except Exception:
                resolved.append(context)
        else:
            resolved.append(context)
    return list(set(resolved))

def main():

    parser = argparse.ArgumentParser(description="Convert multiple input files to row-based CDF format using a config file.")
    parser.add_argument("--metadata", required=True, help="Path to the configuration JSON file")
    parser.add_argument("--cdf", required=True, help="Path to the configuration JSON file")
    args = parser.parse_args()

    # Load metadata and CSV
    with open(args.metadata) as f:
        metadata = json.load(f)
    df = pd.read_csv(args.cdf)

    errors = []

    for index, row in df.iterrows():
        category = row["Category"]
        variable = row["VariableName"]
        subcat = row["VariableContext"] if not pd.isna(row["VariableContext"]) else ""
        raw_value = str(row["Value"]).strip()

        if category not in metadata["parameters"]:
            errors.append((index, f"❌ Category '{category}' not found."))
            continue

        if variable not in metadata["parameters"][category]:
            available = ", ".join(metadata["parameters"][category].keys())
            errors.append((index, f"❌ Variable '{variable}' not found in category '{category}'. Available: {available}"))
            continue

        param = metadata["parameters"][category][variable]
        expected_types = param.get("types", [])
        raw_contexts = param.get("VariableContext", [])
        context_defs = metadata.get("$contextDefs", {})
        known_subs = resolve_variable_context(raw_contexts, context_defs)
        if subcat not in known_subs:
            errors.append((index, f"❌ VariableContext '{subcat}' not listed for {category} → {variable}. Available: {known_subs}"))

        try:
            parsed = json.loads(raw_value)
        except Exception:
            parsed = raw_value

        # Check if value matches any allowed type
        valid = False
        for typ in expected_types:
            typ_name = typ.replace("$defs:", "")
            if typ in ("number", "string", "array", "object") and check_type(parsed, [typ]):
                valid = True
                break
            elif typ_name in metadata.get("$defs", {}):
                if isinstance(parsed, dict):
                    try:
                        jsonschema.validate(instance=parsed, schema=metadata["$defs"][typ_name])
                        valid = True
                        break
                    except jsonschema.exceptions.ValidationError as ve:
                        errors.append((index, f"❌ Object value error for {category} → {variable}: {ve.message}. Value: {raw_value}"))
                    except jsonschema.exceptions.ValidationError:
                        continue

        if not valid:
            errors.append((index, f"❌ Value type mismatch for {category} → {variable}. Value: {raw_value}, expected types: {expected_types}"))

        unit = row["unit"] if not pd.isna(row["unit"]) else ""
        raw_units = param.get("units", [])
        units_defs = metadata.get("$unitDefs", {})
        known_units = resolve_variable_context(raw_units, units_defs)
        if unit and unit not in known_units:
            errors.append((index, f"❌ Units '{unit}' not listed for {category} → {variable}. Available: {known_units}"))

        try:
            parsed = json.loads(raw_value)
        except Exception:
            parsed = raw_value

        # # Extended unit validation: enum → pattern → conversions
        # if 'units' in param:
        #     unit_info = param['units']
        #     unit_val = str(row.get('unit', '')).strip()
        #     allowed_units = unit_info.get('enum', [])

        #     if not allowed_units:
        #         pass  # No constraints to check
        #     elif allowed_units and unit_val in allowed_units:
        #         pass  # Valid by enum
        #     else:
        #         msg = f"❌ Invalid unit for {category} → {variable}. Found: '{unit_val}', allowed: {allowed_units}"
        #         errors.append((index, msg))

    if not errors:
        print("✅ All rows passed validation.")
    else:
        for idx, msg in errors:
            print(f"Row {idx+2}: {msg}")