"""Compare the production AST model with cxlrd's ResNet-18 locally.

This script is evaluation-only. It uses the production ``analyze_knock``
function unchanged and follows the ResNet model card's inference example:
MelSpectrogram -> AmplitudeToDB -> bilinear 224x224 resize -> repeat to RGB.
The checkpoint README does not specify a separate inference normalization, so
the evaluator does not add one.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.model.knock_model import (  # noqa: E402
    KNOCK_MODEL_NAME,
    _resolve_knock_label,
    analyze_knock,
)


RESNET_MODEL_ID = "cxlrd/engine-knock-resnet18"
RESNET_REVISION = "8a3c6a7cf497ffdff40a14aeace3399f953950f6"
DEFAULT_CLEAN_DIR = Path(
    "/Users/kp/Documents/Hack/UB AI For Good/UB-AI-for-Good/"
    "backend/demo/sample_audio/car_clean"
)
DEFAULT_KNOCKING_DIR = Path(
    "/Users/kp/Documents/Hack/UB AI For Good/UB-AI-for-Good/"
    "backend/demo/sample_audio/car_knocking"
)

TARGET_SAMPLE_RATE = 16000
N_FFT = 1024
HOP_LENGTH = 512
N_MELS = 128
IMAGE_SIZE = 224


def _is_offline() -> bool:
    return os.environ.get("HF_HUB_OFFLINE", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }


def _normalize_label(label: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", label.lower()).split())


def _class_indices(labels: Sequence[str]) -> Tuple[int, int]:
    """Resolve clean and knocking indices from explicit checkpoint labels."""
    clean_names = {"clean", "normal", "engine clean", "non knocking"}
    knock_names = {
        "knock",
        "knocking",
        "engine knock",
        "engine knocking",
        "detonation",
    }
    clean_indices = [
        index for index, label in enumerate(labels) if _normalize_label(label) in clean_names
    ]
    knock_indices = [
        index for index, label in enumerate(labels) if _normalize_label(label) in knock_names
    ]
    if len(clean_indices) != 1 or len(knock_indices) != 1:
        raise ValueError(
            "Class mapping is ambiguous: labels must identify exactly one clean "
            "and one knocking class; got %r." % list(labels)
        )
    if clean_indices[0] == knock_indices[0]:
        raise ValueError("Class mapping assigns clean and knocking to the same output.")
    return clean_indices[0], knock_indices[0]


def _load_metadata(offline: bool) -> Dict[str, Any]:
    """Read model label maps and the published ResNet preprocessing config."""
    from huggingface_hub import hf_hub_download
    from transformers import AutoConfig

    ast_config = AutoConfig.from_pretrained(
        KNOCK_MODEL_NAME,
        local_files_only=offline,
    )
    ast_id2label, ast_label2id, ast_knock_index = _resolve_knock_label(ast_config)
    ast_labels = [ast_id2label[index] for index in sorted(ast_id2label)]
    ast_clean_index, resolved_ast_knock_index = _class_indices(ast_labels)
    ast_indices = sorted(ast_id2label)
    ast_clean_index = ast_indices[ast_clean_index]
    if ast_indices[resolved_ast_knock_index] != ast_knock_index:
        raise ValueError("AST production label resolver disagrees with its config labels.")
    if len(ast_id2label) != int(ast_config.num_labels) or len(ast_id2label) != 2:
        raise ValueError("AST config does not expose exactly two mapped output labels.")

    resnet_config_path = hf_hub_download(
        repo_id=RESNET_MODEL_ID,
        filename="config.json",
        revision=RESNET_REVISION,
        local_files_only=offline,
    )
    resnet_config = json.loads(Path(resnet_config_path).read_text(encoding="utf-8"))
    labels = resnet_config.get("class_names")
    if not isinstance(labels, list) or not all(isinstance(label, str) for label in labels):
        raise ValueError("ResNet config does not define a string class_names list.")
    resnet_clean_index, resnet_knock_index = _class_indices(labels)
    if len(labels) != 2 or int(resnet_config.get("num_classes", -1)) != 2:
        raise ValueError("ResNet config does not describe a two-class output.")

    expected_config = {
        "sample_rate": TARGET_SAMPLE_RATE,
        "n_fft": N_FFT,
        "hop_length": HOP_LENGTH,
        "n_mels": N_MELS,
        "input_size": [3, IMAGE_SIZE, IMAGE_SIZE],
    }
    for key, expected in expected_config.items():
        if resnet_config.get(key) != expected:
            raise ValueError(
                "Published ResNet config has unexpected %s=%r (expected %r)."
                % (key, resnet_config.get(key), expected)
            )

    return {
        "ast": {
            "model_id": KNOCK_MODEL_NAME,
            "revision": getattr(ast_config, "_commit_hash", None),
            "id2label": {str(index): label for index, label in ast_id2label.items()},
            "label2id": ast_label2id,
            "clean_index": ast_clean_index,
            "knocking_index": ast_knock_index,
            "activation": getattr(ast_config, "problem_type", None)
            or "single_label_classification (softmax in production)",
        },
        "resnet": {
            "model_id": RESNET_MODEL_ID,
            "revision": RESNET_REVISION,
            "class_names": labels,
            "clean_index": resnet_clean_index,
            "knocking_index": resnet_knock_index,
            "config": resnet_config,
        },
    }


def _prepare_assets(offline: bool) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Make sure model files are cached before measuring first inference calls."""
    from huggingface_hub import hf_hub_download, snapshot_download

    assets: Dict[str, str] = {}
    errors: Dict[str, str] = {}
    try:
        ast_cache = snapshot_download(
            repo_id=KNOCK_MODEL_NAME,
            local_files_only=offline,
        )
        assets["ast_cache"] = str(Path(ast_cache).resolve())
    except Exception as error:
        errors["AST"] = "%s: %s" % (type(error).__name__, error)

    try:
        resnet_config = hf_hub_download(
            repo_id=RESNET_MODEL_ID,
            filename="config.json",
            revision=RESNET_REVISION,
            local_files_only=offline,
        )
        resnet_weights = hf_hub_download(
            repo_id=RESNET_MODEL_ID,
            filename="model.pth",
            revision=RESNET_REVISION,
            local_files_only=offline,
        )
        assets["resnet_config"] = str(Path(resnet_config).resolve())
        assets["resnet_weights"] = str(Path(resnet_weights).resolve())
    except Exception as error:
        errors["ResNet18"] = "%s: %s" % (type(error).__name__, error)
    return assets, errors


