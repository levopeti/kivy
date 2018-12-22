from distutils.core import setup
from setuptools import find_packages

options = {'apk': {'debug': None,  # use None for arguments that don't pass a value
                   'requirements': 'python3crystax==3.5,numpy,pysdl2,kivy,Pillow',
                   'android-api': 23,
                   'ndk-dir': '/home/biot/Android/crystax-ndk-10.3.2',
                   'dist-name': 'bdisttest',
                   'arch': 'armeabi-v7a',
                   'sdk_dir': '/home/biot/Android',
                   'ndk_version': '10.3.2',
                   'bootstrap': 'sdl2',
                   }}

packages = find_packages()
print('packages are', packages)

setup(
    name='D_S_8',
    version='2.9',
    description='prupack',
    author='LevoPeti',
    author_email='beracom@freemail.hu',
    packages='d_s_8',
    options=options,
    package_data={'dig_rec_2': ['*.py', '*.kv', '*.txt']}
)


