"""CI pipeline template generator."""

import os

import yaml


TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")


def generate(language: str) -> str:
    """Return a CI pipeline YAML string for the given language.

    Falls back to a generic Python template when the language is unknown.
    """
    language = language.lower()
    candidates = [
        os.path.join(TEMPLATES_DIR, f"{language}-ci.yml"),
        os.path.join(TEMPLATES_DIR, "python-ci.yml"),
    ]

    for path in candidates:
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                content = fh.read()
            # Validate it parses as YAML before returning
            yaml.safe_load(content)
            return content

    raise FileNotFoundError(f"No CI template found for language: {language}")
