# Implementation Plan for Strands-Langfuse Reorganization

## Overview
Complete rewrite of the Strands-Langfuse demos to create a clean, modular structure with unified entry points and simplified imports.

## Phase 1: Core Infrastructure (Tasks 1-3)
**Goal**: Create the foundational modules that all demos will use

1. **Create core directory structure**
   - Create `core/` directory
   - Add `core/__init__.py`
   - Ensures module is importable

2. **Implement core/setup.py**
   - Extract OTEL initialization logic
   - `initialize_langfuse_telemetry()` function
   - `setup_telemetry(service_name)` function
   - Must be called before importing Strands Agent

3. **Implement core/agent_factory.py**
   - `create_bedrock_model()` function
   - `create_agent()` function with trace attributes
   - Standardizes agent creation across all demos

## Phase 2: Demo Modules (Tasks 4-7)
**Goal**: Convert existing demos to modular format

4. **Create demos directory structure**
   - Create `demos/` directory
   - Add `demos/__init__.py`

5. **Implement demos/scoring.py**
   - Port logic from `strands_scoring_demo.py`
   - Export `run_demo(session_id=None)` function
   - Return `(session_id, trace_ids)` tuple
   - Maintain all test cases and scoring logic

6. **Implement demos/examples.py**
   - Port logic from `strands_langfuse_demo.py`
   - Include all example functions (chat, calculator, creative)
   - Export `run_demo(session_id=None)` function

7. **Implement demos/monty_python.py**
   - Port logic from `strands_monty_python_demo.py`
   - Maintain all the fun interactions
   - Export `run_demo(session_id=None)` function

## Phase 3: Main Entry Point (Task 8)
**Goal**: Create unified interface for running demos

8. **Create and test main.py**
   - Interactive menu system
   - Command-line argument support
   - Import and execute demo modules
   - Error handling and reporting

## Phase 4: Validation Scripts (Tasks 9-10)
**Goal**: Update validation to work with new structure

9. **Update run_and_validate.py**
   - Change to execute `main.py` instead of individual scripts
   - Support demo name parameter
   - Maintain trace validation logic

10. **Update run_scoring_and_validate.py**
    - Use `main.py scoring` command
    - Ensure scoring validation still works

## Phase 5: Lambda Integration (Tasks 11-12)
**Goal**: Create Lambda handler with demo selection

11. **Create lambda_handler.py**
    - Move to main directory for simpler imports
    - Support JSON field demo selection
    - Maintain custom query mode
    - Import demo modules directly

12. **Test lambda_handler.py**
    - Test each demo mode
    - Verify custom query mode
    - Check telemetry flushing
    - Validate response formats

## Phase 6: Infrastructure Updates (Tasks 13-15)
**Goal**: Update build and deployment for new structure

13. **Update lambda/build_lambda.py**
    - Adjust paths to package from new structure
    - Include `core/` and `demos/` directories
    - Copy `lambda_handler.py` from main directory

14. **Update lambda/requirements.txt**
    - Verify all dependencies are included
    - Add any new requirements

15. **Update CDK stack**
    - Update handler reference if needed
    - Ensure proper packaging

## Phase 7: Integration Testing (Task 16)
**Goal**: Verify entire system works end-to-end

16. **Test complete flow**
    - Run each demo via `main.py`
    - Validate traces are created
    - Test Lambda deployment
    - Verify all APIs work correctly

## Phase 8: Documentation & Cleanup (Tasks 17-18)
**Goal**: Update docs and remove old code

17. **Update documentation**
    - Update README.md with new usage
    - Update CLAUDE.md with new structure
    - Document API changes for Lambda

18. **Clean up old files**
    - Remove original demo files
    - Remove old Lambda handler
    - Archive any deprecated code

## Testing Strategy

### After Each Phase:
1. **Unit Testing**: Test individual functions
2. **Integration Testing**: Test module interactions
3. **Trace Validation**: Ensure Langfuse receives traces
4. **Error Handling**: Test failure scenarios

### Key Test Cases:
- Each demo runs successfully via `main.py`
- Lambda handler processes all demo types
- Validation scripts detect traces
- OTEL telemetry is properly initialized
- Import paths work correctly

## Rollback Plan
Since you're backing up the directory, we can always restore if needed. The new structure is completely separate from the old files until Phase 8.

## Success Criteria
1. All demos run via unified `main.py`
2. Lambda supports demo selection via JSON
3. No code duplication
4. Clean import structure
5. All validation scripts work
6. Documentation is updated
7. Traces appear in Langfuse as expected

## Notes
- The most critical part is Phase 1 - getting the OTEL initialization right
- Each demo module must follow the same pattern for consistency
- Lambda handler location in main directory simplifies the entire build process
- Keep the old files until everything is verified working