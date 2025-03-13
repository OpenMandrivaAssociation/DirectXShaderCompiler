# Workaround for build system flaws
%undefine _debugsource_packages

%define use_clang 1
%define so_ver 3_7
%define libdxcompiler %{mklibname dxcompiler}
%define devdxcompiler %{mklibname -d dxcompiler}

Name:          DirectXShaderCompiler
Version:       1.8.2502
Release:       2
Summary:       DirectX Shader Compiler
License:       Apache-2.0 WITH LLVM-exception OR NCSA
Group:         Development/Graphics
URL:           https://github.com/microsoft/DirectXShaderCompiler/
Source0:       https://github.com/microsoft/DirectXShaderCompiler/archive/refs/tags/v%{version}/%{name}-%{version}.tar.gz
# dxc build process relies on the presence of spirv-headers source including
# cmake files, for now just pointing it at the system copy the way it should
# be doesn't work
# Expected git commit IDs can be seen at https://github.com/microsoft/DirectXShaderCompiler/tree/main/external
Source1:	https://github.com/KhronosGroup/SPIRV-Headers/archive/54a521dd130ae1b2f38fef79b09515702d135bdd.tar.gz
Source2:	https://github.com/KhronosGroup/SPIRV-Tools/archive/f289d047f49fb60488301ec62bafab85573668cc.tar.gz
Source3:	https://github.com/microsoft/DirectX-Headers/archive/980971e835876dc0cde415e8f9bc646e64667bf7.tar.gz
%if 0%{?use_clang}
BuildRequires: clang-devel
BuildRequires: lld
%else
BuildRequires: gcc-c++
%endif
BuildRequires: cmake
BuildRequires: ninja
BuildRequires: llvm-devel
BuildRequires: ninja
BuildRequires: libxml2-devel
BuildRequires: ocaml
BuildRequires: git
BuildRequires: xz
Provides:      directxshadercompiler = %{version}-%{release}
Provides:      dxc = %{version}-%{release}

%patchlist
dxsc-soversion.patch

%description
The DirectX Shader Compiler project includes a compiler and related tools used to compile
High-Level Shader Language (HLSL) programs into DirectX Intermediate Language (DXIL) representation.
Applications that make use of DirectX for graphics, games, and computation can use it to generate shader programs.

%package -n %{libdxcompiler}
Summary:  DirectX Shader Compiler library
Group:    Development/Graphics
Provides: libdxcompiler = %{version}
Provides: dxc-libdxcompiler = %{version}-%{release}
%rename %{name}-libdxcompiler%{so_ver}

%description -n %{libdxcompiler}
DirectX Shader Compiler standalone dynamic library

%package -n %{devdxcompiler}
Summary:  DirectX Shader Compiler library development files
Group:    Development/Graphics
Requires: %{name}-libdxcompiler%{so_ver}
Provides: dxc-libdxcompiler-devel = %{version}-%{release}
%rename %{name}-libdxcompiler-devel

%description -n %{devdxcompiler}
DirectX Shader Compiler standalone dynamic library

%prep
%autosetup -p1

cd external
rmdir SPIRV-Headers
tar xf %{S:1}
mv SPIRV-Headers-* SPIRV-Headers
rmdir SPIRV-Tools
tar xf %{S:2}
mv SPIRV-Tools-* SPIRV-Tools
rmdir DirectX-Headers
tar xf %{S:3}
mv DirectX-Headers-* DirectX-Headers
cd ..

# clean out hardcoding
%if 0%{?use_clang:1}
#sed -i -e 's/ -fno-exceptions//g' -e 's/ -fno-rtti//g' -e '/add_compile_options(-fno-rtti)/d' \
#        external/SPIRV-Tools/CMakeLists.txt \
#        external/effcee/cmake/setup_build.cmake
#sed -i -e '/"-Werror",/d' -e '/"-fno-exceptions",/d' -e '/"-fno-rtti",/d' \
#        external/SPIRV-Tools/build_defs.bzl
#sed -i -e '/CmdArgs.push_back("-fno-exceptions");/d' -e '/CmdArgs.push_back("-fno-rtti");/d' -e '/CmdArgs.push_back("-fno-rtti-data");/d' \
#        tools/clang/lib/Driver/Tools.cpp
sed -i -e '/list(APPEND LLVM_COMPILE_FLAGS "-fno-exceptions")/d' \
    -e '/list(APPEND LLVM_COMPILE_FLAGS "-fno-rtti")/d' \
    -e '/set(LLVM_REQUIRES_RTTI OFF)/d' \
        cmake/modules/AddLLVM.cmake
%endif

