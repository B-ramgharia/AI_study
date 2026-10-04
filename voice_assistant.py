"""
Voice Assistant Module for AI Study Buddy
Provides Speech-to-Text (Voice Input) and Text-to-Speech (Voice Output) capabilities.
"""

import io
import re
import base64
import streamlit as st
import streamlit.components.v1 as components
from gtts import gTTS


def clean_text_for_speech(text: str) -> str:
    """Removes markdown syntax, emojis, and HTML tags for natural voice synthesis."""
    if not text:
        return ""
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', text)
    # Remove markdown bold/italic/headers/links
    clean = re.sub(r'[*#_`~\[\]]', '', clean)
    # Remove URLs
    clean = re.sub(r'http\S+', '', clean)
    # Truncate if extremely long to avoid audio buffer delay
    if len(clean) > 800:
        clean = clean[:800] + "... and more."
    return clean.strip()


def speak(text: str, lang: str = "en", autoplay: bool = True, key: str = None):
    """
    Converts text into spoken audio using gTTS and plays it directly in Streamlit.
    """
    clean_str = clean_text_for_speech(text)
    if not clean_str:
        return

    try:
        tts = gTTS(text=clean_str, lang=lang, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        audio_bytes = fp.read()
        
        st.audio(audio_bytes, format="audio/mp3", autoplay=autoplay)
    except Exception as e:
        st.caption(f"🎙️ Voice assistant output unavailable: {e}")


def transcribe_audio_bytes(audio_bytes, client=None, mime_type="audio/wav") -> str:
    """
    Transcribes audio bytes to text using Google Gemini API.
    """
    if not audio_bytes:
        return ""

    if client:
        try:
            from google.genai import types
            
            # Determine audio format
            if audio_bytes.startswith(b'OggS'):
                actual_mime = "audio/ogg"
            elif audio_bytes.startswith(b'RIFF'):
                actual_mime = "audio/wav"
            elif audio_bytes[0:3] == b'ID3' or audio_bytes[0:2] == b'\xff\xfb':
                actual_mime = "audio/mp3"
            else:
                actual_mime = mime_type or "audio/wav"

            prompt = "Transcribe this spoken audio accurately. Output ONLY the raw transcribed text without any quotes, formatting, or commentary."
            
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=[
                    types.Part.from_bytes(
                        data=audio_bytes,
                        mime_type=actual_mime
                    ),
                    prompt
                ]
            )
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            st.error(f"🎙️ Speech recognition error: {e}")

    return ""


def render_voice_input(key_prefix: str, client=None, label: str = "🎙️ Voice Input") -> str:
    """
    Renders a unified Streamlit Voice Input component that allows recording voice
    and transcribes it into text.
    """
    st.markdown(f"**{label}**")
    audio_data = st.audio_input(label="Record your question", key=f"v_input_{key_prefix}")
    
    if audio_data is not None:
        raw_bytes = audio_data.getvalue()
        if raw_bytes:
            with st.spinner("🎙️ Transcribing voice..."):
                transcription = transcribe_audio_bytes(raw_bytes, client=client)
                if transcription:
                    st.success(f"🗣️ **Heard:** \"{transcription}\"")
                    return transcription
                else:
                    st.warning("⚠️ Could not transcribe voice. Please speak clearly or try again.")
    return ""


def render_browser_voice_dictation_btn(button_label: str = "🎙️ Dictate Voice", input_key: str = ""):
    """
    Renders a live browser Web Speech API mic button for instant dictation into chat inputs.
    """
    html_code = f"""
    <div style="margin-top: 5px; margin-bottom: 5px;">
        <button id="mic-btn-{input_key}" style="
            background: linear-gradient(135deg, #0ea5e9, #3b82f6);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            box-shadow: 0 4px 12px rgba(14, 165, 233, 0.3);
            transition: all 0.2s ease;
        ">
            <span id="mic-icon-{input_key}">🎙️</span> {button_label}
        </button>
        <span id="mic-status-{input_key}" style="font-size: 13px; color: #64748b; margin-left: 8px;"></span>
    </div>

    <script>
    (function() {{
        const btn = document.getElementById('mic-btn-{input_key}');
        const icon = document.getElementById('mic-icon-{input_key}');
        const status = document.getElementById('mic-status-{input_key}');
        
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {{
            if (status) status.innerText = "Web Speech API not supported in this browser.";
            return;
        }}

        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        let isListening = false;

        btn.onclick = function() {{
            if (!isListening) {{
                try {{
                    recognition.start();
                    isListening = true;
                    btn.style.background = "linear-gradient(135deg, #ef4444, #dc2626)";
                    icon.innerText = "🔴";
                    status.innerText = "Listening...";
                }} catch(e) {{
                    status.innerText = "Mic error: " + e.message;
                }}
            }} else {{
                recognition.stop();
                isListening = false;
                btn.style.background = "linear-gradient(135deg, #0ea5e9, #3b82f6)";
                icon.innerText = "🎙️";
                status.innerText = "Stopped.";
            }}
        }};

        recognition.onresult = function(event) {{
            const transcript = event.results[0][0].transcript;
            status.innerText = "Captured: " + transcript;
            btn.style.background = "linear-gradient(135deg, #0ea5e9, #3b82f6)";
            icon.innerText = "🎙️";
            isListening = false;

            // Target parent inputs if available
            const parentDoc = window.parent.document;
            if (parentDoc) {{
                const inputs = parentDoc.querySelectorAll('input[type="text"], textarea');
                if (inputs.length > 0) {{
                    const lastInput = inputs[inputs.length - 1];
                    lastInput.value = (lastInput.value ? lastInput.value + " " : "") + transcript;
                    lastInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                }}
            }}
        }};

        recognition.onerror = function(event) {{
            status.innerText = "Mic error: " + event.error;
            btn.style.background = "linear-gradient(135deg, #0ea5e9, #3b82f6)";
            icon.innerText = "🎙️";
            isListening = false;
        }};
    }})();
    </script>
    """
    components.html(html_code, height=45)
