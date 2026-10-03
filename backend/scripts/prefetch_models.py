"""Download the local Hugging Face assets needed by the knock model."""

import importlib
from pathlib import Path


MODEL_ID = "cxlrd/revix-AST-engine-knock"
REQUIRED_PACKAGES = (
    ("torch", "PyTorch", "torch"),
    ("transformers", "Transformers", "transformers"),
    ("huggingface_hub", "Hugging Face Hub", "huggingface_hub"),
)


def _short_error(error: Exception) -> str:
    message = str(error).splitlines()[0].strip() if str(error) else error.__class__.__name__
    return message[:240]


def _check_dependencies() -> bool:
    ready = True
    for module_name, display_name, package_name in REQUIRED_PACKAGES:
        try:
            importlib.import_module(module_name)
        except Exception as error:
            ready = False
            missing_name = getattr(error, "name", None) or package_name
            print(f"[FAIL] {display_name} is unavailable ({missing_name}).")
            print(
                "       Install the model dependencies from Session A "
                f"(missing package: {package_name}) and rerun this command."
            )
        else:
            print(f"[PASS] {display_name} available")
    return ready


def main() -> int:
    print("ACOUSTIC MODEL PREFETCH")
    print(f"Model: {MODEL_ID}")

    if not _check_dependencies():
        print("\nPREFETCH FAILED: required model dependencies are missing.")
        return 1

    try:
        from huggingface_hub import snapshot_download
    except Exception as error:
        print(f"\n[FAIL] Hugging Face download support is unavailable: {_short_error(error)}")
        print("       Check the installed huggingface_hub package and rerun this command.")
        return 1

    try:
        cache_path = snapshot_download(repo_id=MODEL_ID, local_files_only=True)
        already_cached = True
    except Exception:
        # A cache miss is expected on the first run. snapshot_download uses the
        # standard Hugging Face cache and reuses any files already present.
        try:
            cache_path = snapshot_download(repo_id=MODEL_ID)
            already_cached = False
        except Exception as error:
            print(f"\n[FAIL] Could not cache {MODEL_ID}: {_short_error(error)}")
            print("       Check network access and that the public model is reachable.")
            print("       No hosted inference or paid account is used.")
            return 1

    resolved_cache_path = Path(cache_path).expanduser().resolve()
    if not resolved_cache_path.is_dir():
        print(f"\n[FAIL] Hugging Face returned a missing cache directory: {resolved_cache_path}")
        return 1

    if already_cached:
        print("[PASS] Model artifacts already present in the local cache")
    else:
        print("[PASS] Model and processor artifacts downloaded to the local cache")
    print(f"Cache path: {resolved_cache_path}")
    print("Ready to run preflight; keep this cache on the demo machine.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
