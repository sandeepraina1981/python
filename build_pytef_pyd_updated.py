
# Updated build_pytef_pyd.py
from pathlib import Path
from setuptools import setup, Extension
from Cython.Build import cythonize
from multiprocessing import freeze_support
import os
import sys
import traceback

EXCLUDE_DIRS = {
    "backend",
    "frontend",
    "fastapi",
    "examples",
    "templates",
    "testbench",
}

EXCLUDE_FILES = {
    "__init__.py",
    "__main__.py",
}

EXCLUDE_FILE_NAMES = {
    "BackendRunner.py",
    "TestBenchRunner.py",
}

SKIP_PATTERNS = (
    "quicktest",
    "example",
)

KNOWN_BAD_MODULES_FILE = "known_bad_modules.txt"


def build_module_name(root: Path, pyfile: Path) -> str:
    rel = pyfile.relative_to(root)
    return ".".join(rel.with_suffix("").parts)


def load_known_bad_modules(root):
    path = root / KNOWN_BAD_MODULES_FILE
    if not path.exists():
        return set()
    with open(path, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def save_known_bad_modules(root, bad_modules):
    path = root / KNOWN_BAD_MODULES_FILE
    with open(path, "w", encoding="utf-8") as f:
        for item in sorted(bad_modules):
            f.write(item + "\n")


def discover_bad_modules(root, sources, known_bad_modules):
    bad_modules = []
    total = len(sources)

    print("\nDiscovering Cython incompatible modules...")

    for idx, pyfile in enumerate(sources, start=1):

        rel = str(pyfile.relative_to(root)).replace('\\', '/')

        if rel in known_bad_modules:
            continue

        try:
            module_name = build_module_name(root, pyfile)

            cythonize(
                [Extension(module_name, [str(pyfile)])],
                compiler_directives={"language_level": "3"},
                quiet=True,
                force=False,
            )

        except BaseException as ex:
            bad_modules.append(rel)
            print(f"[BAD {len(bad_modules)}] {rel}")
            print(f"      {type(ex).__name__}")

        if idx % 50 == 0:
            print(f"Checked {idx}/{total}")

    return bad_modules


def build_extensions(root, sources):
    return [
        Extension(
            build_module_name(root, pyfile),
            [str(pyfile)],
            extra_compile_args=["/MP"],
        )
        for pyfile in sources
    ]


def run_build(root, sources):
    extensions = build_extensions(root, sources)

    ext_modules = cythonize(
        extensions,
        compiler_directives={"language_level": "3"},
        quiet=False,
        force=False,
        nthreads=max(1, os.cpu_count() or 1),
    )

    setup(
        script_args=["build_ext", "--inplace"],
        ext_modules=ext_modules,
    )


def main():

    if len(sys.argv) < 2:
        raise RuntimeError(
            "Usage: python build_pytef_pyd.py <pytef_root>"
        )

    root = Path(sys.argv[1]).resolve()

    compiled_modules_file = root / "compiled_modules.txt"
    failed_modules_file = root / "failed_modules.txt"
    skipped_modules_file = root / "skipped_modules.txt"

    known_bad_modules = load_known_bad_modules(root)

    print(f"PyTeF Root : {root}")
    print(f"Loaded {len(known_bad_modules)} known bad modules")

    original_cwd = os.getcwd()
    os.chdir(root)

    try:
        sources = []
        skipped = []

        for pyfile in root.rglob("*.py"):

            if pyfile.name in EXCLUDE_FILES:
                continue

            if pyfile.name in EXCLUDE_FILE_NAMES:
                skipped.append((str(pyfile), "Excluded file"))
                continue

            rel_path = pyfile.relative_to(root)

            if rel_path.parts[0] in EXCLUDE_DIRS:
                skipped.append((str(pyfile), f"Excluded dir: {rel_path.parts[0]}"))
                continue

            if not pyfile.stem.isidentifier():
                skipped.append((str(pyfile), "Invalid module name"))
                continue

            if any(p in pyfile.name.lower() for p in SKIP_PATTERNS):
                skipped.append((str(pyfile), "Utility/Test file"))
                continue

            rel_name = str(rel_path).replace('\\', '/')

            if rel_name in known_bad_modules:
                skipped.append((str(pyfile), "Known compile failure"))
                continue

            sources.append(pyfile)

        compiled = []
        failed = []

        with open(skipped_modules_file, 'w', encoding='utf-8') as f:
            for filename, reason in skipped:
                f.write(f'{reason} : {filename}\n')

        try:
            print(f"\nGenerating Cython sources using {max(1, os.cpu_count() or 1)} threads...")
            run_build(root, sources)
            compiled.extend(str(x) for x in sources)
            print("\n[SUCCESS] FULL BUILD SUCCESS")

        except BaseException:
            print("\n[ERROR] Global build failed")
            traceback.print_exc()

            new_bad_modules = discover_bad_modules(
                root,
                sources,
                known_bad_modules,
            )

            if new_bad_modules:
                known_bad_modules.update(new_bad_modules)
                save_known_bad_modules(root, known_bad_modules)
                print(f"\nSaved {len(known_bad_modules)} known bad modules")

            filtered_sources = []

            for pyfile in sources:
                rel_name = str(pyfile.relative_to(root)).replace('\\', '/')

                if rel_name in known_bad_modules:
                    failed.append((str(pyfile), 'Cython incompatible'))
                    continue

                filtered_sources.append(pyfile)

            print(f"\nRetrying build with {len(filtered_sources)} modules")

            try:
                run_build(root, filtered_sources)
                compiled.extend(str(x) for x in filtered_sources)
                print("\n[SUCCESS] Build completed after excluding incompatible modules.")
            except BaseException:
                print("\n[ERROR] Retry build failed")
                traceback.print_exc()
                return 1

        with open(compiled_modules_file, 'w', encoding='utf-8') as f:
            for module in compiled:
                f.write(module + '\n')

        with open(failed_modules_file, 'w', encoding='utf-8') as f:
            for module, reason in failed:
                f.write(module + '\n')
                f.write(reason + '\n')
                f.write('-' * 80 + '\n')

        print("\n====================================")
        print("Compilation Summary")
        print("====================================")
        print(f"Compiled : {len(compiled)}")
        print(f"Failed   : {len(failed)}")
        print(f"Skipped  : {len(skipped)}")
        print(f"Known Bad: {len(known_bad_modules)}")
        print("====================================")

        return 0

    finally:
        os.chdir(original_cwd)


if __name__ == '__main__':
    freeze_support()
    sys.exit(main())
