cmake_policy(SET CMP0048 NEW)
project(
  ${SKBUILD_PROJECT_NAME}
  VERSION ${SKBUILD_PROJECT_VERSION}
  LANGUAGES CXX)

cmake_minimum_required(VERSION 3.15...3.27)

option(BUILD_PYTHON_BINDING "Build Python Binding" on)


set(CMAKE_POSITION_INDEPENDENT_CODE ON)

set(CMAKE_CXX_STANDARD 17)

# Detect architecture
if(CMAKE_SYSTEM_PROCESSOR MATCHES "aarch64")
    set(ARCH_DIR "aarch64")
else()
    set(ARCH_DIR "x86_64")
endif()

# Set library paths
set(BOOSTER_LIB_DIR ${PROJECT_SOURCE_DIR}/lib/${ARCH_DIR})
set(THIRD_PARTY_LIB_DIR ${PROJECT_SOURCE_DIR}/third_party/lib/${ARCH_DIR})

# Set exact library paths
set(BOOSTER_SDK_LIB ${BOOSTER_LIB_DIR}/libbooster_robotics_sdk.a)
set(FASTRTPS_LIB ${THIRD_PARTY_LIB_DIR}/libfastrtps.so)
set(FASTCDR_LIB ${THIRD_PARTY_LIB_DIR}/libfastcdr.so)
set(FOONATHAN_LIB ${THIRD_PARTY_LIB_DIR}/libfoonathan_memory-0.7.3.a)

# System dependencies for FastRTPS
find_library(TINYXML2_LIB tinyxml2 PATHS /usr/lib/x86_64-linux-gnu NO_DEFAULT_PATH)
find_library(SSL_LIB ssl PATHS /usr/lib/x86_64-linux-gnu NO_DEFAULT_PATH)
find_library(CRYPTO_LIB crypto PATHS /usr/lib/x86_64-linux-gnu NO_DEFAULT_PATH)

# Libraries will be linked per target

add_executable(b1_loco_example_client example/high_level/b1_loco_example_client.cpp)
add_executable(b1_arm_sdk_example_client example/high_level/b1_arm_sdk_example.cpp)
add_executable(b1_7dof_arm_sdk_example_client example/high_level/b1_7dof_arm_sdk_example.cpp)
add_executable(b1_low_level_publisher example/low_level/low_level_publisher.cpp)
add_executable(b1_low_level_subscriber example/low_level/low_level_subscriber.cpp)
add_executable(low_level_hand_data_subscriber example/low_level/low_level_hand_data_subscriber.cpp)
add_executable(b1_low_sdk_example example/low_level/b1_low_sdk_example.cpp)
add_executable(b1_7dof_arm_low_sdk_example example/low_level/b1_7dof_arm_low_sdk_example.cpp)
add_executable(odometer_example example/low_level/odometer_example.cpp)

# Link libraries to all executables
foreach(target b1_loco_example_client b1_arm_sdk_example_client b1_7dof_arm_sdk_example_client
              b1_low_level_publisher b1_low_level_subscriber low_level_hand_data_subscriber
              b1_low_sdk_example b1_7dof_arm_low_sdk_example odometer_example)
    target_link_libraries(${target} PRIVATE
        ${BOOSTER_SDK_LIB}
        ${FASTRTPS_LIB}
        ${FASTCDR_LIB}
        ${FOONATHAN_LIB}
        ${TINYXML2_LIB}
        ${SSL_LIB}
        ${CRYPTO_LIB}
    )
endforeach()


include_directories(BEFORE ${PROJECT_SOURCE_DIR}/include)

if(BUILD_PYTHON_BINDING)
    find_package(Python3 REQUIRED COMPONENTS Interpreter Development.Module)
    message(STATUS "Python3 executable: ${Python3_EXECUTABLE}")

    execute_process(
        COMMAND ${Python3_EXECUTABLE} -c "import sysconfig; print(sysconfig.get_paths()['purelib'])"
        OUTPUT_VARIABLE PYTHON_SITE_PACKAGES
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )

    include_directories(${Python3_INCLUDE_DIRS})
    execute_process(
        COMMAND ${Python3_EXECUTABLE} -m pybind11 --includes
        OUTPUT_VARIABLE PYBIND11_INCLUDES
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )
    string(REPLACE "-I" "" PYBIND11_INCLUDES "${PYBIND11_INCLUDES}")
    string(REPLACE " " ";" PYBIND11_INCLUDE_DIRS "${PYBIND11_INCLUDES}")
    include_directories(${PYBIND11_INCLUDE_DIRS})
    find_package(pybind11 CONFIG REQUIRED)

    python3_add_library(booster_robotics_sdk_python MODULE python/binding.cpp WITH_SOABI)

    target_compile_definitions(booster_robotics_sdk_python PRIVATE VERSION_INFO=${PROJECT_VERSION})

    # Link specific libraries to the Python module
    target_link_libraries(booster_robotics_sdk_python PRIVATE
        ${BOOSTER_SDK_LIB}
        ${FASTRTPS_LIB}
        ${FASTCDR_LIB}
        ${FOONATHAN_LIB}
        ${TINYXML2_LIB}
        ${SSL_LIB}
        ${CRYPTO_LIB}
    )

    # Set RPATH to find bundled libraries and system libs for libstdc++
    set_target_properties(booster_robotics_sdk_python PROPERTIES
        BUILD_RPATH "${THIRD_PARTY_LIB_DIR}:/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu"
        INSTALL_RPATH "${THIRD_PARTY_LIB_DIR}:/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu"
    )

    install(TARGETS booster_robotics_sdk_python LIBRARY DESTINATION ${PYTHON_SITE_PACKAGES})    
endif()

