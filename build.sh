#!/bin/sh

pyinstaller --paths=$PWD --distpath=$PWD/../dist --onefile httpservice.py
rm -rf build
rm httpservice.spec
