# Workaround for build system flaws
%undefine _debugsource_packages

%define __builder ninja
%ifarch %{x86_64}
%define use_clang 1
%else
%define use_clang 0
%endif
%global _lto_cflags %nil
%global _lto_ldlags %nil
%define so_ver 3_7
%define real_version 1.7.2207

Name:          DirectXShaderCompiler
Version:       1.7.2207
Release:       1
Summary:       DirectX Shader Compiler
License:       Apache-2.0 WITH LLVM-exception OR NCSA
Group:         Development/Graphics
URL:           https://github.com/microsoft/DirectXShaderCompiler/
Source0:       https://github.com/microsoft/DirectXShaderCompiler/archive/refs/tags/v%{version}/%{name}-%{version}.tar.gz
# dxc build process relies on the presence of spirv-headers source including
# cmake files, for now just pointing it at the system copy the way it should
# be doesn't work
Source1:	https://github.com/KhronosGroup/SPIRV-Headers/archive/0bcc624926a25a2a273d07877fd25a6ff5ba1cfb.tar.gz
Source2:	https://github.com/KhronosGroup/SPIRV-Tools/archive/71b2aee6c868a673ec82d1385f97593aa2881316.tar.gz
Source3:	https://github.com/google/effcee/archive/35912e1b7778ec2ddcff7e7188177761539e59e0.tar.gz
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

%description
The DirectX Shader Compiler project includes a compiler and related tools used to compile
High-Level Shader Language (HLSL) programs into DirectX Intermediate Language (DXIL) representation.
Applications that make use of DirectX for graphics, games, and computation can use it to generate shader programs.

%package libdxcompiler%{so_ver}
Summary:  DirectX Shader Compiler library
Group:    Development/Graphics
Provides: libdxcompiler = %{version}
Provides: dxc-libdxcompiler = %{version}-%{release}

%description libdxcompiler%{so_ver}
DirectX Shader Compiler standalone dynamic library

%package libdxcompiler-devel
Summary:  DirectX Shader Compiler library development files
Group:    Development/Graphics
Requires: %{name}-libdxcompiler%{so_ver}
Provides: dxc-libdxcompiler-devel = %{version}-%{release}

%description libdxcompiler-devel
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
rmdir effcee
tar xf %{S:3}
mv effcee-* effcee
cd ..

# clean out hardcoding
%if 0%{?use_clang}
sed -i -e 's/ -fno-exceptions//g' -e 's/ -fno-rtti//g' -e '/add_compile_options(-fno-rtti)/d' \
        external/SPIRV-Tools/CMakeLists.txt \
        external/effcee/cmake/setup_build.cmake
sed -i -e '/"-Werror",/d' -e '/"-fno-exceptions",/d' -e '/"-fno-rtti",/d' \
        external/SPIRV-Tools/build_defs.bzl
sed -i -e '/CmdArgs.push_back("-fno-exceptions");/d' -e '/CmdArgs.push_back("-fno-rtti");/d' -e '/CmdArgs.push_back("-fno-rtti-data");/d' \
        tools/clang/lib/Driver/Tools.cpp
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
# fix correct lib folder
%ifarch %{x86_64}
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
%{_bindir}/dxc*

%files libdxcompiler%{so_ver}
%{_libdir}/libdxcompiler.so.*

%files libdxcompiler-devel
%{_includedir}/dxc
%{_libdir}/libdxcompiler.so
%{_libdir}/libdxclib.a
