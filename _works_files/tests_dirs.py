from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def replicate_test_structure(source_dir, target_roots):
    """
    Replicate the directory structure from source to multiple targets,
    ignoring __pycache__ directories.
    """
    source_path = Path(source_dir)

    if not source_path.exists():
        print(f"Error: Source {source_dir} does not exist!")
        return

    # Fetch directories only and filter out __pycache__
    subdirs = [
        d for d in source_path.rglob("*")
        if d.is_dir() and "__pycache__" not in d.parts
    ]

    for root in target_roots:
        target_root_path = Path(root)
        target_root_path.mkdir(parents=True, exist_ok=True)
        print(f"\n--- Processing Root: {target_root_path} ---")

        for subdir in subdirs:
            # Get the relative path from the source
            relative_path = subdir.relative_to(source_path)

            # Build the target directory path
            new_target_dir = target_root_path / relative_path

            # Create the directory
            new_target_dir.mkdir(parents=True, exist_ok=True)

            print(f"Created: {new_target_dir}")


if __name__ == "__main__":
    # Define paths relative to the current script's location
    main_dir = Path(__file__).parent.parent
    SOURCE = main_dir / "src/main_app"
    TARGETS = [
        main_dir / "tests/integration",
        main_dir / "tests/unit",
        main_dir / "tests/functional"
    ]

    replicate_test_structure(SOURCE, TARGETS)
    print("\nTask completed successfully. Cache directories were excluded.")
