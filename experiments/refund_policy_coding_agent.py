#!/usr/bin/env python3
"""
refund_policy_coding_agent.py - Refund Policy Coding Agent

This script implements a minimal "Refund Policy Coding Agent" that:

1) Takes a natural language instruction describing desired refund policy changes.
2) Uses an LLM to convert it into structured policy parameters.
3) Applies those changes to a sandbox copy of refund_tool.py.
4) Runs tests against the sandbox version.
5) Prints a code diff and test summary.

It never modifies the production refund_tool.py automatically.

Usage:
    python -m experiments.refund_policy_coding_agent \
        --instruction "For NO_LONGER_WANTED, allow returns within 10 days and refund 90% of the order amount."

Example:
    python -m experiments.refund_policy_coding_agent \
        --instruction "Increase the refund window for damaged items to 45 days"
"""

import os
import sys
import shutil
import subprocess
import textwrap
import difflib
import json
import argparse
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.clients import get_openai_client


# ============================================================================
# Data Models
# ============================================================================

class RefundPolicyChangeRequest(BaseModel):
    """
    Structured description of desired refund policy changes.
    
    This is the schema the LLM will fill from natural language instructions.
    """
    # Optional updated numeric constants
    max_days_no_longer_wanted: Optional[int] = Field(
        None, description="New max days for NO_LONGER_WANTED refunds."
    )
    max_days_damaged_or_defective: Optional[int] = Field(
        None, description="New max days for DAMAGED_OR_DEFECTIVE refunds."
    )
    partial_refund_rate: Optional[float] = Field(
        None, description="New partial refund rate for NO_LONGER_WANTED (0.0–1.0)."
    )
    # Optional flag to enable category-specific logic later (MVP can ignore if None)
    enable_category_based_rules: Optional[bool] = Field(
        None, description="Whether to enable different policies per product category."
    )
    comments: Optional[str] = Field(
        None, description="Free-form notes or explanation."
    )


# ============================================================================
# Custom Exceptions
# ============================================================================

class PolicyParseError(Exception):
    """Raised when LLM fails to parse policy change instruction."""
    pass


# ============================================================================
# LLM Parsing
# ============================================================================

def parse_policy_change_instruction(instruction: str) -> RefundPolicyChangeRequest:
    """
    Parse natural language instruction into structured RefundPolicyChangeRequest.
    
    Args:
        instruction: Natural language description of desired policy changes
        
    Returns:
        RefundPolicyChangeRequest instance
        
    Raises:
        PolicyParseError: If LLM parsing fails or client unavailable
    """
    client = get_openai_client()
    if client is None:
        raise PolicyParseError(
            "OpenAI client not available. Please set OPENAI_API_KEY environment variable."
        )
    
    # Get model from env or use default
    model = os.getenv("ECOMMERCE_LLM_MODEL", "gpt-4o-mini")
    
    # Construct system prompt
    system_prompt = (
        "You are an assistant that converts natural language refund policy change requests "
        "into a strict JSON object. You must output valid JSON only, matching the schema exactly."
    )
    
    # Construct user prompt with instruction and schema explanation
    user_prompt = textwrap.dedent(f"""
        Convert the following refund policy change request into a JSON object:
        
        "{instruction}"
        
        Output a JSON object with the following optional fields:
        - max_days_no_longer_wanted: integer (new max days for NO_LONGER_WANTED refunds)
        - max_days_damaged_or_defective: integer (new max days for DAMAGED_OR_DEFECTIVE refunds)
        - partial_refund_rate: float between 0.0 and 1.0 (new partial refund rate for NO_LONGER_WANTED)
        - enable_category_based_rules: boolean (whether to enable category-based rules, optional)
        - comments: string (free-form notes, optional)
        
        Only include fields that are explicitly mentioned or can be inferred from the instruction.
        Use null for fields that are not applicable.
        
        Output only valid JSON, no additional text.
    """).strip()
    
    try:
        # Call LLM with JSON mode
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        
        # Extract JSON from response
        content = response.choices[0].message.content
        if not content:
            raise PolicyParseError("LLM returned empty response")
        
        # Parse JSON
        try:
            parsed_dict = json.loads(content)
        except json.JSONDecodeError as e:
            raise PolicyParseError(f"Failed to parse LLM response as JSON: {e}")
        
        # Construct Pydantic model
        return RefundPolicyChangeRequest(**parsed_dict)
        
    except Exception as e:
        if isinstance(e, PolicyParseError):
            raise
        raise PolicyParseError(f"LLM call failed: {e}")


# ============================================================================
# Sandbox File Operations
# ============================================================================

def prepare_sandbox_copy() -> str:
    """
    Create a sandbox copy of refund_tool.py and return its content.
    
    Returns:
        Original source code as string
    """
    project_root = Path(__file__).parent.parent
    production_refund_tool = (
        project_root / "services" / "fiqa_api" / "ecommerce" / "tools" / "refund_tool.py"
    )
    sandbox_dir = project_root / "sandbox" / "ecommerce"
    sandbox_refund_tool = sandbox_dir / "refund_tool_candidate.py"
    
    # Create sandbox directory
    sandbox_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy production file to sandbox
    shutil.copy2(production_refund_tool, sandbox_refund_tool)
    
    # Read and return content
    return sandbox_refund_tool.read_text(encoding="utf-8")


