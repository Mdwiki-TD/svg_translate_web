import ast
import os
from pathlib import Path


def extract_classes_and_functions(file_path):
    """Parse the file and extract only the top-level class and function names."""
    classes = []
    functions = []
    try:
        file_content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(file_content)

        # Use tree.body to iterate over top-level elements only.
        # This prevents extracting functions defined inside classes or other functions.
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                # Ignore classes starting with _
                if not node.name.startswith("_"):
                    classes.append(node.name)

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Ignore functions starting with _
                if not node.name.startswith("_"):
                    functions.append(node.name)

    except SyntaxError:
        # Ignore files with Syntax Errors
        pass
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")

    return classes, functions


def generate_domain_test_placeholders(src_root, test_root, src_name: str = "src") -> None:
    """Generates test placeholders based on the source directory structure."""
    src_path = Path(src_root)
    test_base_unit = Path(test_root) / "unit"
    test_base_integration = Path(test_root) / "integration"

    list_of_all_tests_files = [x.name for x in Path(test_root).rglob("*.py")]
    duplicate_names = []

    for root, _dirs, files in os.walk(src_path):
        current_path = Path(root)

        # if "domain" not in current_path.parts: continue

        # Extract the relative path after the project folder
        # Use current_path.relative_to(src_path) to get the path inside the source dir
        rel_path = current_path.relative_to(src_path)

        for file in files:
            target_dir = test_base_unit / rel_path
            if file.endswith(".py"):
                parent_name = current_path.stem
                file_path = current_path / file

                file_stem = Path(file).stem
                if "routes" in current_path.parts or file_stem == "routes":
                    target_dir = test_base_integration / rel_path

                to_re = [
                    "worker",
                    "utils",
                    "objects",
                    "routes",
                ]
                if file_stem in to_re:
                    test_filename = f"test_{parent_name}_{file_stem}.py"

                else:
                    test_filename = f"test_{file_stem}.py"

                if file == "__init__.py":
                    file_content = file_path.read_text(encoding="utf-8")
                    if "def " not in file_content:
                        continue
                    else:
                        test_filename = f"test_{parent_name}_init.py"

                if "routes_routes" in test_filename:
                    test_filename = test_filename.replace("routes_routes", "routes")

                if test_filename in list_of_all_tests_files:
                    duplicate_names.append(test_filename)
                    continue

                # Create the directory if it doesn't exist
                target_dir.mkdir(parents=True, exist_ok=True)
                test_file_path = target_dir / test_filename

                # The path that will appear in the docstring
                # Find the index of the "{src_name}" part to build the internal path
                parts = current_path.parts
                try:
                    internal_path = "/".join(parts[parts.index(f"{src_name}") :])
                except ValueError:
                    internal_path = "/".join(parts)

                # Extract classes and functions from the current file
                classes, functions = extract_classes_and_functions(file_path)

                # Format the lists as strings for the Docstring
                classes_str = ", ".join(classes) if classes else ""
                functions_str = ", ".join(functions) if functions else ""

                # Combine classes and functions to create the import statement
                items_to_import = classes + functions

                if items_to_import:
                    # Convert elements to a comma-separated string
                    items_str = ", ".join(items_to_import)

                    # Convert path (e.g., {src_name}/main_app/domain) to python path ({src_name}.main_app.domain)
                    module_path = f"{internal_path.replace('/', '.')}.{file_stem}"

                    if module_path.endswith(".__init__"):
                        module_path = f"{internal_path.replace('/', '.')}"

                    # Create absolute import statement (safer for tests)
                    import_statement = f"from {module_path} import (\n    {items_str},\n)"

                    # If you prefer to use relative imports, you can enable this line instead:
                    # import_statement = f"from ..{file_stem} import ({items_str})"
                else:
                    import_statement = ""

                methods_parts = []
                if classes_str:
                    methods_parts.append(f"Classes to test: {classes_str}")
                if functions_str:
                    methods_parts.append(f"Functions to test: {functions_str}")

                _new = [
                    '"""',
                    f"Unit tests for {internal_path}/{file} module.",
                    "",
                    "\n".join(methods_parts),
                    "",
                    "TODO: write tests",
                    '"""',
                    "\n",
                    import_statement,
                ]
                # ------------------------------------------------
                _old = [
                    '"""',
                    f"Unit tests for {internal_path}/{file} module.",
                    "TODO: write tests",
                    '"""',
                    "\n",
                ]
                content_old = "\n".join(_old)
                # ------------------------------------------------
                content_new = "\n".join(_new)

                if test_file_path.exists():
                    test_text = test_file_path.read_text(encoding="utf-8")
                    if test_text != content_old:
                        # continue to skip goto next part
                        continue

                # save content_new to the file
                with open(test_file_path, "w", encoding="utf-8") as f:
                    f.write(content_new)

    print(f"Duplicate file names: {len(duplicate_names):,}")


if __name__ == "__main__":
    main_path = Path(__file__).parent.parent

    SOURCE_DIR = main_path / "src/main_app"
    TEST_DIR = main_path / "tests"

    print(f"SOURCE_DIR: {SOURCE_DIR}")
    print(f"TEST_DIR: {TEST_DIR}")

    generate_domain_test_placeholders(SOURCE_DIR, TEST_DIR, src_name="src")
