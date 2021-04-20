from conans import ConanFile, CMake, tools
from conans.errors import ConanInvalidConfiguration
import os

class OpenVDBConan(ConanFile):
    name = "OpenVDB"
    version = "7.1.0"
    license = "Mozilla Public License 2.0"
    homepage = "http://openvdb.org/"
    url = "https://github.com/AcademySoftwareFoundation/openvdb.git"
    description = "OpenVDB is an Academy Award-winning open-source " \
        "C++ library comprising a novel hierarchical data structure " \
        "and a suite of tools for the efficient storage and " \
        "manipulation of sparse volumetric data discretized on " \
        "three-dimensional grids."
    topics = ("conan", "openvdb", "voxel", "pointcloud", "vfx", "aswf")
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False]
        }
    default_options = {
        "shared": False,
        "*:fPIC": True
        }
    generators = "cmake", "cmake_find_package", "cmake_paths"
    exports_sources = ["CMakeLists.txt", "patches/*"]

    requires = (
        "boost/1.74.0",
        "openexr/2.5.3",
        "c-blosc/1.20.1",
        "tbb/2020.0",
        "zlib/1.2.11"
    )

    _cmake = None

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    @property
    def _build_subfolder(self):
        return "build_subfolder"

    def config_options(self):
        pass

    def configure(self):
        if self.options.shared:
            raise ConanInvalidConfiguration("OpenVDB only supports shared=False at this time")

    def requirements(self):
        #self.options["tbb"].tbbmalloc = False
        #self.options["tbb"].tbbproxy = False
        self.options["tbb"].shared = False
        self.options["openexr"].shared = False

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        #tools.untargz("C:\\Users\\TM-Z8\\source\\repos\\conan-openvdb\\tmp\\openvdb-7.1.0.tar.gz")
        tools.patch(patch_file="patches/openvdb-7.1.0.patch",
                    base_path="openvdb-{}".format(self.version))
        os.rename("openvdb-{}".format(self.version), self._source_subfolder)

    def _configure_cmake(self):
        if self._cmake:
            return self._cmake
        self._cmake = CMake(self)

        self._cmake.definitions["OPENVDB_BUILD_CORE"] = True
        self._cmake.definitions["OPENVDB_BUILD_BINARIES"] = False
        self._cmake.definitions["OPENVDB_BUILD_PYTHON_MODULE"] = False
        self._cmake.definitions["OPENVDB_BUILD_UNITTESTS"] = False
        self._cmake.definitions["OPENVDB_BUILD_DOCS"] = False
        self._cmake.definitions["OPENVDB_BUILD_HOUDINI_PLUGIN"] = False
        self._cmake.definitions["OPENVDB_BUILD_HOUDINI_ABITESTS"] = False
        self._cmake.definitions["OPENVDB_INSTALL_HOUDINI_PYTHONRC"] = False
        self._cmake.definitions["OPENVDB_BUILD_MAYA_PLUGIN"] = False
        self._cmake.definitions["OPENVDB_ENABLE_RPATH"] = True
        self._cmake.definitions["OPENVDB_CXX_STRICT"] = False
        self._cmake.definitions["OPENVDB_CODE_COVERAGE"] = False
        self._cmake.definitions["OPENVDB_INSTALL_CMAKE_MODULES"] = False
        self._cmake.definitions["USE_HOUDINI"] = False
        self._cmake.definitions["USE_MAYA"] = False
        self._cmake.definitions["USE_BLOSC"] = True
        self._cmake.definitions["USE_LOG4CPLUS"] = False
        self._cmake.definitions["USE_EXR"] = True
        self._cmake.definitions["OPENVDB_DISABLE_BOOST_IMPLICIT_LINKING"] = False
        self._cmake.definitions["USE_CCACHE"] = False
        self._cmake.definitions["USE_STATIC_DEPENDENCIES"] = False
        self._cmake.definitions["DISABLE_DEPENDENCY_VERSION_CHECKS"] = True
        self._cmake.definitions["DISABLE_CMAKE_SEARCH_PATHS"] = False
        self._cmake.definitions["OPENVDB_USE_DEPRECATED_ABI_5"] = False
        self._cmake.definitions["OPENVDB_FUTURE_DEPRECATION"] = False
        self._cmake.definitions["USE_COLORED_OUTPUT"] = False
        self._cmake.definitions["USE_PKGCONFIG"] = False
        self._cmake.definitions["OPENVDB_CORE_SHARED"] = False
        self._cmake.definitions["OPENVDB_CORE_STATIC"] = True
        self._cmake.definitions["CONCURRENT_MALLOC"] = "None"

        self._cmake.configure(build_folder=self._build_subfolder)
        return self._cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy("LICENSE.txt", src=self._source_subfolder, dst="licenses")
        cmake = self._configure_cmake()
        cmake.install()
        tools.rmdir(os.path.join(self.package_folder, "share"))
        tools.rmdir(os.path.join(self.package_folder, "lib", "pkgconfig"))
        tools.rmdir(os.path.join(self.package_folder, "lib", "cmake"))

        self.copy(pattern="*.dll", dst="bin", keep_path=False)
        self.copy(pattern="*.dylib", dst="lib", keep_path=False)
        self.copy(pattern="*.so*", dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.names["cmake_find_package"] = "OpenVDB"
        self.cpp_info.names["cmake_find_package_multi"] = "OpenVDB"
        self.cpp_info.names["pkg_config"] = "OpenVDB"

        self.cpp_info.libs = tools.collect_libs(self)
        if self.settings.os == "Windows":
            self.cpp_info.defines.append("NOMINMAX")

        self.cpp_info.defines.append("OPENVDB_TOOLS_RAYTRACER_USE_EXR")
        self.cpp_info.defines.append("OPENVDB_STATICLIB")
        self.cpp_info.defines.append("OPENVDB_OPENEXR_STATICLIB")