def _wav_files(directory: Path, limit: int) -> List[Path]:
    if not directory.is_dir():
        raise ValueError("Dataset directory does not exist: %s" % directory)
    paths = sorted(
        (path for path in directory.iterdir() if path.is_file() and path.suffix.lower() == ".wav"),
        key=lambda path: path.name,
    )
    if len(paths) < limit:
        raise ValueError(
            "Expected at least %d WAV files in %s, found %d."
            % (limit, directory, len(paths))
        )
    return paths[:limit]


class _ResNetPredictor:
    def __init__(self, config: Dict[str, Any], weights_path: str) -> None:
        self.config = config
        self.weights_path = weights_path
        self.model: Any = None
        self.torch: Any = None
        self.torchaudio: Any = None
        self.mel_transform: Any = None
        self.db_transform: Any = None

    def _load(self) -> None:
        import torch
        import torchaudio
        from torchvision.models import resnet18

        model = resnet18(weights=None)
        model.fc = torch.nn.Linear(model.fc.in_features, int(self.config["num_classes"]))
        state_dict = torch.load(self.weights_path, map_location="cpu", weights_only=True)
        if not isinstance(state_dict, dict):
            raise ValueError("ResNet checkpoint is not a state dictionary.")
        model.load_state_dict(state_dict, strict=True)
        model.eval()

        self.torch = torch
        self.torchaudio = torchaudio
        self.model = model
        self.mel_transform = torchaudio.transforms.MelSpectrogram(
            sample_rate=TARGET_SAMPLE_RATE,
            n_fft=N_FFT,
            hop_length=HOP_LENGTH,
            n_mels=N_MELS,
        )
        self.db_transform = torchaudio.transforms.AmplitudeToDB()

    def predict(self, path: Path) -> float:
        if self.model is None:
            self._load()

        waveform, sample_rate = self.torchaudio.load(str(path))
        if waveform.ndim != 2 or waveform.shape[0] < 1 or waveform.shape[1] < 1:
            raise ValueError("WAV decode returned an empty or invalid waveform.")
        waveform = waveform.mean(dim=0, keepdim=True)
        if sample_rate != TARGET_SAMPLE_RATE:
            waveform = self.torchaudio.functional.resample(
                waveform,
                orig_freq=sample_rate,
                new_freq=TARGET_SAMPLE_RATE,
            )

        # Match the published model-card inference snippet. The transform
        # defaults (including power=2 and AmplitudeToDB top_db=80) are retained.
        mel_spec = self.mel_transform(waveform)
        mel_spec_db = self.db_transform(mel_spec)
        image = self.torch.nn.functional.interpolate(
            mel_spec_db.unsqueeze(0),
            size=(IMAGE_SIZE, IMAGE_SIZE),
            mode="bilinear",
        ).repeat(1, 3, 1, 1)

        with self.torch.inference_mode():
            logits = self.model(image)
            if logits.ndim != 2 or logits.shape != (1, int(self.config["num_classes"])):
                raise ValueError("ResNet returned an unexpected logits shape %r." % (logits.shape,))
            probability = self.torch.softmax(logits, dim=-1)[
                0, self.config["knocking_index"]
            ].item()
        probability = float(probability)
        if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
            raise ValueError("ResNet returned an invalid knock probability.")
        return probability


