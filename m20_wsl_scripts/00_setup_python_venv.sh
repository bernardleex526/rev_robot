#!/bin/bash
# Python venv for the repo's MuJoCo digital twin (sim/*.py) and policy tooling.
set -e
python3 -m venv ~/.venvs/m20
~/.venvs/m20/bin/pip install -q --upgrade pip
~/.venvs/m20/bin/pip install -q numpy mujoco onnxruntime onnx scipy pyelftools pyyaml matplotlib scapy rosbags
~/.venvs/m20/bin/python -c "import mujoco,onnxruntime;print('mujoco',mujoco.__version__,'ort',onnxruntime.__version__)"
