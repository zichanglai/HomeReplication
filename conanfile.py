from os.path import join
from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import copy
from conan.tools.build import check_min_cppstd
from conans import CMake

required_conan_version = ">=1.50.0"

class HomeReplicationConan(ConanFile):
    name = "home_replication"
    version = "0.1.1"
    homepage = "https://github.com/eBay/HomeReplication"
    description = "Fast Storage Replication using NuRaft"
    topics = ("ebay")
    url = "https://github.com/eBay/HomeReplication"
    license = "Apache-2.0"

    settings = "arch", "os", "compiler", "build_type"

    options = {
                "shared": ['True', 'False'],
                "fPIC": ['True', 'False'],
                "coverage": ['True', 'False'],
                "sanitize": ['True', 'False'],
                "testing": ['True', 'False'],
              }
    default_options = {
                'shared': False,
                'fPIC': True,
                'coverage': False,
                'sanitize': False,
                'testing': False,
                'sisl:prerelease': True,
            }

    generators = "cmake", "cmake_find_package"
    exports_sources = ("CMakeLists.txt", "cmake/*", "src/*", "LICENSE")

    def build_requirements(self):
        self.build_requires("gtest/1.13.0")

    def requirements(self):
        self.requires("nuraft_mesg/[~=1,    include_prerelease=True]@oss/main")
        self.requires("homestore/[~=4,      include_prerelease=True]@oss/master")
        self.requires("sisl/[~=10,          include_prerelease=True]@oss/master")

    def validate(self):
        if self.info.settings.os in ["Macos", "Windows"]:
            raise ConanInvalidConfiguration("{} Builds are unsupported".format(self.info.settings.os))
        if self.info.settings.compiler.cppstd:
            check_min_cppstd(self, 11)

    def configure(self):
        if self.options.shared:
            del self.options.fPIC
        if self.settings.build_type == "Debug":
            if self.options.coverage and self.options.sanitize:
                raise ConanInvalidConfiguration("Sanitizer does not work with Code Coverage!")
            if self.options.sanitize:
                self.options['sisl'].malloc_impl = 'libc'
            if self.options.coverage:
                self.options.testing = True

    def build(self):
        definitions = {
            'CMAKE_EXPORT_COMPILE_COMMANDS': 'ON',
            'CONAN_CMAKE_SILENT_OUTPUT': 'ON',
        }

        if self.settings.build_type == "Debug":
            if self.options.sanitize:
                definitions['MEMORY_SANITIZER_ON'] = 'ON'
            elif self.options.coverage:
                definitions['BUILD_COVERAGE'] = 'ON'

        cmake = CMake(self)
        cmake.configure(defs=definitions)
        cmake.build()
        if self.options.testing:
             cmake.test(output_on_failure=True)

    def package(self):
        lib_dir = join(self.package_folder, "lib")
        copy(self, "LICENSE", self.source_folder, join(self.package_folder, "licenses"), keep_path=False)
        copy(self, "*.lib", self.build_folder, lib_dir, keep_path=False)
        copy(self, "*.a", self.build_folder, lib_dir, keep_path=False)
        copy(self, "*.dylib*", self.build_folder, lib_dir, keep_path=False)
        copy(self, "*.dll*", self.build_folder, join(self.package_folder, "bin"), keep_path=False)
        copy(self, "*.so*", self.build_folder, lib_dir, keep_path=False)
        copy(self, "*", join(self.source_folder, "src", "flip", "client", "python"), join(self.package_folder, "bindings", "flip", "python"), keep_path=False)

        copy(self, "*.h*", join(self.source_folder, "src", "include"), join(self.package_folder, "include"), keep_path=True)

    def package_info(self):
        self.cpp_info.names["cmake_find_package"] = "HomeReplication"
        self.cpp_info.names["cmake_find_package_multi"] = "HomeReplication"
        self.cpp_info.components["nuraft"].libs = ["home_replication"]
        self.cpp_info.components["nuraft"].requires = ["nuraft_mesg::nuraft_mesg", "homestore::homestore"]
        self.cpp_info.components["mock"].libs = ["home_replication_mock"]
        self.cpp_info.components["mock"].requires = ["nuraft_mesg::nuraft_mesg", "homestore::homestore"]

        if self.settings.os == "Linux":
            self.cpp_info.components["nuraft"].system_libs.append("pthread")
            self.cpp_info.components["mock"].system_libs.append("pthread")
