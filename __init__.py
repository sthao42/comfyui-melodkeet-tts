import os
import requests
import soundfile as sf
import numpy as np
import torch
from server import PromptServer
import folder_paths
from urllib.parse import urlparse, urlunparse

class MelodkeetTTSNode:
    """
    A ComfyUI node that sends text to a Chatterbox TTS API for speech synthesis,
    with an option for voice cloning.
    """
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "default": "Hello, world! This is a test of the text-to-speech node."}),
                "tts_url": ("STRING", {"default": "http://localhost:4123/v1/audio/speech"}),
                "tts_model": ("STRING", {"default": "hifigan"}),
                "tts_voice": ("STRING", {"default": "en_US-ljspeech-medium"}),
                "api_key": ("STRING", {"default": "your-api-key"}),
            },
            "optional": {
                "voice_audio": ("AUDIO",),
                "voice_library_name": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("audio",)
    FUNCTION = "generate_speech"
    CATEGORY = "audio"

    def clone_voice(self, tts_url, api_key, audio_path, library_name):
        """
        Sends a request to the Chatterbox API to clone a new voice.
        """
        try:
            parsed_url = urlparse(tts_url)
            clone_url = urlunparse((parsed_url.scheme, parsed_url.netloc, '/v1/voices', '', '', ''))
            
            headers = {"Authorization": f"Bearer {api_key}"}
            data = {'library_name': library_name}
            
            print(f"[MelodkeetTTS - DEBUG] Attempting to clone voice. URL: {clone_url}, Library: '{library_name}'")

            with open(audio_path, 'rb') as f:
                files = {'files': (os.path.basename(audio_path), f, 'audio/wav')}
                response = requests.post(clone_url, headers=headers, data=data, files=files)
                
                # --- DIAGNOSTIC CHECK ---
                if response.status_code >= 400:
                    print(f"[MelodkeetTTS - ERROR] Voice cloning failed with status code: {response.status_code}")
                    print(f"[MelodkeetTTS - ERROR] Server response: {response.text}")
                    response.raise_for_status()
            
            print(f"[MelodkeetTTS] Voice cloning successful: {response.json()}")
            return True
        except Exception as e:
            print(f"[MelodkeetTTS] An exception occurred during voice cloning: {e}")
            return False

    def generate_speech(self, text, tts_url, tts_model, tts_voice, api_key, voice_library_name="", voice_audio=None):
        voice_to_use = tts_voice
        empty_audio = {"waveform": torch.zeros(1, 1, 1), "sample_rate": 22050}
        error_return = (empty_audio,)

        if voice_audio is not None and voice_library_name:
            try:
                waveform = voice_audio["waveform"]
                sample_rate = voice_audio["sample_rate"]
                
                # --- DIAGNOSTIC PRINT ---
                print(f"[MelodkeetTTS - DEBUG] Received audio for cloning.")
                print(f"[MelodkeetTTS - DEBUG]   - Sample Rate: {sample_rate}")
                print(f"[MelodkeetTTS - DEBUG]   - Tensor Shape: {waveform.shape}")
                print(f"[MelodkeetTTS - DEBUG]   - Data Type: {waveform.dtype}")

                temp_dir = folder_paths.get_temp_directory()
                temp_file_path = os.path.join(temp_dir, "melodkeet_clone_temp.wav")

                waveform_np = waveform.squeeze(0).cpu().numpy()
                
                if waveform_np.ndim > 2:
                    waveform_np = waveform_np.squeeze(0)

                sf.write(temp_file_path, waveform_np.T, sample_rate)
                print(f"[MelodkeetTTS - DEBUG] Saved temporary clone audio to: {temp_file_path}")

                if self.clone_voice(tts_url, api_key, temp_file_path, voice_library_name):
                    voice_to_use = voice_library_name
                else:
                    print("[MelodkeetTTS] Voice cloning failed. Falling back to selected voice in 'tts_voice' field.")

            except Exception as e:
                print(f"[MelodkeetTTS - ERROR] Could not process input audio for cloning: {e}. Using selected voice.")
        
        elif voice_audio is not None and not voice_library_name:
            print("[MelodkeetTTS - WARNING] An audio file was connected, but the 'voice_library_name' field is empty. Skipping cloning.")
            print("[MelodkeetTTS - WARNING] Please provide a name for the new voice to enable cloning.")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": tts_model,
            "input": text,
            "voice": voice_to_use,
        }

        try:
            print(f"[MelodkeetTTS] Generating speech with voice: {voice_to_use}")
            response = requests.post(tts_url, headers=headers, json=data)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error generating speech with TTS API: {e}")
            return error_return

        try:
            audio_data_np = np.frombuffer(response.content, dtype=np.int16)
            waveform = audio_data_np.astype(np.float32) / 32767.0
            
            sample_rate_tts = 22050
            fade_duration_ms = 5
            fade_samples = int(sample_rate_tts * fade_duration_ms / 1000)

            if len(waveform) > fade_samples:
                fade_in_ramp = np.linspace(0.0, 1.0, fade_samples, dtype=np.float32)
                waveform[:fade_samples] *= fade_in_ramp

            waveform_tensor = torch.from_numpy(waveform).float()
            if waveform_tensor.ndim == 1:
                waveform_tensor = waveform_tensor.unsqueeze(0)
            waveform_tensor = waveform_tensor.unsqueeze(0) 

            audio_output = {"waveform": waveform_tensor, "sample_rate": sample_rate_tts}
        except Exception as e:
            print(f"Error preparing audio tensor for output: {e}")
            return error_return

        return (audio_output,)

NODE_CLASS_MAPPINGS = { "MelodkeetTTS": MelodkeetTTSNode }
NODE_DISPLAY_NAME_MAPPINGS = { "MelodkeetTTS": "ComfyUI Melodkeet TTS" }

