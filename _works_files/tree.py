from pathlib import Path

from directory_tree import DisplayTree

main_project_path = Path(__file__).parent.parent


def create_tree_view(skip_list: list[str], work_path: Path, save_path: Path) -> None:
    tree: str = DisplayTree(
        dirPath=str(work_path),
        stringRep=True,
        header=False,
        maxDepth=float("inf"),
        showHidden=False,
        ignoreList=skip_list,
        onlyFiles=False,
        onlyDirs=False,
        sortBy=2,
        raiseException=False,
        printErrorTraceback=False,
        spacing=True,
    )  # pyright: ignore[reportAssignmentType]

    save_path.write_text(f"```\n{tree}\n```", encoding="utf-8")


skip_list = [
    "__pycache__",
    "old",
    "app1.py",
    "example.env",
    "*.html",
    "*.php",
]

paths = [
    (main_project_path / "www/python/src", Path(__file__).parent / "tree.md"),
    (main_project_path / "tests", Path(__file__).parent / "test_tree.md"),
]

for work_path, save_path in paths:
    create_tree_view(skip_list, work_path, save_path)


skip_not_src = skip_list + [
    "www",
    "tests",
    "docs",
    "_works_files",
]

create_tree_view(skip_not_src, main_project_path, Path(__file__).parent / "all.md")
