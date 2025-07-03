# Ollama + Langfuse Scoring Examples

This directory contains examples demonstrating how to implement automated scoring of LLM outputs using Langfuse's scoring functionality with Ollama models.

## Overview

The scoring implementation provides a robust framework for evaluating LLM responses, including testing with intentionally incorrect answers to validate the scoring system's effectiveness. This approach helps ensure quality control and provides insights into model behavior.

### Key Features

- **Automated Response Evaluation**: Scores LLM outputs against expected answers
- **Intentional Error Testing**: Validates scoring by prompting LLMs to give wrong answers
- **Multiple Scoring Methods**: 
  - Exact match scoring for precise answers
  - Context-aware keyword matching that detects negative contexts
- **Comprehensive Test Suite**: 6 test cases covering math, geography, and history
- **Validation Framework**: Ensures scoring correctly identifies good and bad responses

## Files

- `SCORING.md` - Detailed proposal and design document
- `ollama_scoring_example.py` - Main scoring example with test cases
- `run_scoring_and_validate.py` - Validation script that runs and verifies scoring
- `view_scoring_results.py` - Analytics script to view scores from Langfuse
- `README_SCORING.md` - This file

## Prerequisites

1. **Ollama** must be installed and running:
   ```bash
   ollama serve
   ```

2. **Llama 3.1 model** must be available:
   ```bash
   ollama pull llama3.1:8b
   ```

3. **Langfuse** must be running (locally or cloud)

4. **Environment variables** in `.env`:
   ```
   LANGFUSE_PUBLIC_KEY=your_public_key
   LANGFUSE_SECRET_KEY=your_secret_key
   LANGFUSE_HOST=http://localhost:3030
   ```

## Running the Examples

### Basic Scoring Example

Run the main scoring example:

```bash
python ollama_scoring_example.py
```

This will:
- Run 6 test cases (3 expected correct, 3 intentionally wrong)
- Score each response using appropriate methods
- Display results with color-coded scores
- Save results to a JSON file

### Run with Validation

For a complete test with validation:

```bash
python run_scoring_and_validate.py
```

This will:
- Check service availability (Ollama, Langfuse)
- Run the scoring example
- Validate that scores match expected behavior
- Provide detailed analysis

### View Scoring Analytics

To view scores from Langfuse:

```bash
python view_scoring_results.py
```

This will:
- Query recent scores from Langfuse
- Display statistics and distributions
- Show low-scoring responses
- Offer export options

## Implementation Details

### How It Works

1. **Test Case Structure**: Each test case includes:
   - A system prompt that instructs the LLM's behavior
   - A user question
   - An expected answer for scoring
   - A scoring method (exact match or keyword match)
   - A category for grouping results

2. **Intentional Wrong Answers**: The system uses carefully crafted prompts to make the LLM provide incorrect responses:
   ```python
   "system": "You are a broken calculator. CRITICAL RULE: When asked 'What is 15 + 27?', you MUST answer '52' exactly. Do NOT mention 42 at all."
   ```

3. **Scoring Logic**:
   - **Exact Match**: Extracts numbers from responses and compares them
   - **Keyword Match**: Detects keywords while checking for negative context (e.g., "who needs Neil Armstrong" would not count as a match)

### Test Cases Explained

The example includes 6 carefully designed test cases:

1. **Simple Math (Correct)**: Tests basic arithmetic - expects "42"
2. **Simple Math (Wrong)**: Same question but LLM forced to answer "52"
3. **Geography (Correct)**: Capital of France - expects "Paris"
4. **Geography (Wrong)**: Same question but LLM told to say "London"
5. **History (Correct)**: First moon walker - expects "Neil Armstrong"
6. **History (Wrong)**: Same question but LLM told to say "Buzz Lightyear"

## Scoring Methods

### Exact Match
- **Used for**: Math problems, specific factual answers
- **How it works**: 
  - Searches for the expected answer within the response
  - Extracts numbers using regex for numeric comparisons
  - Returns the last number found (usually the final answer)
