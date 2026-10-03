"""Check that the backend and local model assets are ready for a demo."""

import importlib
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEMO_AUDIO_DIR = BACKEND_ROOT / "demo" / "sample_audio"
MODEL_ID = "cxlrd/revix-AST-engine-knock"
MINIMUM_PYTHON = (3, 9)

# Readiness checks and the optional inference smoke test must never fetch assets.
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def _load_module(module_name: str) -> Any:
    return importlib.import_module(module_name)


def _short_error(error: Exception) -> str:
    message = str(error).splitlines()[0].strip() if str(error) else error.__class__.__name__
    return message[:240]


def _check_import(module_name: str, label: str, package_name: Optional[str] = None) -> Tuple[bool, Any]:
    try:
        module = _load_module(module_name)
    except Exception as error:
        missing_name = getattr(error, "name", None) or package_name or module_name
        print(f"[FAIL] {label} ({missing_name}: {_short_error(error)})")
        if package_name:
            print(f"       Install the required package: python -m pip install {package_name}")
        return False, None
    print(f"[PASS] {label}")
    return True, module


def _check_ml_imports() -> Tuple[bool, Dict[str, Any]]:
    modules: Dict[str, Any] = {}
    ready = True
    dependencies = (
        ("torch", "PyTorch", "torch"),
        ("transformers", "Transformers", "transformers"),
        ("huggingface_hub", "Hugging Face Hub", "huggingface_hub"),
    )
    for module_name, label, package_name in dependencies:
        ok, module = _check_import(module_name, label, package_name)
        ready = ready and ok
        if ok:
            modules[module_name] = module
    return ready, modules


def _check_model_cache(hub_module: Optional[Any]) -> Tuple[bool, Optional[Path]]:
    if hub_module is None:
        print("[FAIL] Model weights cached (Hugging Face Hub is unavailable)")
        print("       Install huggingface_hub, then run: python backend/scripts/prefetch_models.py")
        return False, None

    try:
        cache_path = hub_module.snapshot_download(
            repo_id=MODEL_ID,
            local_files_only=True,
        )
    except Exception as error:
        print(f"[FAIL] Model weights cached ({_short_error(error)})")
        print("       Run: python backend/scripts/prefetch_models.py")
        return False, None

    path = Path(cache_path).expanduser().resolve()
    if not path.is_dir():
        print(f"[FAIL] Model weights cached (cache directory is missing: {path})")
        print("       Run: python backend/scripts/prefetch_models.py")
        return False, None
    print("[PASS] Model weights cached")
    print(f"       Cache path: {path}")
    return True, path


def _check_demo_audio() -> Tuple[bool, List[Path]]:
    if not DEMO_AUDIO_DIR.is_dir():
        print("[SKIP] Demo WAV readable (sample_audio directory is not present)")
        return True, []

    wav_paths = sorted(path for path in DEMO_AUDIO_DIR.iterdir() if path.is_file() and path.suffix.lower() == ".wav")
    if not wav_paths:
        print("[SKIP] Demo WAV readable (no WAV files; add real demo recordings to backend/demo/sample_audio/)")
        return True, []

    try:
        from app.model.audio_io import AudioValidationError, validate_wav
    except Exception as error:
        print(f"[FAIL] Demo WAV readable (WAV validator unavailable: {_short_error(error)})")
        return False, []

    valid_paths: List[Path] = []
    for path in wav_paths:
        try:
            validate_wav(str(path))
        except (AudioValidationError, OSError) as error:
            print(f"[FAIL] Demo WAV readable: {path.name} ({_short_error(error)})")
            return False, valid_paths
        valid_paths.append(path)

    names = ", ".join(path.name for path in valid_paths)
    print(f"[PASS] Demo WAV readable ({names})")
    return True, valid_paths


def main() -> int:
    print("ACOUSTIC INTELLIGENCE PREFLIGHT")
    failures = 0

    python_ok = sys.version_info >= MINIMUM_PYTHON
    if python_ok:
        print(f"[PASS] Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    else:
        print(
            f"[FAIL] Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}; "
            f"Python {MINIMUM_PYTHON[0]}.{MINIMUM_PYTHON[1]} or newer is required"
        )
        failures += 1

    backend_ok = True
    for module_name in ("app.model", "app.model.audio_io"):
        ok, _ = _check_import(module_name, f"Backend import: {module_name}")
        backend_ok = backend_ok and ok
    if not backend_ok:
        failures += 1

    ml_ok, ml_modules = _check_ml_imports()
    if not ml_ok:
        failures += 1

    knock_ok, knock_module = _check_import(
        "app.model.knock_model",
        "Knock model available",
    )
    if not knock_ok:
        failures += 1

    cache_ok, _ = _check_model_cache(ml_modules.get("huggingface_hub"))
    if not cache_ok:
        failures += 1

    wav_ok, demo_wavs = _check_demo_audio()
    if not wav_ok:
        failures += 1

    scoring_ok, _ = _check_import("app.scoring.acoustic_score", "Scoring module imports")
    if not scoring_ok:
        failures += 1

    schemas_ok, _ = _check_import("app.schemas", "Schemas import", "pydantic")
    if not schemas_ok:
        failures += 1

    api_ok, _ = _check_import("app.api.main", "API app imports", "fastapi")
    if not api_ok:
        failures += 1

    if not demo_wavs:
        print("[SKIP] Inference smoke test (no readable demo WAV is available)")
    elif not (ml_ok and knock_ok and cache_ok and wav_ok):
        print("[SKIP] Inference smoke test (required checks did not pass)")
    else:
        try:
            from app.model import ModelNotReadyError

            result = knock_module.analyze_knock(demo_wavs[0])
            probability = float(result.knock_probability)
            if not 0.0 <= probability <= 1.0:
                raise ValueError("model returned a probability outside 0.0–1.0")
        except Exception as error:
            detail = _short_error(error)
            if isinstance(error, ModelNotReadyError):
                detail = f"knock inference is not configured: {detail}"
            print(f"[FAIL] Inference smoke test ({detail})")
            failures += 1
        else:
            print("[PASS] Inference smoke test (one real local inference completed)")

    if failures:
        print(f"\nNOT READY FOR DEMO ({failures} critical check(s) failed)")
        return 1
    print("\nREADY FOR DEMO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