def _timed_prediction(call: Any) -> Tuple[Optional[float], float, Optional[str]]:
    start = time.perf_counter()
    try:
        probability = float(call())
        elapsed = time.perf_counter() - start
        if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
            raise ValueError("model returned an invalid probability")
        return probability, elapsed, None
    except Exception as error:  # Record per-file failures and keep the paired row.
        return None, time.perf_counter() - start, "%s: %s" % (type(error).__name__, error)


def _auc(labels: Sequence[int], scores: Sequence[float]) -> Optional[float]:
    positives = [score for label, score in zip(labels, scores) if label == 1]
    negatives = [score for label, score in zip(labels, scores) if label == 0]
    if not positives or not negatives:
        return None
    wins = sum(
        1.0 if positive > negative else 0.5 if positive == negative else 0.0
        for positive in positives
        for negative in negatives
    )
    return wins / (len(positives) * len(negatives))


def _model_metrics(rows: Sequence[Dict[str, Any]], probability_key: str) -> Dict[str, Any]:
    evaluated = [row for row in rows if row[probability_key] is not None]
    labels = [1 if row["ground_truth"] == "knocking" else 0 for row in evaluated]
    scores = [float(row[probability_key]) for row in evaluated]
    clean = [score for label, score in zip(labels, scores) if label == 0]
    knocking = [score for label, score in zip(labels, scores) if label == 1]
    predicted = [1 if score >= 0.5 else 0 for score in scores]
    tp = sum(actual == 1 and guess == 1 for actual, guess in zip(labels, predicted))
    fp = sum(actual == 0 and guess == 1 for actual, guess in zip(labels, predicted))
    tn = sum(actual == 0 and guess == 0 for actual, guess in zip(labels, predicted))
    fn = sum(actual == 1 and guess == 0 for actual, guess in zip(labels, predicted))

    def describe(values: Sequence[float]) -> Dict[str, Optional[float]]:
        if not values:
            return {"mean": None, "median": None, "min": None, "max": None}
        return {
            "mean": statistics.fmean(values),
            "median": statistics.median(values),
            "min": min(values),
            "max": max(values),
        }

    return {
        "number_evaluated": len(evaluated),
        "clean": describe(clean),
        "knocking": describe(knocking),
        "mean_separation": (
            statistics.fmean(knocking) - statistics.fmean(clean)
            if clean and knocking
            else None
        ),
        "roc_auc": _auc(labels, scores),
        "accuracy_at_0_50": (tp + tn) / len(labels) if labels else None,
        "precision_at_0_50": tp / (tp + fp) if tp + fp else 0.0,
        "recall_at_0_50": tp / (tp + fn) if tp + fn else 0.0,
        "confusion_matrix": {"TP": tp, "FP": fp, "TN": tn, "FN": fn},
    }


def _mean_subsequent(timings: Sequence[float]) -> Optional[float]:
    return statistics.fmean(timings[1:]) if len(timings) > 1 else None


def _better(a: Optional[float], b: Optional[float], higher_is_better: bool = True) -> str:
    if a is None or b is None:
        return "inconclusive (insufficient successful predictions)"
    if math.isclose(a, b, rel_tol=0.0, abs_tol=1e-12):
        return "tie"
    if (a > b) == higher_is_better:
        return "MODEL A — AST"
    return "MODEL B — RESNET18"


