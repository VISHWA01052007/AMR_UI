from setuptools import find_packages, setup

package_name = "ui"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),

    data_files=[
        (
            "share/ament_index/resource_index/packages",
            ["resource/" + package_name],
        ),
        (
            "share/" + package_name,
            ["package.xml"],
        ),
    ],

    package_data={
        package_name: [
            "resources/style.qss",
            "resources/icons/*",
        ],
    },

    include_package_data=True,

    install_requires=[
        "setuptools",
    ],

    zip_safe=True,

    maintainer="vishwa",
    maintainer_email="vishwags26@gmail.com",

    description="Autonomous Mobile Robot Dashboard UI",

    extras_require={
        "test": [
            "pytest",
        ],
    },

    entry_points={
        "console_scripts": [
            "ui_node = ui.ui_node:main",
        ],
    },
)
