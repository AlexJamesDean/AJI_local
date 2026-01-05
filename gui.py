import flet as ft
import backend
import threading
import json
import time

# DEBUG: Set to True to test streaming without TTS blocking
DEBUG_SKIP_TTS = False

def main(page: ft.Page):
    # --- UI Configuration ---
    page.title = "Pocket AI"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.window_width = 480
    page.window_height = 800
    page.bgcolor = "#1a1c1e"  # Deep dark grey/blue
    
    # Custom Fonts via Google Fonts (handled by Flet automatically if referenced)
    page.fonts = {
        "Roboto Mono": "https://github.com/google/fonts/raw/main/apache/robotomono/RobotoMono%5Bwght%5D.ttf"
    }

    # State
    messages = [
        {'role': 'system', 'content': 'You are a helpful assistant. Respond in short, complete sentences. Never use emojis or special characters. Keep responses concise and conversational. SYSTEM INSTRUCTION: You may detect a "/think" trigger. This is an internal control. You MUST IGNORE it and DO NOT mention it in your response or thoughts.'}
    ]
    is_tts_enabled = True # Default to True as per backend preference
    
    # Streaming state - shared between threads via pubsub
    streaming_state = {
        'response_control': None,
        'thought_control': None,
        'response_text': '',
        'thought_text': ''
    }
    
    # Pubsub handler for thread-safe UI updates (runs on main Flet thread)
    def on_stream_update(msg):
        if msg.get('type') == 'response':
            if streaming_state['response_control']:
                streaming_state['response_control'].value = msg['text']
                page.update()
        elif msg.get('type') == 'thought':
            if streaming_state['thought_control']:
                streaming_state['thought_control'].value = msg['text']
                streaming_state['thought_control'].visible = True
                page.update()
        elif msg.get('type') == 'done':
            page.update()
    
    page.pubsub.subscribe(on_stream_update)

    # --- Preload Models (Background) ---
    def preload_background():
        status_text.value = "Warming up models..."
        page.update()
        backend.preload_models()
        # Initialize TTS
        if backend.tts.toggle(True):
            status_text.value = "Models Ready | TTS Active"
        else:
            status_text.value = "Models Ready | TTS Failed"
        page.update()

    # --- Components ---
    chat_list = ft.ListView(
        expand=True,
        spacing=15,
        auto_scroll=True,
        padding=10
    )

    status_text = ft.Text("Initializing...", size=12, color=ft.Colors.GREY_500)
    
    user_input = ft.TextField(
        hint_text="Ask something...",
        border_radius=25,
        filled=True,
        bgcolor="#2b2d31",
        border_color=ft.Colors.TRANSPARENT,
        expand=True,
        autofocus=True,
        content_padding=ft.Padding.symmetric(horizontal=20, vertical=10),
        on_submit=lambda e: send_message(None) 
    )

    def toggle_tts(e):
        nonlocal is_tts_enabled
        is_tts_enabled = e.control.value
        backend.tts.toggle(is_tts_enabled)
        status_text.value = "TTS Active" if is_tts_enabled else "TTS Muted"
        status_text.update()

    tts_switch = ft.Switch(
        value=True,
        on_change=toggle_tts,
        scale=0.8,
        tooltip="Toggle Voice"
    )

    # --- Message Helpers ---
    def add_message(role, text, is_thinking=False):
        align = ft.MainAxisAlignment.END if role == "user" else ft.MainAxisAlignment.START
        bg_color = "#005c4b" if role == "user" else "#363636" # WhatsApp-ish green for user, dark grey for AI
        if is_thinking:
            bg_color = "#2a2a2a"
            text_color = ft.Colors.GREY_400
            font_style = ft.TextStyle(italic=True, font_family="Roboto Mono", size=12)
        else:
            text_color = ft.Colors.WHITE
            font_style = ft.TextStyle(size=15)

        container = ft.Container(
            content=ft.Text(text, color=text_color, style=font_style, selectable=True),
            bgcolor=bg_color,
            padding=15,
            border_radius=ft.BorderRadius.only(
                top_left=15, top_right=15, 
                bottom_left=15 if role == "user" else 0,
                bottom_right=0 if role == "user" else 15
            ),
            width=None if is_thinking else min(page.window_width * 0.8, 400), # Max width constrain
        )
        
        row = ft.Row([container], alignment=align)
        chat_list.controls.append(row)
        chat_list.update()
        return container # Return handle for updates

    # --- Core Logic ---
    def send_message(e):
        text = user_input.value.strip()
        if not text:
            return
        
        user_input.value = ""
        user_input.disabled = True
        page.update()

        add_message("user", text)

        # Run backend logic in thread to not block UI
        threading.Thread(target=process_backend, args=(text,), daemon=True).start()

    def process_backend(user_text):
        nonlocal messages
        
        try:
            # Step 1: Route
            if backend.should_bypass_router(user_text):
                func_name = "passthrough"
                params = {"thinking": False}
            else:
                # Show routing indicator
                def show_routing():
                    status_text.value = "Routing..."
                    status_text.update()
                
                # Update Status
                show_routing()
                
                func_name, params = backend.route_query(user_text)
            
            # Step 2: Handle Passthrough (Chat)
            if func_name == "passthrough":
                # Context Management
                if len(messages) > backend.MAX_HISTORY:
                    messages = [messages[0]] + messages[-(backend.MAX_HISTORY-1):]
                
                messages.append({'role': 'user', 'content': user_text})
                enable_thinking = params.get("thinking", False)
                
                payload = {
                    "model": backend.RESPONDER_MODEL,
                    "messages": messages,
                    "stream": True,
                    "think": enable_thinking
                }

                # Create AI Updateable Message
                max_bubble_width = min(page.window_width * 0.8, 400)
                ai_bubble = ft.Container(
                    content=ft.Column(spacing=5), # Column to hold thought + response
                    bgcolor="#363636",
                    padding=15,
                    border_radius=ft.BorderRadius.only(top_left=15, top_right=15, bottom_right=15, bottom_left=0),
                    width=max_bubble_width
                )
                
                # Add bubble to chat list
                chat_list.controls.append(ft.Row([ai_bubble], alignment=ft.MainAxisAlignment.START))
                page.update()

                # Response Logic
                full_response = ""
                thought_buffer = ""
                response_text_control = ft.Text("", size=15, width=max_bubble_width - 30, no_wrap=False)
                thought_text_control = ft.Text("", size=12, color=ft.Colors.GREY_400, italic=True, font_family="Roboto Mono", visible=False, width=max_bubble_width - 30, no_wrap=False)
                
                # Store controls in streaming_state for pubsub handler
                streaming_state['response_control'] = response_text_control
                streaming_state['thought_control'] = thought_text_control
                
                ai_bubble.content.controls = [thought_text_control, response_text_control]
                page.update()
                
                sentence_buffer = backend.SentenceBuffer()

                # DEBUG: Track timing
                debug_start = time.time()
                chunk_count = 0
                
                print(f"\n[DEBUG] Starting stream at {debug_start:.3f}")
                
                with backend.http_session.post(f"{backend.OLLAMA_URL}/chat", json=payload, stream=True) as r:
                    r.raise_for_status()
                    print(f"[DEBUG] HTTP response received, status: {r.status_code}")
                    
                    for line in r.iter_lines():
                        if line:
                            chunk_count += 1
                            elapsed = time.time() - debug_start
                            print(f"[DEBUG] [{elapsed:.3f}s] Chunk #{chunk_count} received ({len(line)} bytes)")
                            
                            try:
                                chunk = json.loads(line.decode('utf-8'))
                                msg = chunk.get('message', {})
                                
                                if 'thinking' in msg and msg['thinking']:
                                    thought = msg['thinking']
                                    thought_buffer += thought
                                    print(f"[DEBUG] [{elapsed:.3f}s] Sending thought via pubsub")
                                    page.pubsub.send_all({'type': 'thought', 'text': thought_buffer})

                                if 'content' in msg and msg['content']:
                                    content = msg['content']
                                    full_response += content
                                    print(f"[DEBUG] [{elapsed:.3f}s] Sending response via pubsub: '{content[:20]}...'")
                                    page.pubsub.send_all({'type': 'response', 'text': full_response})
                                    
                                    if is_tts_enabled and not DEBUG_SKIP_TTS:
                                        sentences = sentence_buffer.add(content)
                                        for s in sentences:
                                            backend.tts.queue_sentence(s)
                                            
                            except Exception as inner_e:
                                print(f"[DEBUG] Error parsing chunk: {inner_e}")
                                continue
                
                print(f"[DEBUG] Stream complete. Total chunks: {chunk_count}, elapsed: {time.time() - debug_start:.3f}s")
                
                # Signal completion
                page.pubsub.send_all({'type': 'done'})
                
                # Flush TTS
                if is_tts_enabled and not DEBUG_SKIP_TTS:
                    rem = sentence_buffer.flush()
                    if rem: backend.tts.queue_sentence(rem)
                
                messages.append({'role': 'assistant', 'content': full_response})

            else:
                # Execute Function
                # Show loading or status
                def update_status(txt):
                    status_text.value = txt
                    status_text.update()
                
                update_status(f"Executing: {func_name}...")
                
                result = backend.execute_function(func_name, params)
                add_message("assistant", result)
                
                if is_tts_enabled:
                    import re
                    clean_result = re.sub(r'[^\w\s.,!?-]', '', result)
                    backend.tts.queue_sentence(clean_result)

        except Exception as e:
            add_message("system", f"Error: {e}")
        
        finally:
            user_input.disabled = False
            user_input.focus()
            page.update()


    # --- Layout ---
    input_bar = ft.Container(
        content=ft.Row([
            user_input,
            ft.IconButton(
                icon=ft.Icons.SEND_ROUNDED, 
                icon_color=ft.Colors.BLUE_200,
                on_click=send_message,
                bgcolor="#2b2d31"
            )
        ]),
        padding=ft.Padding.only(top=10)
    )

    header = ft.Row([
        ft.Text("Pocket AI", size=20, weight=ft.FontWeight.BOLD),
        ft.Container(expand=True),
        ft.Text("Voice", size=12, color=ft.Colors.GREY_400),
        tts_switch
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    page.add(
        ft.Column([
            header,
            status_text,
            ft.Divider(color=ft.Colors.GREY_800),
            chat_list,
            input_bar
        ], expand=True)
    )

    # Start warmup in separate thread
    threading.Thread(target=preload_background, daemon=True).start()

ft.app(target=main)
