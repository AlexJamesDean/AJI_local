#!/usr/bin/env python3
"""
FunctionGemma Baseline Test (Pre-Fine-Tuning)
Uses proper FunctionGemma control tokens for accurate measurement.
"""

import requests
import re
import sys
from collections import defaultdict

MODEL = "functiongemma:270m"
URL = "http://localhost:11434/api/generate"

FUNCTIONS = {
    "control_light": {"desc": "Controls smart lights", "params": {"action": "on or off", "room": "room name"}},
    "set_thermostat": {"desc": "Sets temperature", "params": {"temperature": "number", "unit": "celsius or fahrenheit"}},
    "play_music": {"desc": "Plays music", "params": {"query": "song or artist", "source": "spotify or youtube"}},
    "set_alarm": {"desc": "Sets an alarm", "params": {"time": "time string", "label": "alarm label"}},
    "send_message": {"desc": "Sends a text message", "params": {"recipient": "contact name", "message": "text"}},
    "get_weather": {"desc": "Gets weather", "params": {"location": "city name"}},
    "create_reminder": {"desc": "Creates reminder", "params": {"task": "what to remind", "time": "when"}},
    "control_tv": {"desc": "Controls TV", "params": {"action": "on off or channel", "value": "optional value"}},
    "lock_door": {"desc": "Controls door locks", "params": {"door": "which door", "action": "lock or unlock"}},
    "order_food": {"desc": "Orders food", "params": {"restaurant": "restaurant name", "items": "what to order"}}
}

TEST_CASES = [
    {"prompt": "Turn on the bedroom lights", "expected": "control_light"},
    {"prompt": "Switch off the kitchen light", "expected": "control_light"},
    {"prompt": "Dim the living room lights", "expected": "control_light"},
    {"prompt": "Set the temperature to 72 degrees", "expected": "set_thermostat"},
    {"prompt": "Make it warmer, set thermostat to 75", "expected": "set_thermostat"},
    {"prompt": "Play some jazz music on Spotify", "expected": "play_music"},
    {"prompt": "Play Taylor Swift's latest album", "expected": "play_music"},
    {"prompt": "Set an alarm for 7 AM tomorrow", "expected": "set_alarm"},
    {"prompt": "Wake me up at 6:30 in the morning", "expected": "set_alarm"},
    {"prompt": "Text Mom that I'll be late for dinner", "expected": "send_message"},
    {"prompt": "Send a message to John saying hi", "expected": "send_message"},
    {"prompt": "What's the weather like in New York?", "expected": "get_weather"},
    {"prompt": "Is it going to rain in Tokyo today?", "expected": "get_weather"},
    {"prompt": "Remind me to call the dentist at 3 PM", "expected": "create_reminder"},
    {"prompt": "Create a reminder to pick up groceries", "expected": "create_reminder"},
    {"prompt": "Turn on the TV", "expected": "control_tv"},
    {"prompt": "Change the channel to ESPN", "expected": "control_tv"},
    {"prompt": "Lock the front door", "expected": "lock_door"},
    {"prompt": "Unlock the garage door", "expected": "lock_door"},
    {"prompt": "Order a pizza from Dominos", "expected": "order_food"},
]


def esc(s):
    """Wrap string with <escape> tokens."""
    return f"<escape>{s}<escape>"


def build_function_declarations():
    """Build function declarations using FunctionGemma control tokens."""
    declarations = ""
    for name, spec in FUNCTIONS.items():
        # Build params object
        params_props = ",".join([
            f"{k}:{{description:{esc(v)},type:{esc('STRING')}}}" 
            for k, v in spec["params"].items()
        ])
        required = ",".join([esc(k) for k in spec["params"].keys()])
        
        declarations += (
            f"<start_function_declaration>"
            f"declaration:{name}{{"
            f"description:{esc(spec['desc'])},"
            f"parameters:{{properties:{{{params_props}}},required:[{required}],type:{esc('OBJECT')}}}"
            f"}}<end_function_declaration>"
        )
    return declarations


