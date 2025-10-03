#!/usr/bin/env bash
set -e

microalpha run -c configs/meanrev.yaml
microalpha wfv -c configs/wfv_meanrev.yaml
