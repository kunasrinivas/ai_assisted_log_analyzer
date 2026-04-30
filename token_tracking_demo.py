#!/usr/bin/env python3
"""
Token Tracking Demo & Test Script

Run this to understand and test token tracking without full GUI.

Usage:
  python token_tracking_demo.py
"""

from src.token_cost_tracker import TokenUsageMetrics, format_cost_human_readable, format_efficiency_grade


def demo_basic_metrics():
    """Demo: Create and display basic token metrics."""
    print("=" * 70)
    print("DEMO 1: Basic Token Metrics")
    print("=" * 70)
    
    # Simulate a response from gpt-4o
    metrics = TokenUsageMetrics(
        prompt_tokens=450,
        completion_tokens=85,
        model="gpt-4o",
        question_length=35,
        answer_length=950,
    )
    
    print(f"\nModel: {metrics.model}")
    print(f"Prompt tokens: {metrics.prompt_tokens:,}")
    print(f"Completion tokens: {metrics.completion_tokens:,}")
    print(f"Total tokens: {metrics.total_tokens:,}")
    print(f"\nQuestion length: {metrics.question_length} chars")
    print(f"Answer length: {metrics.answer_length} chars")
    
    # Display as JSON
    print("\n--- Response Payload (to UI) ---")
    import json
    print(json.dumps(metrics.to_dict(), indent=2))


def demo_cost_comparison():
    """Demo: Compare costs across different models."""
    print("\n" + "=" * 70)
    print("DEMO 2: Cost Comparison Across Models")
    print("=" * 70)
    
    models = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-35-turbo"]
    
    # Same response metrics, different models
    prompt_tokens = 450
    completion_tokens = 85
    
    print(f"\nAssuming: {prompt_tokens} prompt tokens, {completion_tokens} completion tokens\n")
    print(f"{'Model':<20} {'Input Cost':<15} {'Output Cost':<15} {'Total Cost':<15}")
    print("-" * 65)
    
    for model in models:
        metrics = TokenUsageMetrics(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            model=model,
        )
        cost = metrics.cost()
        total = cost["total_cost_usd"]
        input_c = cost["input_cost_usd"]
        output_c = cost["output_cost_usd"]
        
        print(f"{model:<20} {format_cost_human_readable(input_c):<15} {format_cost_human_readable(output_c):<15} {format_cost_human_readable(total):<15}")


def demo_efficiency_grades():
    """Demo: Show efficiency grades based on different token/char ratios."""
    print("\n" + "=" * 70)
    print("DEMO 3: Efficiency Grading")
    print("=" * 70)
    
    test_cases = [
        {"name": "Excellent (A)", "completion_tokens": 100, "answer_length": 2500},  # 0.04
        {"name": "Good (B)", "completion_tokens": 150, "answer_length": 1800},         # 0.083
        {"name": "Fair (C)", "completion_tokens": 200, "answer_length": 1500},         # 0.133
        {"name": "Poor (D)", "completion_tokens": 300, "answer_length": 1500},         # 0.20
        {"name": "Very Poor (F)", "completion_tokens": 500, "answer_length": 1500},    # 0.333
    ]
    
    print("\n" + f"{'Case':<20} {'Tokens':<12} {'Chars':<12} {'Ratio':<12} {'Grade':<20}")
    print("-" * 75)
    
    for case in test_cases:
        metrics = TokenUsageMetrics(
            prompt_tokens=450,
            completion_tokens=case["completion_tokens"],
            model="gpt-4o",
            answer_length=case["answer_length"],
        )
        
        eff = metrics._efficiency_metrics()
        ratio = eff.get("tokens_per_answer_char", 0)
        
        # Grade it
        if ratio < 0.05:
            grade = "A - Excellent 🌟"
        elif ratio < 0.10:
            grade = "B - Good ✓"
        elif ratio < 0.15:
            grade = "C - Fair"
        elif ratio < 0.25:
            grade = "D - Poor"
        else:
            grade = "F - Very Poor"
        
        print(f"{case['name']:<20} {case['completion_tokens']:<12} {case['answer_length']:<12} {ratio:<12.3f} {grade:<20}")


