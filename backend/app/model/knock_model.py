"""Local inference for the Revix AST engine-knock classifier."""

from dataclasses import dataclass
import logging
import math
import os
from pathlib import Path
import threading
from typing import Any, Dict, Mapping, Optional, Tuple

from app.model import ModelNotReadyError
from app.model.audio_io import AudioValidationError, validate_wav


KNOCK_MODEL_NAME = "cxlrd/revix-AST-engine-knock"

_LOGGER = logging.getLogger(__name__)
_MODEL_LOCK = threading.Lock()


@dataclass(frozen=True)
class KnockModelResult:
    knock_probability: float
    model_name: str


@dataclass(frozen=True)
class _ModelBundle:
    torch: Any
    torchaudio: Any
    processor: Any
    model: Any
    device: Any
    knock_label_index: int
    num_labels: int
    activation: str


_MODEL_BUNDLE: Optional[_ModelBundle] = None
_MODEL_LOAD_ERROR: Optional[ModelNotReadyError] = None


def _normalize_label(label: str) -> str:
    """Normalize a label before comparing it to known knock class names."""
    return " ".join("".join(char.lower() if char.isalnum() else " " for char in label).split())


def _resolve_knock_label(config: Any) -> Tuple[Dict[int, str], Dict[str, int], int]:
    """Read and cross-check the classifier's configured label maps.

    The model's published config names class 1 ``knocking`` and class 0
    ``clean``. This resolver uses those semantic labels rather than assuming
    that either numeric output position means knock.
    """
    raw_id2label = getattr(config, "id2label", None) or {}
    raw_label2id = getattr(config, "label2id", None) or {}
    id2label: Dict[int, str] = {}
    label2id: Dict[str, int] = {}

    if isinstance(raw_id2label, Mapping):
        for raw_index, raw_label in raw_id2label.items():
            try:
                index = int(raw_index)
            except (TypeError, ValueError) as error:
                raise ModelNotReadyError("The knock model has an invalid id2label mapping.") from error
            if index < 0 or not isinstance(raw_label, str) or not raw_label.strip():
                raise ModelNotReadyError("The knock model has an invalid id2label mapping.")
            id2label[index] = raw_label.strip()

    if isinstance(raw_label2id, Mapping):
        for raw_label, raw_index in raw_label2id.items():
            if not isinstance(raw_label, str) or not raw_label.strip():
                raise ModelNotReadyError("The knock model has an invalid label2id mapping.")
            try:
                index = int(raw_index)
            except (TypeError, ValueError) as error:
                raise ModelNotReadyError("The knock model has an invalid label2id mapping.") from error
            if index < 0:
                raise ModelNotReadyError("The knock model has an invalid label2id mapping.")
            label2id[raw_label.strip()] = index

    if not id2label and label2id:
        id2label = {index: label for label, index in label2id.items()}
    if not id2label:
        raise ModelNotReadyError("The knock model does not define an id2label or label2id mapping.")

    for label, index in label2id.items():
        configured_label = id2label.get(index)
        if configured_label is None or _normalize_label(configured_label) != _normalize_label(label):
            raise ModelNotReadyError("The knock model's id2label and label2id mappings disagree.")

    knock_names = {"knock", "knocking", "engine knock", "engine knocking", "detonation"}
    knock_indices = [
        index for index, label in id2label.items() if _normalize_label(label) in knock_names
    ]
    if len(knock_indices) != 1:
        raise ModelNotReadyError(
            "The knock model's label mapping must identify exactly one knock class; "
            "found labels %r." % id2label
        )

    return id2label, label2id, knock_indices[0]


