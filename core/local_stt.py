"""Low-latency local speech-to-text for JARVIS owner utterances."""
from __future__ import annotations

import os
import threading

import numpy as np

MODEL_NAME = (os.getenv("JARVIS_STT_MODEL") or "small").strip()
LANGUAGE_HINT = (os.getenv("JARVIS_STT_LANGUAGE") or "ta").strip() or None


class LocalWhisperSTT:
    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        self._model = None
        self._lock = threading.Lock()

    def _get_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel
            self._model = WhisperModel(
                self.model_name,
                device="cpu",
                compute_type="int8",
            )
        return self._model

    def transcribe_pcm(self, pcm: bytes, sample_rate: int = 16000) -> str:
        if not pcm:
            return ""
        audio = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
        if audio.size < int(sample_rate * 0.25):
            return ""
        with self._lock:
            segments, _info = self._get_model().transcribe(
                audio,
                language=LANGUAGE_HINT,
                initial_prompt=(
                    "Natural Tamil and English Tanglish conversation with JARVIS and BOSS. "
                    "Technical words may include Forex, Futures, Stocks, Crypto, Dark Flow, "
                    "TradingView, MetaTrader, Binance, Tradovate and WhatsApp."
                ),
                beam_size=1,
                best_of=1,
                vad_filter=True,
                condition_on_previous_text=False,
                word_timestamps=False,
            )
            text = " ".join(str(seg.text or "").strip() for seg in segments).strip()
        return " ".join(text.split())
