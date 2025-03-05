import logging
import os

from pymxs import runtime as rt

logger = logging.getLogger(__name__)


def install() -> None:
    scripts_path = rt.getDir(rt.Name('userScripts')) or ''
    scripts_path = os.path.normpath(scripts_path)

    if not scripts_path:
        logging.error('Could not find userScripts directory.')
        return

    try:
        create_macro_scripts(scripts_path=scripts_path)
    except RuntimeError as e:
        logging.error('Could not install MacroScript.')
        logging.error(e)
        return

    logging.info('Installation successful.')


def create_macro_scripts(scripts_path: str) -> None:
    script = (
        'macroScript ShotShaker '
        'category:"Plugins" '
        'tooltip:"Shot Shaker" '
        'buttonText:"Shot Shaker" '
        'Icon:#("Cameras", 1) '
        '(\n'
        '  on execute do (\n'
        '    python.Execute "import sys"\n'
        '    python.Execute "path = r\'' + scripts_path + '\'"\n'
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
        '    python.Execute "path = r\'' + scripts_path + '\'"\n'
        '    python.Execute "if path not in sys.path: sys.path.append(path)"\n'
        '    python.Execute "from shot_shaker.lib import reload; reload()"\n'
        '  )\n'
        ')'
    )
    rt.execute(script)
