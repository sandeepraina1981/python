# Batch optimized build_pytef_pyd.py
from pathlib import Path
from setuptools import setup, Extension
from Cython.Build import cythonize
from multiprocessing import freeze_support
import os, sys, traceback

BATCH_SIZE=300
KNOWN_BAD_MODULES_FILE="known_bad_modules.txt"
EXCLUDE_DIRS={"backend","frontend","fastapi","examples","templates","testbench"}
EXCLUDE_FILES={"__init__.py","__main__.py"}
EXCLUDE_FILE_NAMES={"BackendRunner.py","TestBenchRunner.py"}
SKIP_PATTERNS=("quicktest","example")

def build_module_name(root,pyfile):
    return ".".join(pyfile.relative_to(root).with_suffix("").parts)

def chunk_list(items,size):
    for i in range(0,len(items),size):
        yield items[i:i+size]

def load_known_bad_modules(root):
    p=root/KNOWN_BAD_MODULES_FILE
    if not p.exists(): return set()
    return {x.strip() for x in p.read_text(encoding="utf-8").splitlines() if x.strip()}

def save_known_bad_modules(root,mods):
    (root/KNOWN_BAD_MODULES_FILE).write_text("\n".join(sorted(mods)),encoding="utf-8")

def build_extensions(root,files):
    return [Extension(build_module_name(root,f),[str(f)],extra_compile_args=["/MP"]) for f in files]

def run_batch_build(root,files):
    ext=cythonize(build_extensions(root,files),compiler_directives={"language_level":"3"},quiet=False,force=False,nthreads=max(1,os.cpu_count() or 1))
    setup(script_args=["build_ext","--inplace"],ext_modules=ext)

def main():
    root=Path(sys.argv[1]).resolve()
    known=load_known_bad_modules(root)
    compiled=[]; failed=[]; skipped=[]
    os.chdir(root)
    sources=[]
    for pyfile in root.rglob("*.py"):
        if pyfile.name in EXCLUDE_FILES: continue
        if pyfile.name in EXCLUDE_FILE_NAMES: continue
        rel=pyfile.relative_to(root)
        if rel.parts[0] in EXCLUDE_DIRS: continue
        if any(p in pyfile.name.lower() for p in SKIP_PATTERNS): continue
        relname=str(rel).replace('\\','/')
        if relname in known: skipped.append(relname); continue
        sources.append(pyfile)
    for batch_no,batch in enumerate(chunk_list(sources,BATCH_SIZE),start=1):
        try:
            print(f'Batch {batch_no}: {len(batch)} files')
            run_batch_build(root,batch)
            compiled.extend(map(str,batch))
        except Exception:
            traceback.print_exc()
            for pyfile in batch:
                try:
                    run_batch_build(root,[pyfile])
                    compiled.append(str(pyfile))
                except Exception:
                    rel=str(pyfile.relative_to(root)).replace('\\','/')
                    known.add(rel)
                    failed.append((str(pyfile),'Cython incompatible'))
    save_known_bad_modules(root,known)
    (root/'compiled_modules.txt').write_text('\n'.join(compiled),encoding='utf-8')
    (root/'failed_modules.txt').write_text('\n'.join(f'{m} | {r}' for m,r in failed),encoding='utf-8')
    (root/'skipped_modules.txt').write_text('\n'.join(skipped),encoding='utf-8')
    return 0

if __name__=='__main__':
    freeze_support()
    sys.exit(main())
