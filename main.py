import requests
import json
import sys

# ANSI Escape Codes for coloring output
GRAY = "\033[90m"
RESET = "\033[0m"
BOLD = "\033[1m"

def main():
    # Default State
    thinking_mode = False
    
    print(f"{BOLD}Pocket AI (Qwen3-1.7B) - DeepSeek Style{RESET}")
    print("---------------------------------------------")
    print(f"Commands:")
    print(f"  /think on   -> {GRAY}Show internal reasoning{RESET}")
    print(f"  /think off  -> Hide reasoning (Faster/Cleaner)")
    print(f"  exit        -> Quit")
    print("---------------------------------------------\n")
    
    messages = [
        {'role': 'system', 'content': 'You are a helpful assistant.'}
    ]
    
    url = "http://localhost:11434/api/chat"
    
    while True:
        try:
            # Visual indicator of current mode
            mode_text = f"{GRAY}(Thinking){RESET}" if thinking_mode else "(Fast)"
            user_input = input(f"You {mode_text}: ")
            
            if not user_input: continue
            
            # --- Command Handling ---
            if user_input.strip().lower() == "/think on":
                thinking_mode = True
                print(f">> System: Thinking {BOLD}ENABLED{RESET}. You will see the reasoning process.")
                continue
                
            if user_input.strip().lower() == "/think off":
                thinking_mode = False
                print(f">> System: Thinking {BOLD}DISABLED{RESET}.")
                continue

            if user_input.lower() in ['exit', 'quit']:
                print("Goodbye!")
                break
                
            messages.append({'role': 'user', 'content': user_input})
            
            # --- The Request ---
            payload = {
                "model": "qwen3:1.7b",
                "messages": messages,
                "stream": True,
                "think": thinking_mode 
            }
            
            print("AI: ", end='', flush=True)
            
            # Trackers to handle newlines cleanly between Thought and Answer
            full_response = ""
            has_printed_thought = False
            
            with requests.post(url, json=payload, stream=True) as r:
                r.raise_for_status()
                
                for line in r.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line.decode('utf-8'))
                            
                            # Get the message object (if it exists)
                            msg = chunk.get('message', {})
                            
                            # 1. HANDLE THINKING TOKENS
                            # The API puts reasoning here now, not in 'content'
                            if 'thinking' in msg and msg['thinking']:
                                # Print in GRAY so it looks like a "thought bubble"
                                print(f"{GRAY}{msg['thinking']}{RESET}", end='', flush=True)
                                has_printed_thought = True

                            # 2. HANDLE ACTUAL CONTENT
                            if 'content' in msg and msg['content']:
                                # If we just finished thinking, add a newline to separate Thought from Answer
                                if has_printed_thought:
                                    print(f"{RESET}\n\n", end='', flush=True) 
                                    has_printed_thought = False # Reset flag so we don't print newlines forever
                                
                                # Print the answer normally
                                print(msg['content'], end='', flush=True)
                                full_response += msg['content']
                                
                        except json.JSONDecodeError:
                            continue
            
            print() # Final newline
            messages.append({'role': 'assistant', 'content': full_response})

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    main()