def _print_model(name: str, metrics: Dict[str, Any], timing: Dict[str, Any]) -> None:
    print("\n%s" % name)
    print("Number evaluated: %d" % metrics["number_evaluated"])
    for label, key in (("Clean", "clean"), ("Knocking", "knocking")):
        values = metrics[key]
        print(
            "%s mean / median / min / max: %s"
            % (
                label,
                " / ".join(
                    "n/a" if values[field] is None else "%.4f" % values[field]
                    for field in ("mean", "median", "min", "max")
                ),
            )
        )
    print("Difference (knocking - clean): %s" % _fmt(metrics["mean_separation"]))
    print("ROC-AUC: %s" % _fmt(metrics["roc_auc"]))
    print("Accuracy @ 0.50: %s" % _fmt(metrics["accuracy_at_0_50"]))
    print("Precision @ 0.50: %s" % _fmt(metrics["precision_at_0_50"]))
    print("Recall @ 0.50: %s" % _fmt(metrics["recall_at_0_50"]))
    cm = metrics["confusion_matrix"]
    print("TP/FP/TN/FN: %(TP)d/%(FP)d/%(TN)d/%(FN)d" % cm)
    print("First-call time: %s" % _fmt_seconds(timing["first_call_seconds"]))
    print(
        "Average subsequent per-file time: %s"
        % _fmt_seconds(timing["average_subsequent_seconds"])
    )


def _fmt(value: Optional[float]) -> str:
    return "n/a" if value is None else "%.4f" % value


def _fmt_seconds(value: Optional[float]) -> str:
    return "n/a" if value is None else "%.4f s" % value


