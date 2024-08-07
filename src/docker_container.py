import docker
import time
import os
import base64
import matplotlib.pyplot as plt
import io
from utils import PathInfo

class DockerPythonREPL:
    def __init__(self, image_name='python:3.8-slim', verbose=False, data_dir=None):
        self.client = docker.from_env()
        self.container = None
        self.image_name = image_name
        self.verbose = verbose
        self.data_dir = PathInfo.CSV_PATH #data_dir or os.getcwd() 

    def start_container(self):
        if self.verbose:
            print(f"Creating new Docker container using image {self.image_name}...")
        volumes = {self.data_dir: {'bind': '/data', 'mode': 'ro'}}
        self.container = self.client.containers.run(
            self.image_name,
            detach=True,
            tty=True,
            command="tail -f /dev/null",
            volumes=volumes
        )
        if self.verbose:
            print(f"Container created with ID: {self.container.id}")

        while self.container.status != 'running':
            time.sleep(0.5)
            self.container.reload()

    def install_package(self, package_name):
        if not self.container or self.container.status != 'running':
            self.start_container()
        if self.verbose:
            print(f"Installing package: {package_name}")
        install_command = f"pip install {package_name}"
        result = self.container.exec_run(install_command)
        if result.exit_code != 0:
            print(f"Error installing {package_name}: {result.output.decode()}")
        elif self.verbose:
            print(f"Package {package_name} installed successfully")

    def run(self, code):
        if not self.container or self.container.status != 'running':
            self.start_container()

        for line in code.split('\n'):
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                package = line.split()[1].split('.')[0]
                self.install_package(package)

        if self.verbose:
            print(f"Executing code in container {self.container.id}")

        code = "import matplotlib\nmatplotlib.use('Agg')\n" + code

        if 'import matplotlib.pyplot as plt' in code or 'from matplotlib import pyplot as plt' in code:
            code += "\n\nimport io\nimport base64\nbuf = io.BytesIO()\nplt.savefig(buf, format='png')\nbuf.seek(0)\nplot_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')\nprint('PLOT_BASE64:' + plot_base64)\nplt.close()"

        exec_command = f"python -c \"{code}\""
        result = self.container.exec_run(exec_command)

        output = result.output.decode()

        if 'PLOT_BASE64:' in output:
            plot_data = output.split('PLOT_BASE64:')[1].strip()
            return {"figure_1": {"type": "image", "base64_data": plot_data},
                    "output": output}
        else:
            return output

    def stop_container(self):
        if self.container:
            if self.verbose:
                print(f"Stopping container {self.container.id}")
            self.container.stop()
            if self.verbose:
                print(f"Removing container {self.container.id}")
            self.container.remove()
            self.container = None
            if self.verbose:
                print("Container stopped and removed")