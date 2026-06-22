from pathlib import Path

from directory_tree import DisplayTree

work_path = Path(__file__).parent.parent / "src"
tree_save_path = Path(__file__).parent / "tree.md"

skip_list = [
    "__pycache__",
    "old",
    "app1.py",
    "example.env",
    "*.html",
    "*.php",
]

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
)

tree_save_path.write_text(f"```\n{tree}\n```", encoding="utf-8")

# ---

test_tree_save_path = Path(__file__).parent / "test_tree.md"

test_tree: str = DisplayTree(
    dirPath=str(Path(__file__).parent.parent / "tests"),
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
)

test_tree_save_path.write_text(f"```\n{test_tree}\n```", encoding="utf-8")
