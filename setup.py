from setuptools import setup, find_packages

setup(
    name="karaparty_bot",
    version="0.1.0",
    description="A Discord bot to collect and manage YouTube links from multiple channels.",
    author="Your Name",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "discord.py",
        "pyyaml",
        "python-dotenv"
    ],
    entry_points={
        "console_scripts": [
            "karaparty_bot=main:main"
        ]
    },
)
