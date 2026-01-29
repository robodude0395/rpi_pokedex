from setuptools import setup

setup(
    name='display_and_input',
    version='0.1.0',
    description='ST7789 display and input utilities for Raspberry Pi',
    author='Omar Da Best',
    packages=['display_and_input'],
    package_dir={'display_and_input': '.'},
    include_package_data=True,
    install_requires=[
        'spidev',
        'numpy',
        'Pillow',
        'lgpio',
        'gpiozero'
    ],
    package_data={
        'display_and_input': ['Font/*.ttf', 'Font/*.TXT', 'Font/*.txt', 'Monocraft.ttf'],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: POSIX :: Linux',
    ],
)
