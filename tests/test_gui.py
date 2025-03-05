import logging
import sys

from PySide6 import QtWidgets

from shot_shaker.gui import CreateShakeDialog, ShotShaker


def main() -> None:
    logging.basicConfig(level=logging.DEBUG, force=True)

    app = QtWidgets.QApplication()

    widget = ShotShaker()
    widget.show()

    create_shake_dialog = CreateShakeDialog()
    create_shake_dialog.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
