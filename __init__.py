import os
import requests
import soundfile as sf
import numpy as np
import torch
import io
from urllib.parse import urlparse, urlunparse

import folder_paths
from server import PromptServer

class MelodkeetTTSNode:
    """
    A ComfyUI node that sends text to a Chatterbox TTS API for speech synthesis,
    with an option for voice cloning from an audio input and fine-tuning generation parameters.
    """
    # --- Constants for Configuration ---
    DEFAULT_TTS_URL = "http://localhost:4123/v1/audio/speech"
    DEFAULT_MODEL = "tts-1"
    DEFAULT_VOICE = "en_US-female"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "default": "Hello, world! This is a test of the text-to-speech node."}),
                "tts_url": ("STRING", {"default": s.DEFAULT_TTS_URL}),
                "tts_model": ("STRING", {"default": s.DEFAULT_MODEL}),
                "tts_voice": ("STRING", {"default": s.DEFAULT_VOICE}),
                "api_key": ("STRING", {"multiline": False, "default": ""}),
            },
            "optional": {
                "voice_audio": ("AUDIO",),
                "voice_library_name": ("STRING", {"multiline": False, "default": ""}),
                "exaggeration_intensity": ("FLOAT", {"default": 0.5, "min": 0.25, "max": 2.0, "step": 0.05}),
                "cfg_speech_pace": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.05}),
                "temperature_creativity": ("FLOAT", {"default": 0.8, "min": 0.05, "max": 5.0, "step": 0.05}),
            }
        }

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("audio",)
    FUNCTION = "generate_speech"
    CATEGORY = "audio"

    def _clone_voice(self, tts_url, api_key, audio_data, library_name):
        """
        Sends a request to the Chatterbox API to clone a new voice from in-memory audio data.
        """
        try:
            parsed_url = urlparse(tts_url)
            clone_url = urlunparse((parsed_url.scheme, parsed_url.netloc, '/v1/voices', '', '', ''))
            
            headers = {"Authorization": f"Bearer {api_key}"}
            data = {'library_name': library_name}
            files = {'files': ('clone_voice.wav', audio_data, 'audio/wav')}
            
            print(f"[MelodkeetTTS] Cloning voice with name '{library_name}' to {clone_url}")
            response = requests.post(clone_url, headers=headers, data=data, files=files)
            response.raise_for_status()
            
            print(f"[MelodkeetTTS] Voice cloning successful: {response.json()}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"[MelodkeetTTS] Error during voice cloning API call: {e}")
            return False
        except Exception as e:
            print(f"[MelodkeetTTS] An unexpected error occurred during voice cloning: {e}")
            return False

    def generate_speech(self, text, tts_url, tts_model, tts_voice, api_key, exaggeration_intensity, cfg_speech_pace, temperature_creativity, voice_library_name="", voice_audio=None):
        voice_to_use = tts_voice
        SAMPLE_RATE = 22050
        empty_audio = {"waveform": torch.zeros(1, 1, 1), "sample_rate": SAMPLE_RATE}
        error_return = (empty_audio,)

        if not api_key:
            print("[MelodkeetTTS] Error: API Key is missing.")
            return error_return

        # --- Voice Cloning Logic ---
        if voice_audio is not None and voice_library_name:
            try:
                waveform = voice_audio["waveform"]
                sample_rate = voice_audio["sample_rate"]
                waveform_np = waveform.squeeze(0).cpu().numpy()
                if waveform_np.ndim > 1:
                    waveform_np = waveform_np.squeeze(0)

                with io.BytesIO() as buffer:
                    sf.write(buffer, waveform_np.T, sample_rate, format='WAV')
                    buffer.seek(0)
                    
                    print(f"[MelodkeetTTS] Processing in-memory audio for cloning.")
                    if self._clone_voice(tts_url, api_key, buffer, voice_library_name):
                        voice_to_use = voice_library_name
                    else:
                        print("[MelodkeetTTS] Voice cloning failed. Falling back to the selected voice.")
            except Exception as e:
                print(f"[MelodkeetTTS] Error processing input audio for cloning: {e}. Using selected voice.")
        
        elif voice_audio is not None and not voice_library_name:
            print("[MelodkeetTTS] An audio file was connected, but 'voice_library_name' is empty. Skipping cloning.")

        # --- TTS Speech Synthesis ---
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        generation_config = {
            "exaggeration": exaggeration_intensity,
            "cfg_weight": cfg_speech_pace,
            "temperature": temperature_creativity,
        }

        data = {
            "model": tts_model,
            "input": text,
            "voice": voice_to_use,
            "generation_config": generation_config,
        }

        try:
            print(f"[MelodkeetTTS] Generating speech with voice: '{voice_to_use}'")
            print(f"[MelodkeetTTS] Generation parameters: {generation_config}")
            response = requests.post(tts_url, headers=headers, json=data)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"[MelodkeetTTS] Error generating speech with TTS API: {e}")
            return error_return

        # --- Prepare AUDIO Output Tensor ---
        try:
            audio_data_np = np.frombuffer(response.content, dtype=np.int16)
            waveform = audio_data_np.astype(np.float32) / 32767.0
            
            fade_duration_ms = 5
            fade_samples = int(SAMPLE_RATE * fade_duration_ms / 1000)

            if len(waveform) > fade_samples:
                fade_in_ramp = np.linspace(0.0, 1.0, fade_samples, dtype=np.float32)
                waveform[:fade_samples] *= fade_in_ramp

            waveform_tensor = torch.from_numpy(waveform).float()
            waveform_tensor = waveform_tensor.unsqueeze(0).unsqueeze(0)

            audio_output = {"waveform": waveform_tensor, "sample_rate": SAMPLE_RATE}
        except Exception as e:
            print(f"[MelodkeetTTS] Error preparing audio tensor for output: {e}")
            return error_return

        return (audio_output,)

# --- ComfyUI Registration ---
NODE_CLASS_MAPPINGS = {
    "MelodkeetTTS": MelodkeetTTSNode
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "MelodkeetTTS": "ComfyUI Melodkeet TTS"
}