def build_prompt(user_query):
    """Build prompt using FunctionGemma's exact format."""
    declarations = build_function_declarations()
    
    return (
        f"<start_of_turn>developer "
        f"You are a model that can do function calling with the following functions"
        f"{declarations}"
        f"<end_of_turn>\n"
        f"<start_of_turn>user {user_query}<end_of_turn>\n"
        f"<start_of_turn>model"
    )


def extract_function(response):
    """Extract function name from FunctionGemma response."""
    # Pattern: <start_function_call>call:function_name{...}
    match = re.search(r"call:(\w+)", response)
    if match:
        return match.group(1)
    
    # Fallback: check for function names in response
    for func in FUNCTIONS:
        if func in response:
            return func
    return None


def run_test(prompt, verbose=False):
    """Run test using generate API for raw token control."""
    full_prompt = build_prompt(prompt)
    
    if verbose:
        print(f"\n--- PROMPT ---\n{full_prompt[:500]}...\n")
    
    payload = {
        "model": MODEL,
        "prompt": full_prompt,
        "stream": False,
        "raw": True,  # Use raw mode to preserve tokens
        "options": {
            "temperature": 0.0,
            "seed": 42,
            "num_predict": 150,
            "stop": ["<end_of_turn>", "<start_function_response>"]
        }
    }
    
    try:
        r = requests.post(URL, json=payload, timeout=30)
        return r.json().get("response", "")
    except Exception as e:
        return f"ERROR: {e}"


def main():
    print("=" * 70)
    print(f"FunctionGemma Baseline Test | Model: {MODEL}")
    print("Using proper FunctionGemma control tokens")
    print("=" * 70)
    
    # Show sample prompt/response
    print("\n📋 Sample (first test case):")
    sample = run_test(TEST_CASES[0]["prompt"], verbose=True)
    print(f"Response: {sample[:200]}")
    print("-" * 70)
    
    correct = 0
    results = []
    by_func = defaultdict(lambda: {"total": 0, "correct": 0})
    
    for i, test in enumerate(TEST_CASES):
        sys.stdout.write(f"\rTesting {i+1}/{len(TEST_CASES)}...")
        sys.stdout.flush()
        
        response = run_test(test["prompt"])
        called = extract_function(response)
        expected = test["expected"]
        is_correct = called == expected
        
        if is_correct:
            correct += 1
        
        by_func[expected]["total"] += 1
        if is_correct:
            by_func[expected]["correct"] += 1
            
        results.append({
            "prompt": test["prompt"], 
            "expected": expected,
            "called": called, 
            "correct": is_correct, 
            "raw": response
        })
    
    print("\r" + " " * 30)
    
    # Results table with full output
    print(f"\n{'='*80}")
    for i, r in enumerate(results):
        status = "✓" if r["correct"] else "✗"
        print(f"\n[{i+1}] {status} {r['prompt']}")
        print(f"    Expected: {r['expected']:<16} Got: {r['called'] or 'None'}")
        print(f"    Raw: {r['raw']}")
    
    accuracy = (correct / len(TEST_CASES)) * 100
    print("-" * 80)
    print(f"\n🎯 BASELINE ACCURACY: {correct}/{len(TEST_CASES)} ({accuracy:.1f}%)")
    
    print("\nBy Function:")
    for func, stats in sorted(by_func.items()):
        pct = (stats["correct"] / stats["total"]) * 100 if stats["total"] > 0 else 0
        bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
        print(f"  {func:<16} [{bar}] {stats['correct']}/{stats['total']}")
    
    # Show some raw responses for debugging
    print("\n📝 Sample raw responses:")
    for r in results[:3]:
        print(f"  '{r['prompt'][:30]}...' → '{r['raw']}'")
    
    print("\n" + "=" * 70)
    print("📝 Save this baseline, then run again after fine-tuning!")
    print("=" * 70)


if __name__ == "__main__":
    main()
