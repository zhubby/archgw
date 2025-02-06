import os
import yaml
import logging
import docker
from docker.errors import DockerException

from cli.consts import ARCHGW_DOCKER_IMAGE, ARCHGW_DOCKER_NAME

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def getLogger(name="cli"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger


log = getLogger(__name__)


def update_docker_host_env():
    """
    Update DOCKER_HOST environment variable to use the local Docker socket
    """
    if os.getenv("DOCKER_HOST"):
        return

    default_docker_socket = os.getenv("DEFAULT_DOCKER_SOCKET", "/var/run/docker.sock")
    if not os.path.exists(default_docker_socket):
        home_dir = os.getenv("HOME")
        docker_host = f"unix://{home_dir}/.docker/run/docker.sock"
        log.info(
            f"Default docker socket {default_docker_socket} not found, using {docker_host}"
        )
        os.environ["DOCKER_HOST"] = docker_host


def validate_schema(arch_config_file: str) -> None:
    try:
        try:
            client = docker.from_env()
        except DockerException as e:
            # try setting up the docker host environment variable and retry
            update_docker_host_env()
            client = docker.from_env()

        container = client.containers.run(
            image=ARCHGW_DOCKER_IMAGE,
            volumes={
                f"{arch_config_file}": {
                    "bind": "/app/arch_config.yaml",
                    "mode": "ro",
                },
            },
            entrypoint=["python", "config_generator.py"],
            detach=True,
        )

        # Wait for the container to finish and get the exit code
        exit_code = container.wait()

        # Check exit code for validation success
        if exit_code["StatusCode"] != 0:
            # Validation failed (non-zero exit code)
            logs = container.logs().decode()  # Get container logs for debugging
            raise ValueError(
                f"Validation failed. Container exited with code {exit_code}.\nLogs:\n{logs}"
            )

        # Successful validation (exit code 0)
        log.info("Schema validation successful!")

    except docker.errors.APIError as e:
        # Handle container creation error
        raise ValueError(f"Failed to create container: {e}")


def get_llm_provider_access_keys(arch_config_file):
    with open(arch_config_file, "r") as file:
        arch_config = file.read()
        arch_config_yaml = yaml.safe_load(arch_config)

    access_key_list = []
    for llm_provider in arch_config_yaml.get("llm_providers", []):
        acess_key = llm_provider.get("access_key")
        if acess_key is not None:
            access_key_list.append(acess_key)

    for prompt_target in arch_config_yaml.get("prompt_targets", []):
        for k, v in prompt_target.get("endpoint", {}).get("http_headers", {}).items():
            if k.lower() == "authorization":
                print(
                    f"found auth header: {k} for prompt_target: {prompt_target.get('name')}/{prompt_target.get('endpoint').get('name')}"
                )
                auth_tokens = v.split(" ")
                if len(auth_tokens) > 1:
                    access_key_list.append(auth_tokens[1])
                else:
                    access_key_list.append(v)

    return access_key_list


def load_env_file_to_dict(file_path):
    env_dict = {}

    # Open and read the .env file
    with open(file_path, "r") as file:
        for line in file:
            # Strip any leading/trailing whitespaces
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Split the line into key and value at the first '=' sign
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                # Add key-value pair to the dictionary
                env_dict[key] = value

    return env_dict