def demo_large_scale_cost():
    """Demo: Calculate costs for large-scale usage."""
    print("\n" + "=" * 70)
    print("DEMO 4: Large-Scale Monthly Cost Estimation")
    print("=" * 70)
    
    # Estimate: 1000 questions per day, avg 500 prompt tokens, 100 completion tokens
    questions_per_day = 1000
    days_per_month = 30
    questions_per_month = questions_per_day * days_per_month
    
    prompt_tokens_per_q = 500
    completion_tokens_per_q = 100
    
    total_prompt = questions_per_month * prompt_tokens_per_q
    total_completion = questions_per_month * completion_tokens_per_q
    
    print(f"\nAssumptions:")
    print(f"  - {questions_per_day:,} questions/day")
    print(f"  - {questions_per_month:,} questions/month")
    print(f"  - {prompt_tokens_per_q:,} prompt tokens/question")
    print(f"  - {completion_tokens_per_q:,} completion tokens/question")
    
    print(f"\nMonthly totals:")
    print(f"  - Total prompt tokens: {total_prompt:,}")
    print(f"  - Total completion tokens: {total_completion:,}")
    
    print(f"\n{'Model':<20} {'Monthly Cost':<20} {'Cost/Question':<20}")
    print("-" * 60)
    
    for model in ["gpt-4o", "gpt-4o-mini", "gpt-35-turbo"]:
        metrics = TokenUsageMetrics(
            prompt_tokens=total_prompt,
            completion_tokens=total_completion,
            model=model,
        )
        cost = metrics.cost()
        total_cost = cost["total_cost_usd"]
        cost_per_q = total_cost / questions_per_month
        
        print(f"{model:<20} {format_cost_human_readable(total_cost):<20} {format_cost_human_readable(cost_per_q):<20}")


def demo_efficiency_optimization():
    """Demo: Show impact of optimization on costs."""
    print("\n" + "=" * 70)
    print("DEMO 5: Optimization Impact Analysis")
    print("=" * 70)
    
    print("\nScenario: Optimize system prompt to reduce verbosity by 20%")
    
    baseline = TokenUsageMetrics(
        prompt_tokens=450,
        completion_tokens=100,
        model="gpt-4o",
        answer_length=950,
    )
    
    optimized = TokenUsageMetrics(
        prompt_tokens=400,  # 50 tokens less context (better filtering)
        completion_tokens=80,  # 20% fewer tokens (more concise prompt)
        model="gpt-4o",
        answer_length=760,  # 20% shorter answer
    )
    
    baseline_cost = baseline.cost()["total_cost_usd"]
    optimized_cost = optimized.cost()["total_cost_usd"]
    savings = baseline_cost - optimized_cost
    savings_pct = (savings / baseline_cost) * 100
    
    print(f"\n{'Metric':<30} {'Baseline':<20} {'Optimized':<20} {'Change':<20}")
    print("-" * 90)
    print(f"{'Prompt tokens':<30} {baseline.prompt_tokens:<20} {optimized.prompt_tokens:<20} {optimized.prompt_tokens - baseline.prompt_tokens:>+20}")
    print(f"{'Completion tokens':<30} {baseline.completion_tokens:<20} {optimized.completion_tokens:<20} {optimized.completion_tokens - baseline.completion_tokens:>+20}")
    print(f"{'Answer length':<30} {baseline.answer_length:<20} {optimized.answer_length:<20} {optimized.answer_length - baseline.answer_length:>+20}")
    print(f"{'Total cost':<30} {format_cost_human_readable(baseline_cost):<20} {format_cost_human_readable(optimized_cost):<20} {format_cost_human_readable(savings):<20}")
    print(f"{'Cost savings':<30} {'':<20} {'':<20} {savings_pct:.1f}%")
    
    print(f"\n💡 By optimizing context and prompt, you save {format_cost_human_readable(savings)}")
    print(f"   across {100} questions per month!")


if __name__ == "__main__":
    try:
        demo_basic_metrics()
        demo_cost_comparison()
        demo_efficiency_grades()
        demo_large_scale_cost()
        demo_efficiency_optimization()
        
        print("\n" + "=" * 70)
        print("✅ Token tracking demo complete!")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Run: wsl bash scripts/run.sh")
        print("2. Visit: http://localhost:8080")
        print("3. Ask a question and see token metrics appear below the answer!")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
