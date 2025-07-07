#!/usr/bin/env python3
"""
Cleanup script for Langfuse AWS deployment.
Removes all deployed resources and cleans up local configuration.
"""

import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path


def run_command(cmd, check=True):
    """Run a shell command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result


def run_command_with_progress(cmd, description="Processing"):
    """Run a command with live output and progress indication."""
    print(f"Running: {cmd}")
    
    # Start the command
    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    # Progress indicator
    spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    spinner_idx = 0
    
    def update_status():
        nonlocal spinner_idx
        while process.poll() is None:
            print(f"\r{spinner[spinner_idx % len(spinner)]} {description}... ", end='', flush=True)
            spinner_idx += 1
            time.sleep(0.1)
    
    # Start status thread
    status_thread = threading.Thread(target=update_status)
    status_thread.daemon = True
    status_thread.start()
    
    # Collect output
    output_lines = []
    error_lines = []
    
    # Read stdout
    for line in process.stdout:
        output_lines.append(line)
        line = line.strip()
        
        # Parse CDK destroy progress
        if "Destroying" in line and "(" in line:
            # Clear the spinner line
            print("\r" + " " * 80 + "\r", end='', flush=True)
            print(f"   🔄 {line}")
        elif "✅" in line or ("destroyed" in line.lower() and "stack" in line.lower()):
            print("\r" + " " * 80 + "\r", end='', flush=True)
            print(f"   ✅ {line}")
        elif "❌" in line or "failed" in line.lower():
            print("\r" + " " * 80 + "\r", end='', flush=True)
            print(f"   ❌ {line}")
        elif "DELETE_IN_PROGRESS" in line:
            print("\r" + " " * 80 + "\r", end='', flush=True)
            stack_name = line.split()[0] if line.split() else "Stack"
            print(f"   🗑️  Deleting {stack_name}...")
        elif "DELETE_COMPLETE" in line:
            print("\r" + " " * 80 + "\r", end='', flush=True)
            stack_name = line.split()[0] if line.split() else "Stack"
            print(f"   ✅ {stack_name} deleted")
        elif "Currently in progress:" in line:
            print("\r" + " " * 80 + "\r", end='', flush=True)
            print(f"   ⏳ {line}")
        elif line.startswith("LangfuseAwsDeployment"):
            # Stack status updates
            print("\r" + " " * 80 + "\r", end='', flush=True)
            print(f"   📊 {line}")
    
    # Read any remaining stderr
    stderr_output = process.stderr.read()
    if stderr_output:
        error_lines.append(stderr_output)
    
    # Wait for process to complete
    process.wait()
    
    # Clear the spinner
    print("\r" + " " * 80 + "\r", end='', flush=True)
    
    return process.returncode, ''.join(output_lines), ''.join(error_lines)


def main():
    """Main cleanup function."""
    print("🧹 Starting Langfuse AWS cleanup...")
    
    # Check if CDK is installed
    cdk_check = run_command("cdk --version", check=False)
    if cdk_check.returncode != 0:
        print("❌ AWS CDK not found. Please install it first.")
        sys.exit(1)
    
    # Get list of stacks first
    print("\n📋 Checking deployed stacks...")
    list_result = run_command("cdk list", check=False)
    if list_result.returncode == 0 and list_result.stdout.strip():
        stacks = list_result.stdout.strip().split('\n')
        print(f"   Found {len(stacks)} stacks to destroy:")
        for stack in stacks:
            print(f"   - {stack}")
    else:
        print("   No CDK stacks found or unable to list stacks")
    
    # Destroy all CDK stacks
    print("\n📦 Destroying CDK stacks...")
    print("   This may take 15-20 minutes. Progress will be shown below:")
    print("   " + "-" * 60)
    
    returncode, stdout, stderr = run_command_with_progress(
        "cdk destroy --force --all",
        "Destroying stacks"
    )
    
    if returncode == 0:
        print("\n✅ CDK stacks destroyed successfully")
    else:
        print("\n⚠️  CDK destroy completed with warnings/errors")
        print("   Some resources may need manual cleanup in AWS console")
        if stderr:
            print("\n   Error details:")
            for line in stderr.split('\n'):
                if line.strip():
                    print(f"   {line}")
    
    # Clean up local files
    print("\n🗑️  Cleaning up local files...")
    
    # Remove generated files
    files_to_remove = [
        "cdk.context.json",
        ".env",
        "cdk.out"
    ]
    
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
                print(f"   Removed directory: {file_path}")
            else:
                os.remove(file_path)
                print(f"   Removed file: {file_path}")
    
    # Clean up Python cache
    cache_dirs = ["__pycache__", ".pytest_cache", ".mypy_cache"]
    for cache_dir in cache_dirs:
        for path in Path(".").rglob(cache_dir):
            shutil.rmtree(path)
            print(f"   Removed cache: {path}")
    
    # Remove .pyc files
    for pyc_file in Path(".").rglob("*.pyc"):
        pyc_file.unlink()
    
    print("\n✅ Cleanup completed!")
    print("\nNote: Please check AWS console to ensure all resources were removed.")
    print("     Some resources like CloudWatch logs may persist and incur minimal costs.")


if __name__ == "__main__":
    main()