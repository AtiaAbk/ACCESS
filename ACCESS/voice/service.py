"""Optional offline speech recognition and text-to-speech services."""

from __future__ import annotations

import importlib.util
import queue
import re
import threading


class VoiceError(RuntimeError):
    """Base class for recoverable voice errors."""


class VoiceUnavailable(VoiceError):
    """The required voice backend or audio device is unavailable."""


class VoiceTimeout(VoiceError):
    """No speech started before the listening timeout."""


class VoiceNotUnderstood(VoiceError):
    """Audio was captured, but it could not be transcribed."""


class VoiceService:
    """Provide offline microphone transcription and queued speech output."""

    def __init__(self, language: str = "en-US", rate: int = 185):
        self.language = language
        self.rate = rate
        self._speech_queue: queue.Queue[str | None] = queue.Queue()
        self._speech_thread: threading.Thread | None = None
        self._thread_lock = threading.Lock()

    @property
    def can_listen(self) -> bool:
        return all(
            importlib.util.find_spec(module) is not None
            for module in ("speech_recognition", "pocketsphinx", "pyaudio")
        )

    @property
    def can_speak(self) -> bool:
        return importlib.util.find_spec("pyttsx3") is not None

    def listen(self, timeout: float = 5, phrase_time_limit: float = 10) -> str:
        """Capture one phrase and transcribe it locally with PocketSphinx."""

        if not self.can_listen:
            raise VoiceUnavailable(
                "Offline microphone support is not installed. Reinstall the project requirements."
            )

        import speech_recognition as sr

        recognizer = sr.Recognizer()
        recognizer.dynamic_energy_threshold = True
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )
        except sr.WaitTimeoutError as error:
            raise VoiceTimeout("I didn't hear anything. Please try again.") from error
        except (AttributeError, OSError) as error:
            raise VoiceUnavailable(
                "No working microphone was found. Check the device and microphone permission."
            ) from error

        try:
            transcript = recognizer.recognize_sphinx(audio, language=self.language)
        except sr.UnknownValueError as error:
            raise VoiceNotUnderstood(
                "I heard audio but couldn't understand it. Please speak clearly and try again."
            ) from error
        except (LookupError, RuntimeError) as error:
            raise VoiceUnavailable(
                "The offline speech model could not start. Reinstall the voice dependencies."
            ) from error

        transcript = str(transcript).strip()
        if not transcript:
            raise VoiceNotUnderstood("I couldn't understand that. Please try again.")
        return transcript

    def speak(self, text: str) -> bool:
        """Queue text for non-blocking offline speech output."""

        if not self.can_speak:
            return False
        spoken_text = self._prepare_for_speech(text)
        if not spoken_text:
            return False
        self._ensure_speech_worker()
        self._speech_queue.put(spoken_text)
        return True

    def stop(self) -> None:
        """Discard queued speech and ask the speech worker to stop."""

        while True:
            try:
                self._speech_queue.get_nowait()
            except queue.Empty:
                break
        if self._speech_thread and self._speech_thread.is_alive():
            self._speech_queue.put(None)

    def _ensure_speech_worker(self) -> None:
        with self._thread_lock:
            if self._speech_thread and self._speech_thread.is_alive():
                return
            self._speech_thread = threading.Thread(
                target=self._speech_worker,
                name="access-speech",
                daemon=True,
            )
            self._speech_thread.start()

    def _speech_worker(self) -> None:
        try:
            import pyttsx3

            engine = pyttsx3.init()
            engine.setProperty("rate", self.rate)
        except Exception:
            return

        while True:
            text = self._speech_queue.get()
            if text is None:
                try:
                    engine.stop()
                except Exception:
                    pass
                return
            try:
                engine.say(text)
                engine.runAndWait()
            except Exception:
                # Speech output is optional and must never take down the UI.
                continue

    @staticmethod
    def _prepare_for_speech(text: str) -> str:
        """Remove visual formatting and bound unusually long responses."""

        value = str(text or "")
        value = re.sub(r"```.*?```", " Code block omitted. ", value, flags=re.DOTALL)
        value = re.sub(r"[`*_#>]", "", value)
        value = re.sub(r"https?://\S+", "link", value)
        value = re.sub(r"\s+", " ", value).strip()
        if len(value) > 600:
            value = value[:597].rsplit(" ", 1)[0] + "..."
        return value
