import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from core.function_executor import FunctionExecutor

def test_dates():
    executor = FunctionExecutor()
    
    dates_to_test = [
        ("today", "2026-01-16"), # Assuming today is 2026-01-16 based on context
        ("tomorrow", "2026-01-17"),
        ("2025-12-25", "2025-12-25"),
    ]
    
    print("Verifying FunctionExecutor._parse_date fixes:")
    for date_input, expected in dates_to_test:
        result = executor._parse_date(date_input)
        status = "PASS" if result == expected else f"FAIL (Expected {expected}, got {result})"
        print(f"Input: '{date_input}' -> {status}")

if __name__ == "__main__":
    test_dates()