def run(args: argparse.Namespace) -> Dict[str, Any]:
    offline = _is_offline()
    metadata = _load_metadata(offline)
    assets, asset_errors = _prepare_assets(offline)

    clean_paths = _wav_files(Path(args.clean_dir), args.samples_per_class)
    knocking_paths = _wav_files(Path(args.knocking_dir), args.samples_per_class)
    samples = [(path, "clean") for path in clean_paths] + [
        (path, "knocking") for path in knocking_paths
    ]

    resnet_config = dict(metadata["resnet"]["config"])
    resnet_config["knocking_index"] = metadata["resnet"]["knocking_index"]
    resnet = _ResNetPredictor(resnet_config, assets.get("resnet_weights", ""))
    rows: List[Dict[str, Any]] = []
    ast_times: List[float] = []
    resnet_times: List[float] = []

    for path, label in samples:
        row: Dict[str, Any] = {
            "filename": path.name,
            "ground_truth": label,
            "ast_knock_probability": None,
            "resnet_knock_probability": None,
            "ast_failure": None,
            "resnet_failure": None,
        }
        if "AST" in asset_errors:
            ast_result = (None, 0.0, asset_errors["AST"])
        else:
            ast_result = _timed_prediction(
                lambda sample_path=path: analyze_knock(sample_path).knock_probability
            )
        if "ResNet18" in asset_errors:
            resnet_result = (None, 0.0, asset_errors["ResNet18"])
        else:
            resnet_result = _timed_prediction(lambda sample_path=path: resnet.predict(sample_path))

        row["ast_knock_probability"], ast_elapsed, row["ast_failure"] = ast_result
        row["resnet_knock_probability"], resnet_elapsed, row["resnet_failure"] = resnet_result
        ast_times.append(ast_elapsed)
        resnet_times.append(resnet_elapsed)
        rows.append(row)

    ast_metrics = _model_metrics(rows, "ast_knock_probability")
    resnet_metrics = _model_metrics(rows, "resnet_knock_probability")
    ast_timing = {
        "first_call_seconds": ast_times[0] if ast_times else None,
        "average_subsequent_seconds": _mean_subsequent(ast_times),
    }
    resnet_timing = {
        "first_call_seconds": resnet_times[0] if resnet_times else None,
        "average_subsequent_seconds": _mean_subsequent(resnet_times),
    }

    print("MODEL BAKEOFF — LOCAL INFERENCE")
    print("Offline mode: %s" % ("HF_HUB_OFFLINE=1" if offline else "disabled"))
    print("Models: %s vs %s @ %s" % (KNOCK_MODEL_NAME, RESNET_MODEL_ID, RESNET_REVISION))
    print("Sample selection: first %d sorted WAV files per label." % args.samples_per_class)
    print("AST mapping: %s" % json.dumps(metadata["ast"]["id2label"], sort_keys=True))
    print("  clean index=%d; knocking index=%d" % (
        metadata["ast"]["clean_index"], metadata["ast"]["knocking_index"]
    ))
    print("ResNet mapping: %s" % json.dumps(metadata["resnet"]["class_names"]))
    print("  clean index=%d; knocking index=%d" % (
        metadata["resnet"]["clean_index"], metadata["resnet"]["knocking_index"]
    ))
    print(
        "ResNet preprocessing: mono; resample to 16000 Hz if needed; "
        "MelSpectrogram(sample_rate=16000, n_fft=1024, hop_length=512, n_mels=128; "
        "torchaudio defaults); AmplitudeToDB(defaults); bilinear resize to 224x224; "
        "repeat to 3 channels; no additional normalization."
    )
    if len(assets) == 3 and not asset_errors:
        print("Cache: AST and ResNet artifacts resolved locally before timing.")
    if asset_errors:
        print("Asset preparation failures: %s" % json.dumps(asset_errors, sort_keys=True))

    print("\nPER-FILE RESULTS (same selected file is kept for both models)")
    print("filename | label | AST knock probability | ResNet knock probability | failures")
    for row in rows:
        ast_value = _fmt(row["ast_knock_probability"])
        resnet_value = _fmt(row["resnet_knock_probability"])
        failures = "; ".join(
            part
            for part in (
                "AST: " + row["ast_failure"] if row["ast_failure"] else "",
                "ResNet: " + row["resnet_failure"] if row["resnet_failure"] else "",
            )
            if part
        )
        print(
            "%s | %s | %s | %s | %s"
            % (row["filename"], row["ground_truth"], ast_value, resnet_value, failures or "—")
        )

    _print_model("MODEL A — AST", ast_metrics, ast_timing)
    _print_model("MODEL B — RESNET18", resnet_metrics, resnet_timing)
    print("\nHEAD-TO-HEAD")
    print("Better ROC-AUC: %s" % _better(ast_metrics["roc_auc"], resnet_metrics["roc_auc"]))
    print(
        "Better separation: %s"
        % _better(ast_metrics["mean_separation"], resnet_metrics["mean_separation"])
    )
    print(
        "Better accuracy @ 0.50: %s"
        % _better(ast_metrics["accuracy_at_0_50"], resnet_metrics["accuracy_at_0_50"])
    )
    failures = [
        {
            "filename": row["filename"],
            "ast": row["ast_failure"],
            "resnet": row["resnet_failure"],
        }
        for row in rows
        if row["ast_failure"] or row["resnet_failure"]
    ]
    print(
        "Inference failures: %d total (AST %d, ResNet %d)"
        % (
            sum(bool(row["ast_failure"]) + bool(row["resnet_failure"]) for row in rows),
            sum(bool(row["ast_failure"]) for row in rows),
            sum(bool(row["resnet_failure"]) for row in rows),
        )
    )
    print("AST average subsequent time: %s" % _fmt_seconds(ast_timing["average_subsequent_seconds"]))
    print("ResNet average subsequent time: %s" % _fmt_seconds(resnet_timing["average_subsequent_seconds"]))

    result = {
        "offline_mode": offline,
        "sample_selection": {
            "clean_directory": str(Path(args.clean_dir)),
            "knocking_directory": str(Path(args.knocking_dir)),
            "samples_per_class": args.samples_per_class,
            "sorting": "filename ascending, suffix .wav case-insensitive",
        },
        "models": metadata,
        "resnet_preprocessing": {
            "sample_rate": TARGET_SAMPLE_RATE,
            "mono": "average channels",
            "resample_only_if_needed": True,
            "mel_spectrogram": {
                "n_fft": N_FFT,
                "hop_length": HOP_LENGTH,
                "n_mels": N_MELS,
                "other_torchaudio_defaults": True,
            },
            "amplitude_to_db": "torchaudio default parameters",
            "resize": {"size": [IMAGE_SIZE, IMAGE_SIZE], "mode": "bilinear"},
            "channels": "repeat mono spectrogram to 3 channels",
            "additional_normalization": "none in published inference snippet",
        },
        "cache_assets": assets,
        "asset_preparation_failures": asset_errors,
        "files": rows,
        "metrics": {"ast": ast_metrics, "resnet": resnet_metrics},
        "timing": {"ast": ast_timing, "resnet": resnet_timing},
        "inference_failures": failures,
    }
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print("\nJSON report: %s" % output_path)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clean-dir", type=Path, default=DEFAULT_CLEAN_DIR)
    parser.add_argument("--knocking-dir", type=Path, default=DEFAULT_KNOCKING_DIR)
    parser.add_argument("--samples-per-class", type=int, default=20)
    parser.add_argument("--output", type=Path, help="Optional JSON report path.")
    args = parser.parse_args()
    if args.samples_per_class < 1:
        parser.error("--samples-per-class must be positive")
    try:
        run(args)
    except Exception as error:
        print("BAKEOFF BLOCKER: %s: %s" % (type(error).__name__, error), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
