import ast
from pathlib import Path

from tqdm import tqdm

list_files = """
tests/main_app/admins/test_admin_service.py
"""

list_files = [x.strip() for x in list_files.splitlines() if x.strip()]

main_dir = Path(__file__).parent

created = 0


def get_file_functions(file_path: Path) -> list[str]:
    """
    Use AST to get all functions in file.

    Args:
        file_path: Path to the Python file to analyze.

    Returns:
        List of function names found in the file.
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)
        functions = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef | ast.ClassDef):
                continue

            if ": Blueprint)" in source or "Blueprint(" in source:
                continue

            if f"    def {node.name}(" in source:
                continue

            if node.name.startswith("_"):
                continue

            functions.append(node.name)

        return functions
    except (SyntaxError, UnicodeDecodeError, FileNotFoundError) as e:
        print(f"Error reading {file_path}: {e}")
        return []


for x in tqdm(list_files):
    file_path = main_dir / x
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if not file_path.exists():
        srcpath_str = x.replace("tests/", "src/").replace("test_", "")
        src_path = Path(main_dir / srcpath_str)

        if src_path.exists():
            file_functions = get_file_functions(Path(main_dir / srcpath_str))

            if file_functions:
                file_functions_str = ",\n".join([f"    {x}" for x in file_functions])
                file_text = (
                    '"""\n'
                    f"TODO:write tests for {srcpath_str}\n"
                    '"""\n'
                    "\n\n"
                    f"from {srcpath_str.replace(".py", "").replace("/", ".")} import (\n"
                    f"{file_functions_str}\n"
                    ")\n"
                )
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(file_text)
                created += 1
                # break

print(f"{created=}")
