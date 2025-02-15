import subprocess
import json
import sys
import requests  # Add this import

from cli.consts import ARCHGW_DOCKER_IMAGE, ARCHGW_DOCKER_NAME
from cli.utils import getLogger

log = getLogger(__name__)


def docker_container_status(container: str) -> str:
    result = subprocess.run(
        ["docker", "inspect", container], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        return "not found"
    return json.loads(result.stdout)[0]["State"]["Status"]


def docker_stop_container(container: str) -> str:
    result = subprocess.run(
        ["docker", "stop", container], capture_output=True, text=True, check=False
    )
    return result.returncode


def docker_remove_container(container: str) -> str:
    result = subprocess.run(
        ["docker", "remove", container], capture_output=True, text=True, check=False
    )
    return result.returncode


def docker_start_archgw_detached(
    arch_config_file: str, logs_path_abs: str, env: dict
) -> str:
    env_args = [item for key, value in env.items() for item in ["-e", f"{key}={value}"]]

    port_mappings = ["10000:10000", "12000:12000", "9901:19901"]
    port_mappings_args = [item for port in port_mappings for item in ("-p", port)]

    volume_mappings = [
        f"{logs_path_abs}:/var/log:rw",
        f"{arch_config_file}:/app/arch_config.yaml:ro",
    ]
    volume_mappings_args = [
        item for volume in volume_mappings for item in ("-v", volume)
    ]

    options = [
        "docker",
        "run",
        "-d",
        "--name",
        ARCHGW_DOCKER_NAME,
        *port_mappings_args,
        *volume_mappings_args,
        *env_args,
        "--add-host",
        "host.docker.internal:host-gateway",
        ARCHGW_DOCKER_IMAGE,
    ]

    result = subprocess.run(options, capture_output=True, text=True, check=False)
    return result.returncode, result.stdout, result.stderr


def health_check_endpoint(endpoint: str) -> bool:
    try:
        response = requests.get(endpoint)
        if response.status_code == 200:
            return True
    except requests.RequestException as e:
        pass
    return False


def stream_gateway_logs(follow):
    """
    Stream logs from the arch gateway service.
    """
    log.info("Logs from arch gateway service.")

    options = ["docker", "logs", ARCHGW_DOCKER_NAME]
    if follow:
        options.append("-f")
    try:
        # Run `docker-compose logs` to stream logs from the gateway service
        subprocess.run(
            options,
            check=True,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )

    except subprocess.CalledProcessError as e:
        log.info(f"Failed to stream logs: {str(e)}")


def docker_validate_archgw_schema(arch_config_file):
    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{arch_config_file}:/app/arch_config.yaml:ro",
            "--entrypoint",
            "python",
            ARCHGW_DOCKER_IMAGE,
            "config_generator.py",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode, result.stdout, result.stderr
