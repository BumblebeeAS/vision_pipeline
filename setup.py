import os
from glob import glob

from setuptools import find_namespace_packages, setup

package_name = "vision_pipeline"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_namespace_packages(include=[package_name, package_name + ".*"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (
            os.path.join("share", package_name, "launch"),
            glob(os.path.join("launch", "*launch.[pxy][yma]*")),
        ),
        (
            os.path.join("share", package_name, "launch"),
            glob(os.path.join("launch", "robotx", "*launch.[pxy][yma]*")),
        ),
        (
            os.path.join("share", package_name, "config", "auv4_orin"),
            glob(os.path.join("config", "auv4_orin", "*.yaml")),
        ),
        (
            os.path.join("share", package_name, "config", "auv5"),
            glob(os.path.join("config", "auv5", "*.yaml")),
        ),
        (
            os.path.join("share", package_name, "config", "uav"),
            glob(os.path.join("config", "uav", "*.yaml")),
        ),
        (
            os.path.join("share", package_name, "config", "asv5"),
            glob(os.path.join("config", "asv5", "*.yaml")),
        ),
        (
            os.path.join("share", package_name, "config", "uav", "calib"),
            glob(os.path.join("config", "uav", "calib", "*.yaml")),
        ),
        (
            os.path.join("share", package_name, "config", "asv5"),
            glob(os.path.join("config", "asv5", "*.yaml")),
        )
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="todo",
    maintainer_email="todo@todo.com",
    description="Collection of launch files for vision-related nodes.",
    license="todo",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "lifecycle_manager_node = vision_pipeline.lifecycle_manager_node:main",
            "component_manager_node = vision_pipeline.component_manager_node:main",
        ],
    },
)
