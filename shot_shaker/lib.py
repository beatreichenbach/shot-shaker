from __future__ import annotations

import contextlib
import logging
import sys
from collections.abc import Iterator

from pymxs import runtime as rt

import shot_shaker

logger = logging.getLogger(__name__)


def reload() -> None:
    name = shot_shaker.__name__
    logger.info(f'Unloading package: {name}')
    unload_package(name)


def unload_package(package_name: str) -> None:
    for key, module in list(sys.modules.items()):
        if module and module.__name__.startswith(package_name):
            if 'schema' in module.__name__:
                continue
            del sys.modules[key]


@contextlib.contextmanager
def suspended_refresh() -> Iterator[None]:
    rt.disableSceneRedraw()
    rt.suspendEditing()
    try:
        yield
    finally:
        rt.enableSceneRedraw()
        rt.resumeEditing()


def set_layer_name(obj, old: str, new: str) -> None:
    controller = rt.getPropertyController(obj.controller, 'Rotation')
    for i in range(controller.getCount()):
        layer_name = controller.getLayerName(i + 1)
        if layer_name == old:
            controller.setLayerName(i + 1, new)


def copy_layer_controllers(obj, name: str, source, start_frame: int) -> None:
    layers = get_sub_animtables(obj, name)
    source_layers = get_sub_animtables(source, 'Rotation')
    logger.debug(f'{layers=}')
    logger.debug(f'{source_layers=}')
    for layer in layers:
        logger.debug(f'{rt.classof(layer.controller)=}')
        if rt.classof(layer.controller) == rt.Euler_XYZ:
            rotation = layer.controller
            source = source_layers[0].controller
            logger.debug(f'Copying {source} to {rotation}')
            for i in range(3):
                rotation[i].controller = rt.copy(source[i].controller)
                rt.movekeys(rotation[i].controller, start_frame)


def get_sub_animtables(obj, name: str) -> tuple:
    subs = []
    if obj:
        for i in range(obj.numsubs):
            try:
                sub = obj[i]
            except IndexError:
                continue
            if sub.name == name:
                subs.append(sub)
            subs.extend(get_sub_animtables(sub, name))
    return tuple(subs)


def get_sub_animtable_names(obj) -> tuple[str, ...]:
    names = []
    if obj:
        for i in range(obj.numsubs):
            try:
                sub = obj[i]
            except IndexError:
                continue
            names.append(sub.name)
            names.extend(get_sub_animtable_names(sub))
    return tuple(names)


def offset_keys(obj, name: str, offset: int) -> None:
    layers = get_sub_animtables(obj, name)
    for layer in layers:
        if rt.classof(layer.controller) == rt.Euler_XYZ:
            for i in range(3):
                rt.movekeys(layer.controller[i].controller, offset)
