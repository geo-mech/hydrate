#!/bin/bash

# 🔥 关键：强制切换到脚本所在的目录（解决路径问题）
cd "$(dirname "$0")" || exit 1

CXX=g++

CXXFLAGS=(
  -std=c++17
  -O3
  -DNDEBUG
  -fPIC
  -march=native
  -fopenmp
  #-Wall
  #-Wextra
)

INCLUDES=(
  -I ../../../../
  -I /usr/include/eigen3
)

LIBS=(
  -lboost_serialization
  -lboost_filesystem
  -lboost_thread
  -lboost_timer
  -lboost_system
)

OUTPUT=zml.so

$CXX "${CXXFLAGS[@]}" "${INCLUDES[@]}" \
     -shared ./zml.cpp \
     "${LIBS[@]}" \
     -o $OUTPUT
