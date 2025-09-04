#!/bin/bash

# Medley Test Runner Script

set -e  # Exit on error

echo "================================"
echo "    Medley Test Suite"
echo "================================"
echo ""

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: No virtual environment detected"
    echo "   Consider activating a virtual environment first"
    echo ""
fi

# Install test dependencies if needed
echo "📦 Checking dependencies..."
pip install -q pytest pytest-cov pytest-asyncio

# Run different test suites based on argument
case "${1:-all}" in
    unit)
        echo "🧪 Running unit tests..."
        pytest tests/unit -v -m unit
        ;;
    integration)
        echo "🔗 Running integration tests..."
        pytest tests/integration -v -m integration
        ;;
    coverage)
        echo "📊 Running tests with coverage..."
        pytest --cov=src/medley --cov-report=term-missing --cov-report=html
        echo ""
        echo "📈 Coverage report generated at htmlcov/index.html"
        ;;
    quick)
        echo "⚡ Running quick tests (no coverage)..."
        pytest -x --tb=short
        ;;
    verbose)
        echo "📝 Running tests with verbose output..."
        pytest -vv
        ;;
    all)
        echo "🎯 Running all tests with coverage..."
        pytest --cov=src/medley --cov-report=term-missing
        ;;
    *)
        echo "Usage: $0 [unit|integration|coverage|quick|verbose|all]"
        echo ""
        echo "Options:"
        echo "  unit        - Run only unit tests"
        echo "  integration - Run only integration tests"
        echo "  coverage    - Run all tests with coverage report"
        echo "  quick       - Run tests quickly (stop on first failure)"
        echo "  verbose     - Run tests with verbose output"
        echo "  all         - Run all tests (default)"
        exit 1
        ;;
esac

echo ""
echo "✅ Test run complete!"