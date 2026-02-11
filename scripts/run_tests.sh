#!/bin/bash

# Exit on error
set -e

IMAGE_NAME="commlib-py-testsuite"
TEST_TYPE=${1:-"unit"}

function print_help {
    echo "Usage: ./scripts/run_tests.sh [unit|package|integration|coverage|help]"
    echo ""
    echo "Commands:"
    echo "  unit         Run unit tests (default)"
    echo "  package      Validate package installation"
    echo "  integration  Run integration tests (packaging + unit)"
    echo "  coverage     Run unit tests with coverage"
    echo "  help         Show this help message"
}

if [ "$TEST_TYPE" == "help" ] || [ "$TEST_TYPE" == "--help" ]; then
    print_help
    exit 0
fi

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "Building Docker image for tests..."
docker build -t $IMAGE_NAME -f "$REPO_ROOT/Dockerfile.test" "$REPO_ROOT"

if [ "$TEST_TYPE" == "unit" ]; then
    echo "Running unit tests in Docker container..."
    docker run --rm $IMAGE_NAME
elif [ "$TEST_TYPE" == "package" ]; then
    echo "Running packaging + unit tests in Docker container..."
    docker run --rm --network host $IMAGE_NAME pytest tests --ignore=tests/mqtt --ignore=tests/redis --ignore=tests/kafka --ignore=tests/benchmarks -v
elif [ "$TEST_TYPE" == "coverage" ]; then
    echo "Running unit tests with coverage in Docker container..."
    docker run --rm $IMAGE_NAME bash -c "coverage run -m pytest --ignore=tests/mqtt --ignore=tests/redis --ignore=tests/kafka --ignore=tests/benchmarks && coverage report -m"
elif [ "$TEST_TYPE" == "integration" ]; then
    python "$(dirname "$0")/run_all_broker_tests.py"
else
    echo "Unknown test type: $TEST_TYPE"
    print_help
    exit 1
fi
