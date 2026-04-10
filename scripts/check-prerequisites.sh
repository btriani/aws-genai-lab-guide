#!/usr/bin/env bash
set -uo pipefail

PASS=0
FAIL=0

check_cmd() {
    local name="$1"
    local cmd="$2"
    if command -v "$cmd" &>/dev/null; then
        printf "  %-25s [PASS]\n" "$name"
        ((PASS++))
    else
        printf "  %-25s [FAIL] not found\n" "$name"
        ((FAIL++))
    fi
}

check_python_version() {
    local required="3.10"
    local version
    version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
    if python3 -c "import sys; exit(0 if sys.version_info >= (3,10) else 1)" 2>/dev/null; then
        printf "  %-25s [PASS] %s\n" "Python >= $required" "$version"
        ((PASS++))
    else
        printf "  %-25s [FAIL] found %s\n" "Python >= $required" "$version"
        ((FAIL++))
    fi
}

check_python_pkg() {
    local pkg="$1"
    if python3 -c "import $pkg" 2>/dev/null; then
        printf "  %-25s [PASS]\n" "$pkg"
        ((PASS++))
    else
        printf "  %-25s [FAIL] not installed\n" "$pkg"
        ((FAIL++))
    fi
}

check_aws_auth() {
    if aws sts get-caller-identity &>/dev/null; then
        local account
        account=$(aws sts get-caller-identity --query Account --output text)
        printf "  %-25s [PASS] account %s\n" "AWS credentials" "$account"
        ((PASS++))
    else
        printf "  %-25s [FAIL] run 'aws configure'\n" "AWS credentials"
        ((FAIL++))
    fi
}

check_bedrock_access() {
    if aws bedrock list-foundation-models --region us-east-1 &>/dev/null; then
        printf "  %-25s [PASS]\n" "Bedrock access"
        ((PASS++))
    else
        printf "  %-25s [FAIL] enable model access in Bedrock console\n" "Bedrock access"
        ((FAIL++))
    fi
}

echo ""
echo "AWS GenAI Lab Guide — Prerequisites Check"
echo "==========================================="
echo ""

echo "Core tools:"
check_cmd "AWS CLI" "aws"
check_python_version
check_cmd "pip" "pip3"
check_cmd "Git" "git"

echo ""
echo "Python packages:"
check_python_pkg "boto3"
check_python_pkg "sagemaker"
check_python_pkg "opensearchpy"

echo ""
echo "AWS access:"
check_aws_auth
check_bedrock_access

echo ""
echo "Optional:"
check_cmd "GitHub CLI (gh)" "gh"

echo ""
echo "==========================================="
echo "Results: $PASS passed, $FAIL failed"
echo ""

if [ "$FAIL" -gt 0 ]; then
    echo "Fix the failing checks above before starting the labs."
    echo "See prerequisites.md for setup instructions."
fi

exit "$FAIL"
