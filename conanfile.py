#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, AutoToolsBuildEnvironment, tools
import os, shutil


class PixmanConan(ConanFile):
    name = "pixman"
    version = "0.34.0"
    url = "https://github.com/bincrafters/conan-pixman"
    description = "Pixman is a low-level software library for pixel manipulation, providing features such as image compositing and trapezoid rasterization."
    license = "GNU Lesser General Public License (LGPL) version 2.1 or the Mozilla Public License (MPL) version 1.1"
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = "shared=False", "fPIC=True"
    exports_sources = ["*.patch"]

    folder = "{}-{}".format(name, version)
    includedir = os.path.join("include", "pixman-1")

    def config_options(self):
        del self.settings.compiler.libcxx
        if self.settings.os == 'Windows':
            del self.options.fPIC

    def build_requirements(self):
        if tools.os_info.is_windows:
            self.build_requires("msys2_installer/20161025@bincrafters/stable")

    def source(self):
        tools.get("https://www.cairographics.org/releases/{}.tar.gz".format(self.folder))
        tools.patch(patch_file='clang_builtin.patch', base_path=self.folder)

        if self.settings.os == 'Macos':
            # https://lists.freedesktop.org/archives/pixman/2014-November/003461.html
            test_makefile = os.path.join(self.folder, 'test', 'Makefile.in')
            tools.replace_in_file(test_makefile,
                                  'region_test_OBJECTS = region-test.$(OBJEXT)',
                                  'region_test_OBJECTS = region-test.$(OBJEXT) utils.$(OBJEXT)')
            tools.replace_in_file(test_makefile,
                                  'scaling_helpers_test_OBJECTS = scaling-helpers-test.$(OBJEXT)',
                                  'scaling_helpers_test_OBJECTS = scaling-helpers-test.$(OBJEXT) utils.$(OBJEXT)')

    def build_configure(self):
        win_bash = tools.os_info.is_windows
        if self.settings.compiler == "Visual Studio":
            make_vars = {
                "MMX": "on" if self.settings.arch == "x86" else "off",
                "SSE2": "on",
                "SSSE3": "on",
                "CFG": str(self.settings.build_type).lower(),
            }
            tools.replace_in_file(os.path.join(self.folder, 'Makefile.win32.common'),
                                  '-MDd ', '-%s ' % str(self.settings.compiler.runtime))
            tools.replace_in_file(os.path.join(self.folder, 'Makefile.win32.common'),
                                  '-MD ', '-%s ' % str(self.settings.compiler.runtime))
            var_args = " ".join("{}={}".format(k, v) for k, v in make_vars.items())
            self.run("make -C {}/pixman -f Makefile.win32 {}".format(self.folder, var_args),
                     win_bash=win_bash)
            for s, r in {"@prefix@": self.package_folder,
                         "@exec_prefix@":"${prefix}",
                         "@libdir@":"${prefix}/lib",
                         "@includedir@":"${prefix}/include",
                         "@PACKAGE_VERSION@":self.version}.items():
                tools.replace_in_file(os.path.join(self.folder, 'pixman-1.pc.in'),s,r)
        else:
            args = ["--disable-libpng", "--disable-gtk"]
            if self.options.shared:
                args.extend(["--enable-shared", "--disable-static"])
            else:
                args.extend(["--enable-static", "--disable-shared"])
            autotools = AutoToolsBuildEnvironment(self, win_bash=win_bash)
            if self.settings.os != 'Windows':
                autotools.pic = self.options.fPIC
            autotools.configure(configure_dir=self.folder, args=args)
            autotools.make(target="pixman")
            autotools.install()

    def build(self):
        if self.settings.compiler == "Visual Studio":
            with tools.vcvars(self.settings):
                self.build_configure()
        else:
            self.build_configure()

    def package(self):
        if self.settings.compiler == "Visual Studio":
            self.copy(pattern="*.lib", dst="lib", keep_path=False)
            self.copy(pattern="*.pdb", dst="lib", keep_path=False)
            self.copy(pattern="*{}pixman.h".format(os.sep), dst=self.includedir, keep_path=False)
            self.copy(pattern="*{}pixman-version.h".format(os.sep), dst=self.includedir, keep_path=False)
            tools.mkdir(os.path.join(self.package_folder, "lib", "pkgconfig"))
            shutil.copy2(os.path.join(self.folder, 'pixman-1.pc.in'),
                         os.path.join(self.package_folder, "lib", "pkgconfig", 'pixman-1.pc'))

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        self.cpp_info.includedirs = [self.includedir]
