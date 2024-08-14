import docker
import time
import os
import base64
import matplotlib.pyplot as plt
import io
from src.utils import PathInfo
from src.logger_setup import logger
import shutil

class DockerPythonREPL:
    def __init__(self, image_name='python:3.11.9-slim', verbose=True, data_dir=None):
        self.client = docker.from_env()
        self.container = None
        self.image_name = image_name
        self.verbose = verbose
        self.data_dir = PathInfo.CSV_PATH or os.getcwd()

    def __enter__(self):
        self.start_container()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop_container()

    def start_container(self):
        if self.verbose:
            logger.info(f"Creating new Docker container using image {self.image_name}...")
        volumes = {self.data_dir: {'bind': '/data', 'mode': 'ro'}}
        self.container = self.client.containers.run(
            self.image_name,
            detach=True,
            tty=True,
            command="tail -f /dev/null",
            volumes=volumes
        )
        if self.verbose:
            logger.info(f"Container created with ID: {self.container.id}")

        while self.container.status != 'running':
            time.sleep(0.5)
            self.container.reload()

    def install_package(self, package_name):
        if not self.container or self.container.status != 'running':
            self.start_container()
        if self.verbose:
            logger.info(f"Installing package: {package_name}")
        install_command = f"pip install {package_name}"
        result = self.container.exec_run(install_command)
        if result.exit_code != 0:
            logger.info(f"Error installing {package_name}: {result.output.decode()}")
        elif self.verbose:
            logger.info(f"Package {package_name} installed successfully")

    def run(self, code):
        if not self.container or self.container.status != 'running':
            self.start_container()

        for line in code.split('\n'):
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                package = line.split()[1].split('.')[0]
                self.install_package(package)

        code = "import matplotlib\nmatplotlib.use('Agg')\n" + code

        if 'import matplotlib.pyplot as plt' in code or 'from matplotlib import pyplot as plt' in code:
            code += "\n\nimport io\nimport base64\nbuf = io.BytesIO()\nplt.savefig(buf, format='png')\nbuf.seek(0)\nplot_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')\nprint('PLOT_BASE64:' + plot_base64)\nplt.close()"

        exec_command = f"python -c \"{code}\""

        if self.verbose:
            logger.info(f"Executing code in container: \n\n{code}\n\n")

        result = self.container.exec_run(exec_command)

        output = result.output.decode()

        if 'PLOT_BASE64:' in output:
            logger.info("Passing the base 64 image representation back to the host machine...")
            plot_data = output.split('PLOT_BASE64:')[1].strip()
            return {"figure_1": {"type": "image", "base64_data": plot_data},
                    "output": output}
        else:
            return output

    def stop_container(self):
        if self.container:
            if self.verbose:
                logger.info(f"Stopping container {self.container.id}")
            self.container.stop()
            if self.verbose:
                logger.info(f"Removing container {self.container.id}")
            self.container.remove()
            self.container = None
            if self.verbose:
                logger.info("Container stopped and removed")