import subprocess
import os
import time
import sys
from cli.utils import getLogger
from cli.consts import (
    ARCHGW_DOCKER_NAME,
    KATANEMO_LOCAL_MODEL_LIST,
)
from huggingface_hub import snapshot_download
import subprocess
from cli.docker_cli import (
    docker_container_status,
    docker_remove_container,
    docker_start_archgw_detached,
    docker_stop_container,
    health_check_endpoint,
    stream_gateway_logs,
)


log = getLogger(__name__)


def start_arch(arch_config_file, env, log_timeout=120, foreground=False):
    """
    Start Docker Compose in detached mode and stream logs until services are healthy.

    Args:
        path (str): The path where the prompt_config.yml file is located.
        log_timeout (int): Time in seconds to show logs before checking for healthy state.
    """
    log.info("Starting arch gateway")

    try:
        archgw_container_status = docker_container_status(ARCHGW_DOCKER_NAME)
        if archgw_container_status != "not found":
            log.info("archgw found in docker, stopping and removing it")
            docker_stop_container(ARCHGW_DOCKER_NAME)
            docker_remove_container(ARCHGW_DOCKER_NAME)

        return_code, _, archgw_stderr = docker_start_archgw_detached(
            arch_config_file, os.path.expanduser("~/archgw_logs"), env
        )
        if return_code != 0:
            log.info("Failed to start arch gateway: " + str(return_code))
            log.info("stderr: " + archgw_stderr)
            sys.exit(1)

        start_time = time.time()
        while True:
            health_check_status = health_check_endpoint(
                "http://localhost:10000/healthz"
            )
            archgw_status = docker_container_status(ARCHGW_DOCKER_NAME)
            current_time = time.time()
            elapsed_time = current_time - start_time

            # Check if timeout is reached
            if elapsed_time > log_timeout:
                log.info(f"stopping log monitoring after {log_timeout} seconds.")
                break

            if health_check_status:
                log.info("archgw is running and is healthy!")
                break
            else:
                log.info(f"archgw status: {archgw_status}, health status: starting")
                time.sleep(1)

        if foreground:
            stream_gateway_logs(follow=True)

    except KeyboardInterrupt:
        log.info("Keyboard interrupt received, stopping arch gateway service.")
        stop_arch()


def stop_arch():
    """
    Shutdown all Docker Compose services by running `docker-compose down`.

    Args:
        path (str): The path where the docker-compose.yml file is located.
    """
    log.info("Shutting down arch gateway service.")

    try:
        subprocess.run(
            ["docker", "stop", ARCHGW_DOCKER_NAME],
        )
        subprocess.run(
            ["docker", "remove", ARCHGW_DOCKER_NAME],
        )

        log.info("Successfully shut down arch gateway service.")

    except subprocess.CalledProcessError as e:
        log.info(f"Failed to shut down services: {str(e)}")


def download_models_from_hf():
    for model in KATANEMO_LOCAL_MODEL_LIST:
        log.info(f"Downloading model: {model}")
        snapshot_download(repo_id=model)


def start_arch_modelserver(foreground):
    """
    Start the model server. This assumes that the archgw_modelserver package is installed locally

    """
    try:
        log.info("archgw_modelserver restart")
        if foreground:
            subprocess.run(
                ["archgw_modelserver", "start", "--foreground"],
                check=True,
            )
        else:
            subprocess.run(
                ["archgw_modelserver", "start"],
                check=True,
            )
    except subprocess.CalledProcessError as e:
        log.info(f"Failed to start model_server. Please check archgw_modelserver logs")
        sys.exit(1)


def stop_arch_modelserver():
    """
    Stop the model server. This assumes that the archgw_modelserver package is installed locally

    """
    try:
        subprocess.run(
            ["archgw_modelserver", "stop"],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        log.info(f"Failed to start model_server. Please check archgw_modelserver logs")
        sys.exit(1)
