### Environment setup #########################################################
FROM mcr.microsoft.com/devcontainers/base:ubuntu-22.04

# set PYTHONPATH to include src directory
ENV PYTHONPATH=src

# Prevent creation of __pycache__ directories
ENV PYTHONDONTWRITEBYTECODE=1

# Make output unbuffered (useful for logging/debugging)
ENV PYTHONUNBUFFERED=1

# set pip cache directory
ENV PIP_CACHE_DIR=/home/vscode/.cache/pip

# create pip cache directory and set permissions
RUN mkdir -p /home/vscode/.cache/pip
RUN chown -R vscode:vscode /home/vscode/.cache

# Install Python 3.13 + SWI-Prolog 8.4
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    software-properties-common gnupg ca-certificates \
    # Python 3.13 from deadsnakes PPA
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        python3.13 python3.13-venv python3.13-dev swi-prolog \
        # Bootstrap pip (required for deadsnakes Python 3.13)
    && python3.13 -m ensurepip \
    # Make Python 3.13 the default
    && python3.13 -m pip install --upgrade pip pip-tools \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.13 1 \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3.13 1 \
    # Cleanup
    && apt-get purge -y --auto-remove software-properties-common gnupg \
    && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /workspace
