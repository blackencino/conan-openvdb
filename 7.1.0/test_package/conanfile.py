import os

from conans import ConanFile, CMake, tools

class OpenVDBTestConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake_find_package"

    def build(self):
        cmake = CMake(self, generator='Ninja')
        # Current dir is "test_package/build/<build_id>" and CMakeLists.txt is
        # in "test_package"
        cmake.configure()
        cmake.build()

    def test(self):
        if not tools.cross_building(self):
            bin_path = os.path.join(".", "example")
            usdfile = os.path.join(self.source_folder, "..", "..", "example_data", "example.vdb")
            self.run("{} {}".format(bin_path, usdfile), run_environment=True)