def _load_model_bundle() -> _ModelBundle:
    """Load the local audio processor and model once, always with CPU support."""
    global _MODEL_BUNDLE, _MODEL_LOAD_ERROR

    with _MODEL_LOCK:
        if _MODEL_BUNDLE is not None:
            return _MODEL_BUNDLE
        if _MODEL_LOAD_ERROR is not None:
            raise ModelNotReadyError(str(_MODEL_LOAD_ERROR)) from _MODEL_LOAD_ERROR

        try:
            import torch
            import torchaudio
            from transformers import ASTFeatureExtractor, AutoModelForAudioClassification
        except (ImportError, OSError, RuntimeError) as error:
            _MODEL_LOAD_ERROR = ModelNotReadyError(
                "Local knock inference dependencies are unavailable. Install "
                "backend/requirements-ml.txt (including matching torch and torchaudio versions)."
            )
            raise _MODEL_LOAD_ERROR from error

        try:
            # The knock repo omits preprocessor_config.json. These are the
            # published AST base-model feature-extractor settings inherited by
            # this fine-tuned checkpoint; keeping them here makes cached/offline
            # inference independent of a second Hub download.
            processor = ASTFeatureExtractor(
                do_normalize=True,
                max_length=1024,
                mean=-4.2677393,
                num_mel_bins=128,
                padding_side="right",
                padding_value=0.0,
                return_attention_mask=False,
                sampling_rate=16000,
                std=4.5689974,
            )
        except (TypeError, ValueError, RuntimeError) as error:
            _MODEL_LOAD_ERROR = ModelNotReadyError(
                "Could not initialize the AST audio feature extractor."
            )
            raise _MODEL_LOAD_ERROR from error

        offline = os.environ.get("HF_HUB_OFFLINE", "").strip().lower() in {
            "1",
            "true",
            "yes",
        }
        try:
            model = AutoModelForAudioClassification.from_pretrained(
                KNOCK_MODEL_NAME,
                local_files_only=offline,
                use_safetensors=True,
            )
        except (OSError, RuntimeError, ValueError) as error:
            _MODEL_LOAD_ERROR = ModelNotReadyError(
                "Could not load local weights for %s. On first use, connect to the "
                "internet once to populate the Hugging Face cache; subsequent runs "
                "can use that cache with HF_HUB_OFFLINE=1. Details: %s"
                % (KNOCK_MODEL_NAME, error)
            )
            raise _MODEL_LOAD_ERROR from error

        try:
            model_config = model.config
            id2label, label2id, knock_index = _resolve_knock_label(model_config)
            num_labels = int(model_config.num_labels)
            if len(id2label) != num_labels or knock_index >= num_labels:
                raise ModelNotReadyError(
                    "The knock model's label mapping does not match its output size."
                )
            if int(model_config.num_mel_bins) != processor.num_mel_bins:
                raise ModelNotReadyError(
                    "The AST processor mel-bin count does not match the model config."
                )
            if int(model_config.max_length) != processor.max_length:
                raise ModelNotReadyError(
                    "The AST processor frame length does not match the model config."
                )

            problem_type = getattr(model_config, "problem_type", None)
            if problem_type == "multi_label_classification":
                activation = "sigmoid"
            elif problem_type in (None, "single_label_classification") and num_labels > 1:
                activation = "softmax"
            elif problem_type is None and num_labels == 1:
                activation = "sigmoid"
            else:
                raise ModelNotReadyError(
                    "The knock model has unsupported output semantics: %r." % problem_type
                )

            device = torch.device("cpu")
            model.to(device)
            model.eval()
        except ModelNotReadyError as error:
            _MODEL_LOAD_ERROR = error
            raise
        except (AttributeError, TypeError, ValueError, RuntimeError) as error:
            _MODEL_LOAD_ERROR = ModelNotReadyError(
                "The downloaded knock model config is incompatible with its AST processor."
            )
            raise _MODEL_LOAD_ERROR from error

        _LOGGER.info(
            "Loaded %s on %s; id2label=%s; label2id=%s; knock label=%r (index %d).",
            KNOCK_MODEL_NAME,
            device,
            id2label,
            label2id,
            id2label[knock_index],
            knock_index,
        )
        _MODEL_BUNDLE = _ModelBundle(
            torch=torch,
            torchaudio=torchaudio,
            processor=processor,
            model=model,
            device=device,
            knock_label_index=knock_index,
            num_labels=num_labels,
            activation=activation,
        )
        return _MODEL_BUNDLE


