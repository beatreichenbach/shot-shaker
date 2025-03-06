from __future__ import annotations

import glob
import logging
import os

try:
    from PySide6 import QtCore, QtGui, QtWidgets

    QAction = QtGui.QAction
    Dialog = QtCore.Qt.WindowType.Dialog
except ImportError:
    from PySide2 import QtCore, QtGui, QtWidgets

    QAction = QtWidgets.QAction
    Dialog = QtCore.Qt.Dialog


import shot_shaker
from shot_shaker import core


logger = logging.getLogger(__name__)


class PathWidget(QtWidgets.QWidget):

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)

        self.browse_func = QtWidgets.QFileDialog.getExistingDirectory

        self._init_ui()
        self._connect_ui()

    def _init_ui(self) -> None:
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(QtCore.QMargins())
        self.setLayout(layout)

        self.path_lineedit = QtWidgets.QLineEdit()
        layout.addWidget(self.path_lineedit)

        self.browse_button = QtWidgets.QToolButton()
        self.browse_button.setText('...')
        layout.addWidget(self.browse_button)

    def _connect_ui(self) -> None:
        self.browse_button.clicked.connect(self._browse)

    def path(self) -> str:
        return self.path_lineedit.text()

    def set_path(self, path: str) -> None:
        return self.path_lineedit.setText(path)

    def _browse(self) -> None:
        path = self.path_lineedit.text()
        if os.path.isfile(path):
            current_dir = os.path.dirname(path)
        elif os.path.isdir(path):
            current_dir = path
        else:
            current_dir = os.path.expanduser('~')

        result = self.browse_func(self, caption='Select a Directory', dir=current_dir)
        if result:
            self.path_lineedit.setText(result)


