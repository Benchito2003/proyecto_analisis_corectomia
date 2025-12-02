#!/bin/bash
for f in *.ogg; do
  mv "$f" "$f.bak"
done
