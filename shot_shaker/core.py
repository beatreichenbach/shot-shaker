from __future__ import annotations

import dataclasses
import json
import logging
import os
import random

from pymxs import runtime as rt

from shot_shaker import lib

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class CreateShakeData:
    preset: str
    start_frame: int
    weight: float


class Layer:
    def __init__(self, name: str, camera: Camera) -> None:
        self.name = name
        self.camera = camera
        self.weight = self.get_weight()
        self.start_frame = self.get_start_frame()
        self.preset = self.get_preset()
        self.animated = self.is_animated()
        self.muted = self.get_muted()

    def get_muted(self) -> bool:
        indexes = rt.AnimLayerManager.getNodesLayers((self.camera.node,))
        for i in indexes:
            layer = rt.AnimLayerManager.getLayerName(i)
            if layer == self.name:
                return rt.AnimLayerManager.getLayerMute(i)
        return False

    def set_muted(self, muted: bool) -> None:
        indexes = rt.AnimLayerManager.getNodesLayers((self.camera.node,))
        for i in indexes:
            layer = rt.AnimLayerManager.getLayerName(i)
            if layer == self.name:
                rt.AnimLayerManager.setLayerMute(i, muted)

    def get_preset(self) -> str:
        layers_string = rt.getUserProp(self.camera.node, 'layers')
        if not layers_string:
            return ''
        layers = json.loads(layers_string)
        layer = layers.get(self.name, {})
        preset_path = layer.get('preset', '')
        name, ext = os.path.splitext(os.path.basename(preset_path))
        return name

    def get_weight(self) -> float:
        controller = rt.getPropertyController(self.camera.node.controller, 'Rotation')
        if rt.classof(controller) == rt.Rotation_layer:
            for i in range(controller.count):
                name = controller.getLayerName(i + 1)
                if name == self.name:
                    weight = controller.getLayerWeight(i + 1, rt.slidertime)
                    return weight
        return 0

    def set_weight(self, weight: float) -> None:
        controller = rt.getPropertyController(self.camera.node.controller, 'Rotation')
        if rt.classof(controller) == rt.Rotation_layer:
            for i in range(controller.count):
                name = controller.getLayerName(i + 1)
                if name == self.name:
                    controller.setLayerWeight(i + 1, rt.slidertime, weight)
        self.animated = self.is_animated()

    def get_start_frame(self) -> int:
        layers = lib.get_sub_animtables(self.camera.node, self.name)
        for layer in layers:
            if rt.classof(layer.controller) == rt.Euler_XYZ:
                if len(layer.controller.keys):
                    time = rt.getkeytime(layer.controller, 1)
                    return int(time)
                break
        return 0

    def set_start_frame(self, start_frame: int) -> None:
        offset = start_frame - self.start_frame
        lib.offset_keys(self.camera.node, self.name, offset)
        self.start_frame = start_frame

    def is_animated(self) -> bool:
        controller = rt.getPropertyController(self.camera.node.controller, 'Rotation')
        if rt.classof(controller) == rt.Rotation_layer:
            for i in range(controller.count):
                name = controller.getLayerName(i + 1)
                # if name == self.name:
                # logger.debug(f'{rt.classof(controller)=}')
                # weight_controller = controller.weight[i].controller
                # return (
                #     weight_controller is not None
                #     and weight_controller.keys.count > 1
                # )
        return False


class Camera:
    def __init__(self, node) -> None:
        self.node = node
        self.name = node.name
        self.layers = self.get_layers()
        self.baked = False

    def set_name(self, name: str) -> None:
        self.node.name = name
        self.name = self.node.name

    def add_layer(
        self, preset_path: str, weight: float = 1, start_frame: int = 0
    ) -> None:
        if not os.path.exists(preset_path):
            logger.error(f'The preset {preset_path!r} does not exist.')
            return

        rt.ImportFile(preset_path, rt.Name('noPrompt'), using='FBXIMP')

        preset_name, ext = os.path.splitext(os.path.basename(preset_path))

        preset_camera = rt.getNodeByName(preset_name)
        if not preset_camera:
            logger.warning(f'The camera in the preset does not match the preset name.')
            return

        anim_names = lib.get_sub_animtable_names(self.node)
        iteration = 1
        name = preset_name
        if name in anim_names:
            while True:
                name = preset_name + str(iteration)
                if name in anim_names:
                    iteration += 1
                    continue
                break

        rt.AnimLayerManager.enableLayers(self.node)
        random_name = str(random.getrandbits(16))
        rt.AnimLayerManager.addLayer(random_name, self.node, False)
        lib.set_layer_name(self.node, random_name, name)

        lib.copy_layer_controllers(self.node, name, preset_camera, start_frame)
        rt.delete(preset_camera)
        rt.select(self.node)

        controller = rt.getPropertyController(self.node.controller, 'Rotation')
        controller.setLayerActive(1)

        # Update metadata
        layers_string = rt.getUserProp(self.node, 'layers')
        if layers_string:
            layers = json.loads(layers_string)
        else:
            layers = {}
        layers[name] = {'preset': preset_path}
        rt.setUserProp(self.node, 'layers', json.dumps(layers))

        layer = Layer(name=name, camera=self)
        layer.set_weight(weight)
        layer.start_frame = start_frame

    def get_layers(self) -> tuple[Layer, ...]:
        logger.debug(f'Getting layers for {self.node}')

        base_layer = rt.AnimLayerManager.getLayerName(1)

        layers = []
        controller = rt.getPropertyController(self.node.controller, 'Rotation')
        if rt.classof(controller) == rt.Rotation_layer:
            for i in range(controller.getCount()):
                name = controller.getLayerName(i + 1)
                if name != base_layer:
                    layer = Layer(name=name, camera=self)
                    layers.append(layer)
        return tuple(layers)

    def delete(self) -> None:
        rt.delete(self.node)

    def create_shake(self, data: CreateShakeData) -> None:
        with lib.suspended_refresh():
            self.add_layer(
                preset_path=data.preset,
                weight=data.weight,
                start_frame=data.start_frame,
            )


def get_cameras() -> tuple[Camera, ...]:
    cameras = []
    for obj in rt.objects:
        if not rt.isKindOf(obj, rt.Camera):
            continue
        camera = Camera(node=obj)
        cameras.append(camera)
    return tuple(cameras)