%build
ulimit -Sn 4000
# -w -v ?
export CFLAGS="-w -O2 -pipe"
%if 0%{?use_clang}
export CFLAGS="${CFLAGS} -fexceptions"
#export CFLAGS="${CFLAGS} -march=x86-64-v2 -mtune=generic -mavx -maes -mpclmul"
%endif
%if 0%{?use_clang}
export CC=clang
export CXX=clang++
export LD="lld"
alias ld=ld.lld
export CFLAGS="${CFLAGS} -flto=thin -relocatable-pch"
export CXXFLAGS="${CFLAGS} -fpermissive"
%if 0%{?use_clang}
export CXXFLAGS="${CXXFLAGS} -fcxx-exceptions"
%endif
export LDFLAGS="-Wl,-O2 -fuse-ld=lld -flto=thin -Wl,--icf=safe -Wl,--plugin-opt=O3"
%else
# any gcc/ld-specific options ?
export CFLAGS="${CFLAGS} -ffat-lto-objects"
export CXXFLAGS="${CFLAGS} -fpermissive"
# there are slow gcc-specific LTO options in LDFLAGS by default
#export LDFLAGS="${LDFLAGS} -fPIC -Wl,-O1"
export LDFLAGS="-Wl,-O1 -Wl,--gc-sections"
%endif
#    -DCMAKE_CXX_FLAGS='-Wno-error=restrict -Wno-error=stringop-overflow='
#    -DLLVM_USE_INTEL_JITEVENTS=ON \
#    -DLLVM_USE_OPROFILE=ON
#    -DCMAKE_BUILD_TYPE=MinSizeRel
#    -DHLSL_OPTIONAL_PROJS_IN_DEFAULT=ON \
#    -DLLVM_OPTIMIZED_TABLEGEN=ON \
#    -DLLVM_ENABLE_ASSERTIONS=ON \
#    -DENABLE_EXCEPTIONS=ON \
# see https://github.com/microsoft/DirectXShaderCompiler/issues/4480 for ass-backwards workarounds from cmake/caches/PredefinedParams.cmake
mkdir build
cd build
cmake .. \
    -G Ninja \
%if 0%{?use_clang}
    -DCMAKE_C_COMPILER="${CC}" \
    -DCMAKE_CXX_COMPILER="${CXX}" \
    -DCMAKE_LINKER="${LD}" \
%endif
    -DCMAKE_C_FLAGS="${CFLAGS}" \
    -DCMAKE_CXX_FLAGS="${CXXFLAGS}" \
    -DCMAKE_EXE_LINKER_FLAGS="${LDLAGS}" \
    -DCMAKE_MODULE_LINKER_FLAGS="${LDLAGS}" \
    -DCMAKE_SHARED_LINKER_FLAGS="${LDLAGS}" \
    -DCMAKE_INSTALL_PREFIX="%{_prefix}" \
    -DCMAKE_INSTALL_LIBEXEC="%{_libexecdir}" \
    -DCMAKE_SKIP_RPATH=OFF \
    -DCMAKE_INSTALL_RPATH="" \
    -DCMAKE_BUILD_WITH_INSTALL_RPATH=OFF \
    -DCMAKE_SKIP_INSTALL_RPATH=ON \
    -DUSE_PCH=OFF -DENABLE_PCH=OFF \
    -DENABLE_PRECOMPILED_HEADERS=OFF \
    -DSKIP_PRECOMPILE_HEADERS=ON \
    -DUSE_PRECOMPILED_HEADERS=OFF \
    -C ../cmake/caches/PredefinedParams.cmake \
    -DHLSL_OFFICIAL_BUILD=ON \
    -DHLSL_OPTIONAL_PROJS_IN_DEFAULT=OFF \
    -DLLVM_USE_FOLDERS=OFF \
    -DLLVM_INSTALL_UTILS=OFF \
    -DLLVM_INSTALL_TOOLCHAIN_ONLY=ON \
%if 0%{?use_clang}
    -DLLVM_OPTIMIZED_TABLEGEN=ON \
    -DLLVM_ENABLE_ASSERTIONS=ON \
    -DLLVM_ENABLE_EXCEPTIONS=ON \
    -DENABLE_EXCEPTIONS=ON \
%endif
    -DBUILD_SHARED_LIBS=OFF \
    -DBUILD_STATIC_LIBS=ON \
    -DHLSL_INCLUDE_TESTS=OFF \
    -DSPIRV_BUILD_TESTS=OFF \
    -DLLVM_USE_INTEL_JITEVENTS=ON

%ninja_build

%install
%ninja_install -C build

mkdir -p %{buildroot}%{_includedir} || echo "whatever"
if [ ! -d "%{buildroot}%{_includedir}/dxc" ]; then
    mv -v build/include/dxc %{buildroot}%{_includedir}/
fi
mkdir -p %{buildroot}/%{_libdir} || echo "whatever"
if [ ! -f "%{buildroot}/%{_libdir}/libdxcompiler.so" ]; then
    mv -v build/lib*/libdxc* %{buildroot}/%{_libdir}/
fi
%if "%{_lib}" == "lib64"
# fix correct lib folder
if [ -d "%{buildroot}/%{_exec_prefix}/lib" ]; then
    mkdir -p %{buildroot}/%{_libdir} || echo "whatever"
    mv -v %{buildroot}/%{_exec_prefix}/lib/* %{buildroot}/%{_libdir}/
    rmdir %{buildroot}/%{_exec_prefix}/lib || echo "whatever"
fi
%endif
# Remove static libraries, don't think they are needed at all
#rm %{buildroot}/%{_libdir}/*.a

# Libclang and friends of this fork are harmful, use "real"
# libclang
rm -rf	%{buildroot}%{_includedir}/clang-c \
	%{buildroot}%{_libdir}/libclang.a

%files
%doc README.md
%license LICENSE.TXT
%{_bindir}/dxa*
%{_bindir}/dxc*
%{_bindir}/dxl*
%{_bindir}/dxopt*
%{_bindir}/dxr*
%{_bindir}/dxv*

%files -n %{libdxcompiler}
%{_libdir}/libdxcompiler.so*

%files -n %{devdxcompiler}
%{_includedir}/dxc
%{_libdir}/libdxclib.a
%{_libdir}/libdxcvalidator.a