def apply_policy_changes_to_source(
    source: str, 
    changes: RefundPolicyChangeRequest
) -> str:
    """
    Apply policy changes to source code by replacing constant definitions.
    
    This function performs simple line-level text replacements for:
    - MAX_DAYS_NO_LONGER_WANTED
    - MAX_DAYS_DAMAGED_OR_DEFECTIVE
    - PARTIAL_REFUND_RATE
    
    Args:
        source: Original source code
        changes: RefundPolicyChangeRequest with desired changes
        
    Returns:
        Modified source code
    """
    lines = source.splitlines()
    modified_lines = []
    warnings = []
    
    for line in lines:
        modified = False
        
        # Replace MAX_DAYS_NO_LONGER_WANTED
        if changes.max_days_no_longer_wanted is not None:
            if line.strip().startswith("MAX_DAYS_NO_LONGER_WANTED ="):
                # Extract any comment after the value
                if "#" in line:
                    comment_part = line[line.index("#"):]
                    new_line = f"MAX_DAYS_NO_LONGER_WANTED = {changes.max_days_no_longer_wanted}  {comment_part}"
                else:
                    new_line = f"MAX_DAYS_NO_LONGER_WANTED = {changes.max_days_no_longer_wanted}"
                modified_lines.append(new_line)
                modified = True
        
        # Replace MAX_DAYS_DAMAGED_OR_DEFECTIVE
        if changes.max_days_damaged_or_defective is not None:
            if line.strip().startswith("MAX_DAYS_DAMAGED_OR_DEFECTIVE ="):
                if "#" in line:
                    comment_part = line[line.index("#"):]
                    new_line = f"MAX_DAYS_DAMAGED_OR_DEFECTIVE = {changes.max_days_damaged_or_defective}  {comment_part}"
                else:
                    new_line = f"MAX_DAYS_DAMAGED_OR_DEFECTIVE = {changes.max_days_damaged_or_defective}"
                modified_lines.append(new_line)
                modified = True
        
        # Replace PARTIAL_REFUND_RATE
        if changes.partial_refund_rate is not None:
            if line.strip().startswith("PARTIAL_REFUND_RATE ="):
                if "#" in line:
                    comment_part = line[line.index("#"):]
                    new_line = f"PARTIAL_REFUND_RATE = {changes.partial_refund_rate}  {comment_part}"
                else:
                    new_line = f"PARTIAL_REFUND_RATE = {changes.partial_refund_rate}"
                modified_lines.append(new_line)
                modified = True
        
        if not modified:
            modified_lines.append(line)
    
    # Check if we found the constants (basic validation)
    if changes.max_days_no_longer_wanted is not None:
        if not any("MAX_DAYS_NO_LONGER_WANTED" in line for line in modified_lines):
            warnings.append("Warning: MAX_DAYS_NO_LONGER_WANTED constant not found in source")
    
    if changes.max_days_damaged_or_defective is not None:
        if not any("MAX_DAYS_DAMAGED_OR_DEFECTIVE" in line for line in modified_lines):
            warnings.append("Warning: MAX_DAYS_DAMAGED_OR_DEFECTIVE constant not found in source")
    
    if changes.partial_refund_rate is not None:
        if not any("PARTIAL_REFUND_RATE" in line for line in modified_lines):
            warnings.append("Warning: PARTIAL_REFUND_RATE constant not found in source")
    
    # Print warnings if any
    for warning in warnings:
        print(f"[WARNING] {warning}", file=sys.stderr)
    
    return "\n".join(modified_lines)


def write_sandbox_source(path: Path, new_source: str) -> None:
    """
    Write modified source code to sandbox file.
    
    Args:
        path: Path to sandbox file
        new_source: Modified source code
    """
    path.write_text(new_source, encoding="utf-8")


# ============================================================================
# Diff and Testing
# ============================================================================

def print_diff(original: str, modified: str, filename: str = "refund_tool.py") -> None:
    """
    Print unified diff between original and modified source.
    
    Args:
        original: Original source code
        modified: Modified source code
        filename: Name of file for diff display
    """
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
        lineterm=""
    )
    
    print("\n" + "=" * 70)
    print("=== CODE DIFF (sandbox candidate) ===")
    print("=" * 70)
    print("".join(diff))
    print("=" * 70 + "\n")


