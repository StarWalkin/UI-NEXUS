# Copyright 2024 DeepMind Technologies Limited.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A class that manages an Android Emulator."""
import datetime
import os
import time
from typing import Any

from absl import logging
from android_env.components import adb_controller
from android_env.components import adb_log_stream
from android_env.components import config_classes
from android_env.components import errors
from android_env.components import log_stream
from android_env.components.simulators import base_simulator
from android_env.proto import state_pb2
import grpc
import numpy as np
import portpicker
from PIL import Image
import io


class DeviceSimulator(base_simulator.BaseSimulator):
    """Controls an Android Emulator."""

    def __init__(self, config: config_classes.EmulatorConfig, device_serial: str):
        """Instantiates an EmulatorSimulator."""

        super().__init__(verbose_logs=config.verbose_logs)
        self._config = config
        self.device_serial = device_serial

        # If adb_port, console_port and grpc_port are all already provided,
        # we assume the emulator already exists and there's no need to launch.
        self._existing_emulator_provided = True
        logging.info('Connecting to existing emulator "%r"', self.adb_device_name())

        self._channel = None

        # Initialize own ADB controller.
        self._config.adb_controller.device_name = self.adb_device_name()
        self._adb_controller = self.create_adb_controller()
        self._adb_controller.init_server()
        logging.info(
            "Initialized simulator with ADB server port %r.",
            self._config.adb_controller.adb_server_port,
        )

        self._logfile_path = self._config.logfile_path or None
        self._launcher = None

    def get_logs(self) -> str:
        """Returns logs recorded by the emulator."""
        if self._logfile_path and os.path.exists(self._logfile_path):
            with open(self._logfile_path, "rb") as f:
                return f.read().decode("utf-8")
        else:
            return f"Logfile does not exist: {self._logfile_path}."

    def adb_device_name(self) -> str:
        return self.device_serial

    def create_adb_controller(self):
        """Returns an ADB controller which can communicate with this simulator."""
        return adb_controller.AdbController(self._config.adb_controller)

    def create_log_stream(self) -> log_stream.LogStream:
        return adb_log_stream.AdbLogStream(
            adb_command_prefix=self._adb_controller.command_prefix(), verbose=self._verbose_logs
        )

    def _launch_impl(self) -> None:
        """Prepares an Android Emulator for RL interaction.

        The behavior depends on `self._num_launch_attempts`'s value:
          * <= self._config.launch_n_times_without_reboot   -> Normal boot behavior.
          * > self._config.launch_n_times_without_reboot but <=
              self._config.launch_n_times_without_reinstall -> reboot (i.e. process
              is killed and started again).
          * > self._config.launch_n_times_without_reinstall -> reinstall (i.e.
              process is killed, emulator files are deleted and the process started
              again).
        """

        logging.info(
            "Attempt %r at launching the Android Emulator (%r)", self._num_launch_attempts, self.adb_device_name()
        )
        logging.info("Done booting the Android Emulator.")

    def send_touch(self, touches: list[tuple[int, int, bool, int]]) -> None:
        """Sends a touch event to be executed on the simulator.

        Args:
          touches: A list of touch events. Each element in the list corresponds to a
              single touch event. Each touch event tuple should have:
              0 x: The horizontal coordinate of this event.
              1 y: The vertical coordinate of this event.
              2 is_down: Whether the finger is touching or not the screen.
              3 identifier: Identifies a particular finger in a multitouch event.
        """

        for t in touches:
            self._adb_controller.execute_command(['shell', 'input', 'tap', str(t[0]), str(t[1])])

    def send_key(self, keycode: np.int32, event_type: str) -> None:
        """Sends a key event to the emulator.

        Args:
          keycode: Code representing the desired key press in XKB format.
            See the emulator_controller_pb2 for details.
          event_type: Type of key event to be sent.
        """

        # event_types = emulator_controller_pb2.KeyboardEvent.KeyEventType.keys()
        # if event_type not in event_types:
        #     raise ValueError(f"Event type must be one of {event_types} but is {event_type}.")
        #
        # assert self._emulator_stub is not None, "Emulator stub has not been initialized yet."
        # self._emulator_stub.sendKey(
        #     emulator_controller_pb2.KeyboardEvent(
        #         codeType=emulator_controller_pb2.KeyboardEvent.KeyCodeType.XKB,
        #         eventType=emulator_controller_pb2.KeyboardEvent.KeyEventType.Value(event_type),
        #         keyCode=int(keycode),
        #     )
        # )

    def get_screenshot(self) -> np.ndarray:
        """Fetches the latest screenshot from the emulator."""

        image_bytes = self._adb_controller.execute_command(['exec-out', 'screencap', '-p'])
        image = Image.open(io.BytesIO(image_bytes))
        image_array = np.array(image)[:,:,:3]
        return image_array

    def close(self):
        if self._launcher is not None:
            logging.info("Closing emulator (%r)", self.adb_device_name())
            self._launcher.close()
        self._emulator_stub = None
        self._snapshot_stub = None
        if self._channel is not None:
            self._channel.close()
        super().close()