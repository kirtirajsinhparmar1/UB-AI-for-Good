"""WAV-only input validation shared by model implementations."""

from dataclasses import dataclass
from pathlib import Path
import wave


class AudioValidationError(ValueError):
    """Raised when an input is not a readable, non-empty WAV file."""


@dataclass(frozen=True)
class AudioMetadata:
    sample_rate: int
    channels: int
    duration_seconds: float


def validate_wav(audio_path: str) -> AudioMetadata:
    path = Path(audio_path)
    if not path.exists():
        raise AudioValidationError("Audio file does not exist.")
    if not path.is_file():
        raise AudioValidationError("Audio input is not a file.")
    if path.suffix.lower() != ".wav":
        raise AudioValidationError("Only .wav files are supported.")
    if path.stat().st_size == 0:
        raise AudioValidationError("Audio file is empty.")

    try:
        with wave.open(str(path), "rb") as audio:
            channels = audio.getnchannels()
            sample_rate = audio.getframerate()
            frame_count = audio.getnframes()
            frame_size = channels * audio.getsampwidth()
            if channels < 1 or sample_rate < 1 or frame_count < 1 or frame_size < 1:
                raise AudioValidationError("WAV audio has no readable frames.")

            frames_read = 0
            while frames_read < frame_count:
                chunk = audio.readframes(min(65536, frame_count - frames_read))
                if not chunk or len(chunk) % frame_size:
                    raise AudioValidationError("WAV audio is truncated or unreadable.")
                frames_read += len(chunk) // frame_size

            return AudioMetadata(
                sample_rate=sample_rate,
                channels=channels,
                duration_seconds=frame_count / sample_rate,
            )
    except AudioValidationError:
        raise
    except (EOFError, OSError, ValueError, wave.Error) as error:
        raise AudioValidationError("Audio file is not a readable WAV file.") from error
