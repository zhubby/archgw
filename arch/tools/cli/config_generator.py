import json
import os
from jinja2 import Environment, FileSystemLoader
import yaml
from jsonschema import validate

ENVOY_CONFIG_TEMPLATE_FILE = os.getenv(
    "ENVOY_CONFIG_TEMPLATE_FILE", "envoy.template.yaml"
)
ARCH_CONFIG_FILE = os.getenv("ARCH_CONFIG_FILE", "/app/arch_config.yaml")
ENVOY_CONFIG_FILE_RENDERED = os.getenv(
    "ENVOY_CONFIG_FILE_RENDERED", "/etc/envoy/envoy.yaml"
)
ARCH_CONFIG_SCHEMA_FILE = os.getenv(
    "ARCH_CONFIG_SCHEMA_FILE", "arch_config_schema.yaml"
)


def validate_and_render_schema():
    env = Environment(loader=FileSystemLoader("./"))
    template = env.get_template("envoy.template.yaml")

    try:
        validate_prompt_config(ARCH_CONFIG_FILE, ARCH_CONFIG_SCHEMA_FILE)
    except Exception as e:
        print(str(e))
        exit(1)  # validate_prompt_config failed. Exit

    with open(ARCH_CONFIG_FILE, "r") as file:
        arch_config = file.read()

    with open(ARCH_CONFIG_SCHEMA_FILE, "r") as file:
        arch_config_schema = file.read()

    config_yaml = yaml.safe_load(arch_config)
    config_schema_yaml = yaml.safe_load(arch_config_schema)
    inferred_clusters = {}

    endpoints = config_yaml.get("endpoints", {})

    # override the inferred clusters with the ones defined in the config
    for name, endpoint_details in endpoints.items():
        inferred_clusters[name] = endpoint_details
        endpoint = inferred_clusters[name]["endpoint"]
        if len(endpoint.split(":")) > 1:
            inferred_clusters[name]["endpoint"] = endpoint.split(":")[0]
            inferred_clusters[name]["port"] = int(endpoint.split(":")[1])

    print("defined clusters from arch_config.yaml: ", json.dumps(inferred_clusters))

    if "prompt_targets" in config_yaml:
        for prompt_target in config_yaml["prompt_targets"]:
            name = prompt_target.get("endpoint", {}).get("name", None)
            if not name:
                continue
            if name not in inferred_clusters:
                raise Exception(
                    f"Unknown endpoint {name}, please add it in endpoints section in your arch_config.yaml file"
                )

    arch_tracing = config_yaml.get("tracing", {})

    llms_with_endpoint = []

    updated_llm_providers = []
    for llm_provider in config_yaml["llm_providers"]:
        provider = None
        if llm_provider.get("provider") and llm_provider.get("provider_interface"):
            raise Exception(
                "Please provide either provider or provider_interface, not both"
            )
        if llm_provider.get("provider"):
            provider = llm_provider["provider"]
            llm_provider["provider_interface"] = provider
            del llm_provider["provider"]
        updated_llm_providers.append(llm_provider)

        if llm_provider.get("endpoint", None):
            endpoint = llm_provider["endpoint"]
            if len(endpoint.split(":")) > 1:
                llm_provider["endpoint"] = endpoint.split(":")[0]
                llm_provider["port"] = int(endpoint.split(":")[1])
            llms_with_endpoint.append(llm_provider)

    config_yaml["llm_providers"] = updated_llm_providers

    arch_config_string = yaml.dump(config_yaml)
    arch_llm_config_string = yaml.dump(config_yaml)

    data = {
        "arch_config": arch_config_string,
        "arch_llm_config": arch_llm_config_string,
        "arch_clusters": inferred_clusters,
        "arch_llm_providers": config_yaml["llm_providers"],
        "arch_tracing": arch_tracing,
        "local_llms": llms_with_endpoint,
    }

    rendered = template.render(data)
    print(ENVOY_CONFIG_FILE_RENDERED)
    print(rendered)
    with open(ENVOY_CONFIG_FILE_RENDERED, "w") as file:
        file.write(rendered)


def validate_prompt_config(arch_config_file, arch_config_schema_file):
    with open(arch_config_file, "r") as file:
        arch_config = file.read()

    with open(arch_config_schema_file, "r") as file:
        arch_config_schema = file.read()

    config_yaml = yaml.safe_load(arch_config)
    config_schema_yaml = yaml.safe_load(arch_config_schema)

    try:
        validate(config_yaml, config_schema_yaml)
    except Exception as e:
        print(
            f"Error validating arch_config file: {arch_config_file}, schema file: {arch_config_schema_file}, error: {e.message}"
        )
        raise e


if __name__ == "__main__":
    validate_and_render_schema()
