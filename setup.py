from setuptools import find_namespace_packages, setup

setup(
    name="cli-anything-scholar",
    version="1.0.0",
    description="学术搜索 CLI — 学者与论文检索（OpenAlex）",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    install_requires=["click>=8.0"],
    python_requires=">=3.11",
    entry_points={
        "console_scripts": [
            "cli-anything-scholar=cli_anything.scholar.__main__:main",
        ],
    },
)
