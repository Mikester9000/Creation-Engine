# Makefile for the Creation Engine
#
# Usage:
#   make        - build the creation-engine binary
#   make clean  - remove build artifacts
#   make test   - build and run the test suite

CXX      := g++
CXXFLAGS := -std=c++17 -Wall -Wextra -O2 -Isrc -Ivendor
TARGET   := creation-engine
SRCDIR   := src

SRCS := $(wildcard $(SRCDIR)/*.cpp)
OBJS := $(SRCS:.cpp=.o)

.PHONY: all clean test

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CXX) $(CXXFLAGS) -o $@ $^ -lm
	@echo "Build successful: $(TARGET)"

$(SRCDIR)/%.o: $(SRCDIR)/%.cpp
	$(CXX) $(CXXFLAGS) -c -o $@ $<

clean:
	rm -f $(SRCDIR)/*.o $(TARGET)
	@echo "Cleaned."

test: $(TARGET)
	@bash tests/run_tests.sh