def _read_wav(audio_path: Path) -> Tuple[Any, int]:
    """Read PCM or float WAV audio as a finite, float32 mono waveform."""
    try:
        import numpy as np
        import soundfile as sf
    except ImportError as error:
        raise ModelNotReadyError(
            "Local WAV loading dependencies are unavailable. Install "
            "backend/requirements-ml.txt."
        ) from error

    path = Path(audio_path)
    try:
        metadata = validate_wav(str(path))
    except AudioValidationError as validation_error:
        # Python's wave module accepts integer PCM but rejects IEEE-float WAV.
        # Permit that WAV subtype through libsndfile after checking its format.
        try:
            info = sf.info(str(path))
        except (RuntimeError, OSError, ValueError):
            raise validation_error
        if info.format not in {"WAV", "WAVEX", "RF64"} or info.subtype not in {
            "FLOAT",
            "DOUBLE",
        }:
            raise validation_error
        if info.frames < 1 or info.samplerate < 1 or info.channels < 1:
            raise AudioValidationError("WAV audio has no readable frames.") from validation_error
        sample_rate = int(info.samplerate)
        expected_frames = int(info.frames)
    else:
        sample_rate = metadata.sample_rate
        expected_frames = None

    try:
        audio, decoded_sample_rate = sf.read(
            str(path), dtype="float32", always_2d=True
        )
    except (RuntimeError, OSError, ValueError) as error:
        raise AudioValidationError("Audio file is not a readable WAV file.") from error

    if (
        audio.ndim != 2
        or audio.shape[0] < 1
        or audio.shape[1] < 1
        or (expected_frames is not None and audio.shape[0] != expected_frames)
        or int(decoded_sample_rate) != sample_rate
        or not np.isfinite(audio).all()
    ):
        raise AudioValidationError("WAV audio contains an invalid waveform.")

    mono = audio.mean(axis=1, dtype=np.float32)
    if mono.size == 0 or not np.isfinite(mono).all():
        raise AudioValidationError("WAV audio contains an invalid waveform.")
    return np.ascontiguousarray(mono, dtype=np.float32), sample_rate


def analyze_knock(audio_path: Path) -> KnockModelResult:
    """Return the pretrained model's probability for the engine-knock class."""
    waveform, sample_rate = _read_wav(audio_path)
    bundle = _load_model_bundle()

    target_sample_rate = int(bundle.processor.sampling_rate)
    try:
        if sample_rate != target_sample_rate:
            waveform_tensor = bundle.torch.from_numpy(waveform)
            waveform = bundle.torchaudio.functional.resample(
                waveform_tensor,
                orig_freq=sample_rate,
                new_freq=target_sample_rate,
            ).numpy()
        if waveform.size == 0 or not bundle.torch.isfinite(
            bundle.torch.from_numpy(waveform)
        ).all():
            raise ValueError("Resampling produced an invalid waveform.")
        minimum_samples = int(round(target_sample_rate * 0.025))
        if waveform.size < minimum_samples:
            raise AudioValidationError(
                "WAV audio must be at least 25 ms long for AST feature extraction."
            )

        inputs = bundle.processor(
            waveform,
            sampling_rate=target_sample_rate,
            return_tensors="pt",
        )
        model_inputs = {key: value.to(bundle.device) for key, value in inputs.items()}
        with bundle.torch.inference_mode():
            logits = bundle.model(**model_inputs).logits
            if logits.ndim != 2 or logits.shape[0] != 1:
                raise ValueError("The model returned an unexpected logits shape.")
            if logits.shape[1] != bundle.num_labels:
                raise ValueError("The model logits do not match its configured labels.")
            if bundle.activation == "softmax":
                probabilities = bundle.torch.softmax(logits, dim=-1)
            else:
                probabilities = bundle.torch.sigmoid(logits)
            knock_probability = float(probabilities[0, bundle.knock_label_index].item())
    except AudioValidationError:
        raise
    except Exception as error:
        raise RuntimeError("Local engine-knock inference failed.") from error

    if not math.isfinite(knock_probability) or not 0.0 <= knock_probability <= 1.0:
        raise RuntimeError("The knock model returned an invalid probability.")

    return KnockModelResult(
        knock_probability=knock_probability,
        model_name=KNOCK_MODEL_NAME,
    )
