from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'ai_node'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'msg'), glob('msg/*.msg')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='root',
    maintainer_email='root@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            "ai_speak = ai_node.ai_speak:main",
            'goal_publisher = ai_node.goal_publisher:main',
            'goal_subscriber = ai_node.goal_subscriber:main',
            
        ],
    },
)
