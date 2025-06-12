from setuptools import setup, find_packages

setup(
    name='email-breach-checker',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'requests',
        'colorama',
        'python-dotenv',
    ],
    entry_points={
        'console_scripts': [
            'email-breach-checker=email_breach_checker.cli:main'
        ]
    },
)