class CreateShakeDialog(QtWidgets.QDialog):
    file_type = 'fbx'

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self._presets_path = ''

        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowTitle('Create Shake')

        layout = QtWidgets.QFormLayout()
        self.setLayout(layout)

        self.preset_combo = QtWidgets.QComboBox()
        layout.addRow('Preset', self.preset_combo)

        self.start_frame_spin = QtWidgets.QSpinBox()
        layout.addRow('Start Frame', self.start_frame_spin)

        self.weight_spin = QtWidgets.QDoubleSpinBox()
        self.weight_spin.setValue(1)
        layout.addRow('Weight', self.weight_spin)

        dialog_button_box = QtWidgets.QDialogButtonBox()
        dialog_button_box.setStandardButtons(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        dialog_button_box.accepted.connect(self.accept)
        dialog_button_box.rejected.connect(self.reject)
        layout.addWidget(dialog_button_box)

    def set_presets_path(self, path: str) -> None:
        self._presets_path = path

        self.preset_combo.clear()
        glob_pattern = os.path.join(self._presets_path, f'*.{self.file_type}')
        for path in glob.glob(glob_pattern):
            name, ext = os.path.splitext(os.path.basename(path))
            self.preset_combo.addItem(name)

    def get_data(self) -> core.CreateShakeData:
        preset_name = self.preset_combo.currentText()
        preset = os.path.join(self._presets_path, f'{preset_name}.{self.file_type}')
        start_frame = self.start_frame_spin.value()
        weight = self.weight_spin.value()
        data = core.CreateShakeData(
            preset=preset, start_frame=start_frame, weight=weight
        )
        return data


class ShotShaker(QtWidgets.QWidget):

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self._init_ui()
        self.refresh()
        self.presets_path.set_path(r'D:\files\dev\shot-shaker\presets')

    def _init_ui(self) -> None:
        self.setWindowTitle('Shot Shaker')
        self.resize(1280, 720)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        # Toolbar
        toolbar = QtWidgets.QToolBar()
        layout.addWidget(toolbar)

        action = QAction('Create', parent=self)
        action.triggered.connect(self.create_shake)
        toolbar.addAction(action)

        action = QAction('Delete', parent=self)
        action.triggered.connect(self.delete)
        toolbar.addAction(action)

        action = QAction('Refresh', parent=self)
        action.triggered.connect(self.refresh)
        toolbar.addAction(action)

        # Presets
        preset_layout = QtWidgets.QFormLayout()
        layout.addLayout(preset_layout)
        self.presets_path = PathWidget()
        preset_layout.addRow('Presets', self.presets_path)

        # TreeWidget
        self.camera_tree = QtWidgets.QTreeWidget()
        self.camera_tree.setHeaderLabels(
            ('Camera', 'Weight', 'Start Frame', 'Preset', 'Mute', 'Bake')
        )
        self.camera_tree.itemChanged.connect(self._item_changed)
        layout.addWidget(self.camera_tree)

    def create_shake(self) -> None:
        cameras = self.selected_cameras()
        if not cameras:
            return

        dialog = CreateShakeDialog(parent=self)
        dialog.set_presets_path(self.presets_path.path())
        result = dialog.exec()
        if result == QtWidgets.QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            for camera in cameras:
                camera.create_shake(data)
            self.refresh()

    def selected_cameras(self) -> tuple[core.Camera, ...]:
        cameras = []
        for item in self.camera_tree.selectedItems():
            data = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            if isinstance(data, core.Camera):
                cameras.append(data)
        return tuple(cameras)

    def delete(self) -> None:
        selected_cameras = self.selected_cameras()
        for camera in selected_cameras:
            camera.delete()
        self.refresh()

    def refresh(self) -> None:
        self.camera_tree.clear()
        for camera in core.get_cameras():
            item = QtWidgets.QTreeWidgetItem()
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)
            item.setText(0, camera.name)
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, camera)
            self.camera_tree.addTopLevelItem(item)

            for layer in camera.layers:
                child = QtWidgets.QTreeWidgetItem()
                child.setFlags(child.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)
                child.setText(0, layer.name)
                child.setData(0, QtCore.Qt.ItemDataRole.UserRole, layer)
                child.setData(1, QtCore.Qt.ItemDataRole.DisplayRole, layer.weight)
                child.setData(2, QtCore.Qt.ItemDataRole.DisplayRole, layer.start_frame)
                child.setData(3, QtCore.Qt.ItemDataRole.DisplayRole, layer.preset)
                if layer.muted:
                    checkstate = QtCore.Qt.CheckState.Checked
                else:
                    checkstate = QtCore.Qt.CheckState.Unchecked
                child.setCheckState(4, checkstate)
                child.setCheckState(5, QtCore.Qt.CheckState.Unchecked)
                item.addChild(child)

            item.setExpanded(True)
        for column in range(self.camera_tree.columnCount()):
            self.camera_tree.resizeColumnToContents(column)

    def _item_changed(self, item: QtWidgets.QTreeWidgetItem, column: int) -> None:
        data = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if isinstance(data, core.Camera):
            camera = data

            if column == 0:
                name = item.text(column)
                camera.set_name(name)

        if isinstance(data, core.Layer):
            layer = data

            if column == 1:
                weight = item.data(1, QtCore.Qt.ItemDataRole.DisplayRole)
                layer.set_weight(weight)
            elif column == 2:
                start_frame = item.data(2, QtCore.Qt.ItemDataRole.DisplayRole)
                layer.set_start_frame(start_frame)
            elif column == 4:
                muted = item.checkState(4) == QtCore.Qt.CheckState.Checked
                layer.set_muted(muted)


window = None


def show() -> None:
    init_logging()

    global window
    if window is None:
        logger.debug(f'Creating new window ...')
        window = ShotShaker()
        main_window = get_main_window()
        window.setParent(main_window, Dialog)
    window.show()


def init_logging() -> None:
    logging.basicConfig()
    logging.getLogger(shot_shaker.__name__).setLevel(logging.INFO)


def get_main_window() -> QtWidgets.QWidget:
    """Get main window."""

    from pymxs import runtime as rt

    return QtWidgets.QWidget.find(rt.windows.getMAXHWND())
