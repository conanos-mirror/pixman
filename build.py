#!/usr/bin/env python
# -*- coding: utf-8 -*-


from bincrafters import build_template_default
import platform
import os

os.environ['CONAN_USERNAME'] = os.environ.get('CONAN_USERNAME','conanos')

if __name__ == "__main__":

    builder = build_template_default.get_builder(shared_option_name=('' if platform.system() == 'Windows' else None))

    builder.run()
