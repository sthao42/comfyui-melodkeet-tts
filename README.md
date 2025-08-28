\# ComfyUI Melodkeet TTS

A custom node for ComfyUI that provides a simple and direct way to use OpenAI-compatible Text-to-Speech (TTS) services.

This node is designed to work with services like 

[https://github.com/travisvn/chatterbox-tts-api]()

[https://github.com/remsky/Kokoro-FastAPI](https://github.com/remsky/Kokoro-FastAPI)

[https://github.com/Lex-au/Orpheus-FastAPI](https://github.com/Lex-au/Orpheus-FastAPI)

It allows you to generate speech directly from a text prompt and includes a feature for on-the-fly voice cloning by providing a sample audio file.

\## Features

\-   \*\*Direct Text-to-Speech:\*\* Send text directly to any OpenAI-compatible TTS API endpoint.

\-   \*\*Voice Cloning:\*\* Connect an audio file (e.g., from a "Load Audio" node) and provide a library name to clone a new voice for the TTS generation.

\-   \*\*Standard Audio Output:\*\* Outputs in the standard ComfyUI `AUDIO` format, allowing it to be connected to other audio nodes like "Save Audio" or "Preview Audio".

\-   \*\*Simple Configuration:\*\* Easily configure the API endpoint, model, voice, and API key directly on the node.

---

\## Installation

1\.  \*\*Navigate to Custom Nodes Folder:\*\*

&nbsp;   Open your ComfyUI installation directory and go into the `/ComfyUI/custom_nodes/` folder.

&nbsp;

```
git clone https://github.com/sthao42/comfyui-melodkeet-tts.git
```




4\.  \*\*Install Dependencies:\*\*

&nbsp;   \*\*Note:\*\* If you use a virtual environment (venv) or python\_embeded for ComfyUI, make sure it is activated before you run the `pip install` command.&nbsp;

&nbsp;   Open your terminal or command prompt, navigate into the node's folder, and install the required packages.

&nbsp;   # Navigate to the correct directory

&nbsp;

```
cd /ComfyUI/custom_nodes/comfyui-melodkeet-tts
```

&nbsp;   # Install the required packages

&nbsp;

```
 pip install -r requirements.txt
```

&nbsp;

5\.  \*\*Restart ComfyUI:\*\*

&nbsp;   You must completely shut down and restart the ComfyUI server for the new node to be recognized.

---

\## Setup and Usage

After restarting, you can add the node to your workflow by right-clicking on the canvas, selecting "Add Node," and finding it under the \*\*audio\*\* category.

\### Connecting to a TTS Server

To use the node, you need to have an OpenAI-compatible TTS server running.

1\.  \*\*Set the TTS URL:\*\*

&nbsp;   In the `tts_url` field, enter the full API endpoint for speech generation. For a locally running Chatterbox server, this will typically be `http://localhost:4123/v1/audio/speech`.

2\.  \*\*Set the Model and Voice:\*\*

&nbsp;   -   `tts_model`: Enter the name of the TTS model you want to use (e.g., `tts-1`).

&nbsp;   -   `tts_voice`: Enter the name of the voice you want to use (e.g., `en_US-female`). These names must exactly match what your TTS server has available.

3\.  \*\*Provide API Key (if required):\*\*

&nbsp;   If your TTS server requires an API key for authentication, enter it into the `api_key` field.

\### How to Use Voice Cloning

1\.  Connect an audio source (like a "Load Audio" node) to the `voice_audio` input on the left side of the node.

2\.  In the `voice_library_name` field, type a \*\*new, unique name\*\* for the voice you are creating.

3\.  When you run the workflow, the node will send the audio file to the TTS server to create a new voice library with that name. It will then immediately use this newly cloned voice to generate the speech.

\*\*Important:\*\* The cloning process will be skipped if the `voice_library_name` field is left empty, even if an audio file is connected. A message will be printed to the console to inform you of this.
