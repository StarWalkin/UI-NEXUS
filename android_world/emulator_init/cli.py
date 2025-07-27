"""Command line interface for emulator initialization."""

from absl import app, flags, logging

from .core import EmulatorInitializer
from .utils.helpers import get_default_adb_path


FLAGS = flags.FLAGS

flags.DEFINE_string('config_path', None, 'Path to configuration JSON file.')
flags.DEFINE_integer(
    'console_port', 5554, 'Console port of the Android emulator.'
)
flags.DEFINE_string(
    'adb_path',
    get_default_adb_path(),
    'Path to the ADB binary.',
)
flags.DEFINE_integer(
    'grpc_port', 8554, 'Port for gRPC communication with the emulator.'
)
flags.DEFINE_boolean(
    'emulator_setup', False, 'Perform first-time app setup on the environment.'
)
flags.DEFINE_string(
    'device_serial', None, 'Serial number of the target Android device. If provided and does not start with "emulator-", will be treated as a physical device.'
)

flags.mark_flag_as_required('config_path')


def main(argv):
    """Main function to run the emulator initialization."""
    del argv  # Unused.
    
    initializer = EmulatorInitializer(
        config_path=FLAGS.config_path,
        console_port=FLAGS.console_port,
        adb_path=FLAGS.adb_path,
        grpc_port=FLAGS.grpc_port,
        emulator_setup=FLAGS.emulator_setup,
        device_serial=FLAGS.device_serial,
    )
    
    success = initializer.initialize()
    
    if not success:
        logging.error("Emulator initialization failed")
        exit(1)
    else:
        logging.info("Emulator initialization completed successfully")


def run_cli():
    """Entry point for running the CLI."""
    app.run(main)  