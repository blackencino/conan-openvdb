from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import (
    copy,
    get,
    rm,
    patch,
    export_conandata_patches,
    apply_conandata_patches,
)
from conan.tools.microsoft import check_min_vs, is_msvc_static_runtime, is_msvc
from conan.tools.layout import basic_layout
from conan.tools.cmake import CMake, CMakeToolchain, CMakeDeps
from conan.tools.scm import Version
from conan.tools.build import check_min_cppstd
import os

required_conan_version = ">=1.53.0"


class OpenVDBConan(ConanFile):
    name = "openvdb"
    version = "10.0.1"
    description = (
        "OpenVDB is an open source C++ library comprising a novel hierarchical data"
        "structure and a large suite of tools for the efficient storage and "
        "manipulation of sparse volumetric data discretized on three-dimensional grids."
    )
    license = "MPL-2.0"
    topics = ("voxel", "voxelizer", "volume-rendering", "fx")
    homepage = "https://github.com/AcademySoftwareFoundation/openvdb"
    url = "https://github.com/conan-io/conan-center-index"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "nanovdb_use_cuda": [True, False],
        "with_blosc": [True, False],
        "with_zlib": [True, False],
        "with_log4cplus": [True, False],
        "with_exr": [True, False],
        "simd": [None, "SSE42", "AVX"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "nanovdb_use_cuda": True,
        "with_blosc": True,
        "with_zlib": True,
        "with_log4cplus": False,
        "with_exr": False,
        "simd": None,
    }

    @property
    def _min_cppstd(self):
        return 14

    @property
    def _compilers_minimum_version(self):
        return {
            "msvc": "191",
            "Visual Studio": "15",  # Should we check toolset?
            "gcc": "6.3.1",
            "clang": "3.8",
            "apple-clang": "3.8",
            "intel": "17",
        }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        basic_layout(self)

    def requirements(self):
        self.requires("boost/[>=1.80.0]")
        self.requires("onetbb/[>=2020.3]")
        self.requires("openexr/2.5.7")  # required for IlmBase::Half
        if self.options.with_zlib:
            self.requires("zlib/[>=1.2.12]")
        if self.options.with_blosc:
            self.requires("c-blosc/[>=1.21.1]")
        if self.options.with_log4cplus:
            self.requires("log4cplus/[>=2.0.7]")

    def validate(self):
        if self.info.settings.compiler.cppstd:
            check_min_cppstd(self, self._min_cppstd)
        if self.settings.arch not in ("x86", "x86_64"):
            if self.options.simd:
                raise ConanInvalidConfiguration(
                    "Only intel architectures support SSE4 or AVX."
                )
        check_min_vs(self, 191)
        if not is_msvc(self):
            minimum_version = self._compilers_minimum_version.get(
                str(self.info.settings.compiler), False
            )
            if (
                minimum_version
                and Version(self.info.settings.compiler.version) < minimum_version
            ):
                raise ConanInvalidConfiguration(
                    f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support."
                )

    def source(self):
        get(
            self,
            **self.conan_data["sources"][self.version],
            strip_root=True,
            destination=self.source_folder,
        )

    def _patch_sources(self):
        apply_conandata_patches(self)

        # Remove FindXXX files from OpenVDB. Let Conan do the job
        rm(self, "Find*", os.path.join(self.source_folder, "cmake"))

        with open(os.path.join(self.source_folder, "cmake/FindBlosc.cmake"), "w") as f:
            f.write(
                """find_package(c-blosc)
if(c-blosc_FOUND)
    add_library(blosc INTERFACE)
    target_link_libraries(blosc INTERFACE c-blosc::c-blosc)
    add_library(Blosc::blosc ALIAS blosc)
endif()
"""
            )
        with open(os.path.join(self.source_folder, "FindIlmBase.cmake"), "w") as f:
            f.write(
                """find_package(OpenEXR)
if(OpenEXR_FOUND)
  add_library(Half INTERFACE)
  add_library(IlmThread INTERFACE)
  add_library(Iex INTERFACE)
  add_library(Imath INTERFACE)
  add_library(IlmImf INTERFACE)
  target_link_libraries(Half INTERFACE OpenEXR::OpenEXR)
  target_link_libraries(IlmThread INTERFACE OpenEXR::OpenEXR)
  target_link_libraries(Iex INTERFACE OpenEXR::OpenEXR)
  target_link_libraries(Imath INTERFACE OpenEXR::OpenEXR)
  target_link_libraries(IlmImf INTERFACE OpenEXR::OpenEXR)
  add_library(IlmBase::Half ALIAS Half)
  add_library(IlmBase::IlmThread ALIAS IlmThread)
  add_library(IlmBase::Iex ALIAS Iex)
  add_library(IlmBase::Imath ALIAS Imath)
  add_library(OpenEXR::IlmImf ALIAS IlmImf)
 endif()
 """
            )

    def generate(self):
        toolchain = CMakeToolchain(self)
        # exposed options
        toolchain.variables["USE_BLOSC"] = self.options.with_blosc
        toolchain.variables["USE_ZLIB"] = self.options.with_zlib
        toolchain.variables["USE_LOG4CPLUS"] = self.options.with_log4cplus
        toolchain.variables["USE_EXR"] = self.options.with_exr
        toolchain.variables["OPENVDB_SIMD"] = self.options.simd

        toolchain.variables["OPENVDB_CORE_SHARED"] = self.options.shared
        toolchain.variables["OPENVDB_CORE_STATIC"] = not self.options.shared

        # All available options but not exposed yet. Set to default values
        toolchain.variables["OPENVDB_BUILD_CORE"] = True
        toolchain.variables["OPENVDB_BUILD_BINARIES"] = False
        toolchain.variables["OPENVDB_BUILD_PYTHON_MODULE"] = False
        toolchain.variables["OPENVDB_BUILD_UNITTESTS"] = False
        toolchain.variables["OPENVDB_BUILD_DOCS"] = False
        toolchain.variables["OPENVDB_BUILD_HOUDINI_PLUGIN"] = False
        toolchain.variables["OPENVDB_BUILD_HOUDINI_ABITESTS"] = False

        toolchain.variables["OPENVDB_BUILD_AX"] = False
        toolchain.variables["OPENVDB_BUILD_AX_UNITTESTS"] = False

        toolchain.variables["OPENVDB_BUILD_NANOVDB"] = True
        toolchain.variables["NANOVDB_USE_CUDA"] = self.options.nanovdb_use_cuda

        toolchain.variables["OPENVDB_BUILD_MAYA_PLUGIN"] = False
        toolchain.variables["OPENVDB_ENABLE_RPATH"] = False
        toolchain.variables["OPENVDB_CXX_STRICT"] = False
        toolchain.variables["USE_HOUDINI"] = False
        toolchain.variables["USE_MAYA"] = False
        toolchain.variables["USE_STATIC_DEPENDENCIES"] = False
        toolchain.variables["USE_PKGCONFIG"] = False
        toolchain.variables["OPENVDB_INSTALL_CMAKE_MODULES"] = False

        toolchain.variables["FUTURE_MINIMUM_TBB_VERSION"] = "2020.3"

        toolchain.variables["Boost_USE_STATIC_LIBS"] = not self.options["boost"].shared
        toolchain.variables["OPENEXR_USE_STATIC_LIBS"] = not self.options[
            "openexr"
        ].shared

        toolchain.variables["OPENVDB_DISABLE_BOOST_IMPLICIT_LINKING"] = True

        toolchain.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(
            self,
            "LICENSE",
            src=self.source_folder,
            dst=os.path.join(self.package_folder, "licenses"),
        )
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("cmake_find_mode", "both")
        self.cpp_info.set_property("cmake_file_name", "OpenVDB")
        self.cpp_info.set_property("cmake_target_name", "OpenVDB::openvdb")

        # TODO: back to global scope in conan v2 once cmake_find_package_* generators removed
        lib_prefix = "lib" if is_msvc(self) and not self.options.shared else ""
        self.cpp_info.components["openvdb-core"].libs = [lib_prefix + "openvdb"]

        lib_define = "OPENVDB_DLL" if self.options.shared else "OPENVDB_STATICLIB"
        self.cpp_info.components["openvdb-core"].defines.append(lib_define)

        if self.settings.os == "Windows":
            self.cpp_info.components["openvdb-core"].defines.append("_WIN32")
            self.cpp_info.components["openvdb-core"].defines.append("NOMINMAX")

        if not self.options["openexr"].shared:
            self.cpp_info.components["openvdb-core"].defines.append(
                "OPENVDB_OPENEXR_STATICLIB"
            )
        if self.options.with_exr:
            self.cpp_info.components["openvdb-core"].defines.append(
                "OPENVDB_TOOLS_RAYTRACER_USE_EXR"
            )
        if self.options.with_log4cplus:
            self.cpp_info.components["openvdb-core"].defines.append(
                "OPENVDB_USE_LOG4CPLUS"
            )

        self.cpp_info.components["openvdb-core"].requires = [
            "boost::iostreams",
            "boost::system",
            "onetbb::onetbb",
            "openexr::openexr",  # should be "openexr::Half",
        ]
        if self.settings.os == "Windows":
            self.cpp_info.components["openvdb-core"].requires.append(
                "boost::disable_autolinking"
            )

        if self.options.with_zlib:
            self.cpp_info.components["openvdb-core"].requires.append("zlib::zlib")
        if self.options.with_blosc:
            self.cpp_info.components["openvdb-core"].requires.append("c-blosc::c-blosc")
        if self.options.with_log4cplus:
            self.cpp_info.components["openvdb-core"].requires.append(
                "log4cplus::log4cplus"
            )

        if self.settings.os in ("Linux", "FreeBSD"):
            self.cpp_info.components["openvdb-core"].system_libs = ["pthread"]

        # TODO: to remove in conan v2 once cmake_find_package_* generators removed
        self.cpp_info.names["cmake_find_package"] = "OpenVDB"
        self.cpp_info.names["cmake_find_package_multi"] = "OpenVDB"
        self.cpp_info.components["openvdb-core"].names["cmake_find_package"] = "openvdb"
        self.cpp_info.components["openvdb-core"].names[
            "cmake_find_package_multi"
        ] = "openvdb"
        self.cpp_info.components["openvdb-core"].set_property(
            "cmake_target_name", "OpenVDB::openvdb"
        )
