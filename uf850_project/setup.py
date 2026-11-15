
from setuptools import find_packages, setup
from glob import glob

package_name = 'uf850_project'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),

    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),

        ('share/' + package_name,
            ['package.xml']),

        ('share/' + package_name + '/launch',
            glob('launch/*.launch.py')),

        ('share/' + package_name + '/models/block',
            glob('models/block/*.sdf')),

        ('share/' + package_name + '/scripts',
            glob('scripts/*.py')),
    ],

    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='gnabin',
    maintainer_email='gnabin@todo.todo',
    description='ROB545 UF850 Gazebo simulation project',
    license='TODO: License declaration',

    extras_require={
        'test': [
            'pytest',
        ],
    },

    entry_points={
        'console_scripts': [
        ],
    },
)

