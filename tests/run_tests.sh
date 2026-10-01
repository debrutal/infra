#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Activate virtualenv binaries
export PATH="$PROJECT_DIR/.venv/bin:$PATH"

MODE="${1:-fast}"

echo "================================================================="
echo " 1. Static Analysis (yamllint, ansible-lint, syntax-check)"
echo "================================================================="
yamllint "$PROJECT_DIR"
ansible-lint "$PROJECT_DIR"
ansible-playbook "$PROJECT_DIR/site.yml" --syntax-check

cd "$PROJECT_DIR"

if [ "$MODE" = "--full" ] || [ "$MODE" = "full" ]; then
  echo ""
  echo "================================================================="
  echo " 2 & 3. Full Molecule Integration Lifecycle (Destructive + Idempotence + Verify)"
  echo "================================================================="
  molecule test

  echo ""
  echo "================================================================="
  echo " Standalone Integration Test Suite"
  echo "================================================================="
  python3 "$SCRIPT_DIR/test_deployment.py"
else
  echo ""
  echo "================================================================="
  echo " 2 & 3. Fast Molecule Converge & Verify (Persistent Instance)"
  echo "================================================================="
  molecule converge
  molecule verify
fi

echo ""
echo "================================================================="
echo " Deploy Script Test Suite"
echo "================================================================="
python3 "$SCRIPT_DIR/test_deploy_script.py"

echo ""
echo "================================================================="
echo " Container Log Script Test Suite"
echo "================================================================="
python3 "$SCRIPT_DIR/test_show_container_logs.py"

echo ""
echo "================================================================="
echo " User Credentials Test Suite"
echo "================================================================="
python3 "$SCRIPT_DIR/test_user_credentials.py"

echo ""
echo "All testing tasks completed successfully!"
