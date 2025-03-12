import logging
import os

from pymxs import runtime as rt

logger = logging.getLogger(__name__)


def install(project_dir: str) -> None:
    try:
        create_macro_scripts(os.path.normpath(project_dir))
    except RuntimeError as e:
        logging.error('Could not install MacroScript.')
        logging.error(e)
        return

    logging.info('Installation successful.')


def create_macro_scripts(path: str) -> None:
    script = (
        'macroScript ShotShaker '
        'category:"Plugins" '
        'tooltip:"Shot Shaker" '
        'buttonText:"Shot Shaker" '
        'Icon:#("Cameras", 1) '
        '(\n'
        '  on execute do (\n'
        '    python.Execute "import sys"\n'
        '    python.Execute "path = r\'' + path + '\'"\n'
        '    python.Execute "if path not in sys.path: sys.path.append(path)"\n'
        '    python.Execute "from shot_shaker.gui import show; show()"\n'
        '  )\n'
        ')'
    )
    rt.execute(script)

    script = (
        'macroScript ShotShakerReload '
        'category:"Plugins" '
        'tooltip:"Shot Shaker Reload" '
        'buttonText:"Shot Shaker Reload" '
        'Icon:#("Cameras", 3) '
        '(\n'
        '  on execute do (\n'
        '    python.Execute "import sys"\n'
        '    python.Execute "path = r\'' + path + '\'"\n'
        '    python.Execute "if path not in sys.path: sys.path.append(path)"\n'
        '    python.Execute "from shot_shaker.lib import reload; reload()"\n'
        '  )\n'
        ')'
    )
    rt.execute(script)
