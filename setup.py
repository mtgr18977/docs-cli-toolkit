# setup.py (VERSÃO SIMPLIFICADA PARA TRABALHAR COM PYPROJECT.TOML)
from setuptools import setup

setup(
    # name, version, install_requires, python_requires, entry_points
    # são agora primariamente lidos do pyproject.toml pelo setuptools moderno.
    # No entanto, py_modules ainda é uma forma comum de especificar módulos
    # de nível superior no setup.py se eles não estiverem em um pacote.
    py_modules=[
        "docs_tc",
        "merge_markdown",
        "extract_data_from_markdown",
        "generate_embeddings",   # Mantenha o typo se o nome do arquivo for assim
        "limpa_csv",
        "evaluate_coverage",
        "generate_report",
        "generate_report_html",
    ]
    # Não é necessário entry_points aqui se todos estiverem no pyproject.toml [project.scripts]
    # Não é necessário install_requires aqui se estiver no pyproject.toml [project.dependencies]
    # Não é necessário python_requires aqui se estiver no pyproject.toml [project.requires-python]
)