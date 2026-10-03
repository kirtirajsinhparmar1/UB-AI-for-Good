"""Model weights are intentionally not downloaded by the bootstrap."""


def main() -> None:
    raise SystemExit("No model weights are configured; no downloads were attempted.")


if __name__ == "__main__":
    main()