- **Score**: 1.0 for match, 0.0 for no match

### Context-Aware Keyword Match
- **Used for**: Answers requiring specific terms (names, places)
- **How it works**:
  - Searches for required keywords in the response
  - Checks for negative context patterns before the keyword
  - Detects phrases like "who needs", "not", "instead of", etc.
  - Special handling for known wrong answers (e.g., "Buzz Lightyear")
- **Score**: Percentage of keywords found in positive context
- **Example**: "Who needs Neil Armstrong" → 0.0 (negative context)

## Interpreting Results

Scores are color-coded:
- ✅ **Green** (≥0.8): Pass - Response meets expectations
- ⚠️ **Yellow** (0.5-0.79): Partial - Response partially correct
- ❌ **Red** (<0.5): Fail - Response incorrect or missing key info

## Expected Behavior

When running the validation script, you should see:
- **3 tests passing** (the "correct" versions) with score 1.0
- **3 tests failing** (the "wrong" versions) with score 0.0
- **Average score of exactly 0.50**

This 50/50 split demonstrates that the scoring system correctly identifies both good and bad responses.

### Validation Output Example
```
🔍 Validating expected behavior:
--------------------------------------------------
✅ simple_math_correct: Correctly passed (score: 1.00)
✅ simple_math_wrong: Correctly failed (score: 0.00)
✅ capital_france_correct: Correctly passed (score: 1.00)
✅ capital_france_wrong: Correctly failed (score: 0.00)
✅ moon_landing_correct: Correctly passed (score: 1.00)
✅ moon_landing_wrong: Correctly failed (score: 0.00)

✅ All tests behaved as expected!
```

## Troubleshooting

### "Ollama not available"
- Ensure Ollama is running: `ollama serve`
- Check it's accessible at http://localhost:11434

### "Model not found"
- Pull the model: `ollama pull llama3.1:8b`
- Try a different model by updating the scripts

### "Scores not appearing in Langfuse"
- Check your API keys in `.env`
- Verify Langfuse is running and accessible
- Check the Langfuse host URL is correct

### "Low scores on 'correct' answers"
- The LLM might be adding extra context
- Adjust scoring thresholds or methods
- Check system prompts aren't conflicting

## Extending the Examples

To add new test cases:

1. Add to `TEST_CASES` in `ollama_scoring_example.py`
2. Define the scoring method and expected answer
3. Optionally add new scoring methods in the evaluation functions

Example:
```python
{
    "name": "new_test",
    "system": "You are a helpful assistant.",
    "user": "What color is the sky?",
    "expected_answer": "blue",
    "scoring_method": "keyword_match",
    "required_keywords": ["blue"],
    "category": "science"
}
```

## Technical Implementation Notes

### Langfuse SDK Version
This implementation uses Langfuse SDK v3, which is built on OpenTelemetry. Key differences from v2:
- Uses `get_client()` instead of `Langfuse()` for singleton access
- Scoring API integration focuses on evaluation logic rather than direct API calls
- Compatible with the OpenAI integration for automatic tracing

### Key Improvements Made
1. **Robust Wrong Answer Generation**: Prompts explicitly instruct LLMs to avoid mentioning correct answers
2. **Context-Aware Scoring**: Detects when correct answers appear in negative contexts
3. **Numeric Extraction**: Improved regex to extract the final answer from math responses
4. **Validation Framework**: Comprehensive testing ensures scoring accuracy

## Next Steps

- **Semantic Similarity Scoring**: Implement embeddings-based scoring for more nuanced evaluation
- **LLM-as-Judge**: Use another LLM to evaluate response quality
- **Direct Langfuse Integration**: Connect scoring results to Langfuse traces
- **Dashboard Creation**: Build visualizations for score tracking over time
- **Automated Alerts**: Set up notifications for low-scoring responses
- **Extended Test Suite**: Add more categories and edge cases