cwd = getFilenamePath(getSourceFileName())
cwd = trimright cwd "\\/"
code = "import sys; cwd = r'" + cwd + "'; sys.path.insert(1, cwd); from shot_shaker import setup; setup.install(cwd)"
python.Execute code
