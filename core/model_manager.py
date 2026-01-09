"""
Model Manager - Utilities for loading/unloading Ollama models.
"""

import requests
import threading
from config import OLLAMA_URL, GRAY, RESET


def unload_model(model_name: str):
    """
    Unload a model from Ollama to free up VRAM.
    Uses keep_alive=0 to immediately unload.
    """
    def _unload():
        try:
            # Send a request with keep_alive=0 to unload
            response = requests.post(
                f"{OLLAMA_URL}/generate",
                json={
                    "model": model_name,
                    "prompt": "",
                    "keep_alive": 0  # Immediately unload
                },
                timeout=5
            )
            if response.status_code == 200:
                print(f"{GRAY}[ModelManager] Unloaded model: {model_name}{RESET}")
            else:
                print(f"{GRAY}[ModelManager] Failed to unload {model_name}: {response.status_code}{RESET}")
        except Exception as e:
            print(f"{GRAY}[ModelManager] Error unloading {model_name}: {e}{RESET}")
    
    # Run in background to not block UI
    threading.Thread(target=_unload, daemon=True).start()


def unload_all_models():
    """Unload all running models in Ollama."""
    try:
        response = requests.get(f"{OLLAMA_URL}/ps", timeout=2)
        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            for model in models:
                model_name = model.get("name", "")
                if model_name:
                    unload_model(model_name)
    except Exception as e:
        print(f"{GRAY}[ModelManager] Error getting running models: {e}{RESET}")


def get_running_models() -> list:
    """Get list of currently running model names."""
    try:
        response = requests.get(f"{OLLAMA_URL}/ps", timeout=2)
        if response.status_code == 200:
            data = response.json()
            return [m.get("name", "") for m in data.get("models", [])]
    except:
        pass
    return []
