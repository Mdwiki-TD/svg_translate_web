import ast
import os
from pathlib import Path


def extract_exportable_items(file_path):
    """Parse the file to extract top-level names and check if __all__ already exists."""
    classes = []
    functions = []
    has_all = False

    try:
        file_content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(file_content)

        for node in tree.body:
            # Check if __all__ is already defined in the file
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__":
                        has_all = True

            # Extract top-level classes
            elif isinstance(node, ast.ClassDef):
                if not node.name.startswith("_"):
                    classes.append(node.name)

            # Extract top-level functions and async functions
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith("_"):
                    functions.append(node.name)

    except SyntaxError:
        # Ignore files with Syntax Errors
        pass
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")

    return classes, functions, has_all


def add_all_to_source_files(src_root):
    """Walks through the source directory and appends __all__ to .py files."""
    src_path = Path(src_root)

    for root, _dirs, files in os.walk(src_path):
        current_path = Path(root)

        for file in files:
            if not file.endswith(".py"):
                continue

            # Optional: Skip __init__.py files if you don't want __all__ in them automatically
            # if file == "__init__.py":
            #     continue

            file_path = current_path / file

            # Extract items and check for existing __all__
            classes, functions, has_all = extract_exportable_items(file_path)
            items_to_export = classes + functions

            # Skip the file if __all__ already exists or if there's nothing to export
            if has_all or not items_to_export:
                continue

            # Format the items for the __all__ list (e.g., "Item1",\n    "Item2")
            formatted_items = ",\n    ".join(f'"{item}"' for item in items_to_export)

            # Create the __all__ statement block
            all_statement = f"\n\n__all__ = [\n    {formatted_items},\n]\n"

            # Append the __all__ block to the end of the original file
            # Appending to the end is the safest approach programmatically
            # to avoid breaking line numbers or inserting between decorators and functions.
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(all_statement)

            print(f"Successfully added __all__ to {file_path}")


if __name__ == "__main__":
    # Adjust this path based on where you place this script relative to your project
    main_path = Path(__file__).parent.parent

    # Define the source directory to modify
    SOURCE_DIR = main_path / "src/main_app"

    print(f"Starting to process files in: {SOURCE_DIR}")
    add_all_to_source_files(SOURCE_DIR)
