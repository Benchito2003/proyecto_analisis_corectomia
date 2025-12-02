#!/bin/bash
for FILENAME in *.bak; do mv "$FILENAME" "${FILENAME%.bak}"; done
