import yaml


def load_yaml(path):
    with open(path, "r") as file:
        return yaml.safe_load(file)
