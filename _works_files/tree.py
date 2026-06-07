from pathlib import Path

from directory_tree import DisplayTree

work_path = Path(__file__).parent.parent / "src"
tree_save_path = Path(__file__).parent.parent / "tree.md"

tree: str = DisplayTree(
    dirPath=str(work_path),
    stringRep=True,
    header=False,
    maxDepth=float("inf"),
    showHidden=False,
    ignoreList=["__pycache__", "old", "app1.py", "example.env", "*.html", "app_main"],
    onlyFiles=False,
    onlyDirs=False,
    sortBy=2,
    raiseException=False,
    printErrorTraceback=False,
)

tree_save_path.write_text(f"```\n{tree}\n```", encoding="utf-8")

# ---

test_tree_save_path = Path(__file__).parent.parent / "test_tree.md"

test_tree: str = DisplayTree(
    dirPath=str(Path(__file__).parent.parent / "tests"),
    stringRep=True,
    header=False,
    maxDepth=float("inf"),
    showHidden=False,
    ignoreList=["__pycache__", "old", "app1.py", "example.env", "*.html"],
    onlyFiles=False,
    onlyDirs=False,
    sortBy=2,
    raiseException=False,
    printErrorTraceback=False,
)

test_tree_save_path.write_text(f"```\n{test_tree}\n```", encoding="utf-8")