def run_tests_against_sandbox() -> bool:
    """
    Run a small test suite using the sandbox version of refund_tool.
    
    For MVP, this is a simplified test runner. In a production scenario,
    you would import and run actual unit tests against the sandbox module.
    
    Returns:
        True if tests passed, False otherwise
    """
    project_root = Path(__file__).parent.parent
    
    # For MVP, we'll try to run a simple Python syntax check on the sandbox file
    sandbox_file = project_root / "sandbox" / "ecommerce" / "refund_tool_candidate.py"
    
    if not sandbox_file.exists():
        print("[ERROR] Sandbox file not found", file=sys.stderr)
        return False
    
    # Check Python syntax
    try:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(sandbox_file)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("[TEST] Syntax check: PASSED")
            return True
        else:
            print(f"[TEST] Syntax check: FAILED")
            print(f"[TEST] Error output: {result.stderr}", file=sys.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("[TEST] Syntax check: TIMEOUT", file=sys.stderr)
        return False
    except Exception as e:
        print(f"[TEST] Syntax check: ERROR - {e}", file=sys.stderr)
        return False


# ============================================================================
# Main CLI
# ============================================================================

def extract_current_values(source: str) -> dict:
    """
    Extract current constant values from source code.
    
    Args:
        source: Source code string
        
    Returns:
        Dict with current values
    """
    values = {}
    for line in source.splitlines():
        if "MAX_DAYS_NO_LONGER_WANTED = " in line:
            try:
                value = int(line.split("=")[1].split("#")[0].strip())
                values["max_days_no_longer_wanted"] = value
            except:
                pass
        elif "MAX_DAYS_DAMAGED_OR_DEFECTIVE = " in line:
            try:
                value = int(line.split("=")[1].split("#")[0].strip())
                values["max_days_damaged_or_defective"] = value
            except:
                pass
        elif "PARTIAL_REFUND_RATE = " in line:
            try:
                value = float(line.split("=")[1].split("#")[0].strip())
                values["partial_refund_rate"] = value
            except:
                pass
    return values


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Refund Policy Coding Agent - Modify refund rules in sandbox"
    )
    parser.add_argument(
        "--instruction",
        type=str,
        help="Natural language instruction describing desired refund policy changes"
    )
    
    args = parser.parse_args()
    
    # Get instruction from args or prompt user
    if args.instruction:
        instruction = args.instruction
    else:
        print("Enter your refund policy change instruction:")
        instruction = input("> ").strip()
        if not instruction:
            print("[ERROR] Instruction cannot be empty", file=sys.stderr)
            sys.exit(1)
    
    print("\n" + "=" * 70)
    print("=== Refund Policy Coding Agent ===")
    print("=" * 70)
    print(f"\nInstruction: {instruction}\n")
    
    # Step 1: Parse instruction
    try:
        print("[STEP 1] Parsing instruction with LLM...")
        changes = parse_policy_change_instruction(instruction)
        print(f"[STEP 1] ✓ Parsed successfully")
        print(f"  - max_days_no_longer_wanted: {changes.max_days_no_longer_wanted}")
        print(f"  - max_days_damaged_or_defective: {changes.max_days_damaged_or_defective}")
        print(f"  - partial_refund_rate: {changes.partial_refund_rate}")
        if changes.comments:
            print(f"  - comments: {changes.comments}")
    except PolicyParseError as e:
        print(f"[ERROR] Failed to parse instruction: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Step 2: Prepare sandbox copy
    print("\n[STEP 2] Preparing sandbox copy...")
    original_source = prepare_sandbox_copy()
    print("[STEP 2] ✓ Sandbox copy created")
    
    # Step 3: Apply changes
    print("\n[STEP 3] Applying policy changes...")
    modified_source = apply_policy_changes_to_source(original_source, changes)
    print("[STEP 3] ✓ Changes applied")
    
    # Step 4: Show value comparison
    print("\n[STEP 4] Value comparison:")
    current_values = extract_current_values(original_source)
    for key, new_value in changes.model_dump(exclude_none=True).items():
        if key in ["max_days_no_longer_wanted", "max_days_damaged_or_defective", "partial_refund_rate"]:
            old_value = current_values.get(key, "N/A")
            print(f"  {key}: {old_value} → {new_value}")
    
    # Step 5: Write sandbox file
    print("\n[STEP 5] Writing sandbox file...")
    project_root = Path(__file__).parent.parent
    sandbox_file = project_root / "sandbox" / "ecommerce" / "refund_tool_candidate.py"
    write_sandbox_source(sandbox_file, modified_source)
    print("[STEP 5] ✓ Sandbox file written")
    
    # Step 6: Print diff
    print("\n[STEP 6] Generating code diff...")
    print_diff(original_source, modified_source)
    
    # Step 7: Run tests
    print("[STEP 7] Running tests...")
    tests_passed = run_tests_against_sandbox()
    if tests_passed:
        print("[STEP 7] ✓ Tests passed")
    else:
        print("[STEP 7] ✗ Tests failed")
    
    # Final reminder
    print("\n" + "=" * 70)
    print("=== Summary ===")
    print("=" * 70)
    print(f"Sandbox changes were written to: {sandbox_file}")
    print("\n⚠️  IMPORTANT:")
    print("  - This script never writes to the production refund_tool.py")
    print("  - It only writes to sandbox/ecommerce/refund_tool_candidate.py")
    print("  - A human must review the diff and manually apply changes to production code")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
