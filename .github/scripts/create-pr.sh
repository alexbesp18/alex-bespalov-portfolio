#!/bin/bash
# create-pr.sh - Create a branch, commit changes, and open a pull request
#
# Usage: 
#   ./create-pr.sh "feature-name" "commit message"
#   ./create-pr.sh "fix-alerts" "Fix alert threshold calculation"
#
# This script:
#   1. Creates a new branch from main
#   2. Stages all changes
#   3. Commits with your message
#   4. Pushes the branch
#   5. Opens a PR on GitHub

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Ensure GH_CONFIG_DIR is set (for this machine's gh setup)
export GH_CONFIG_DIR=~/Library/Application\ Support/gh

# Check arguments
if [ -z "$1" ] || [ -z "$2" ]; then
    echo -e "${RED}Usage: $0 \"branch-name\" \"commit message\"${NC}"
    echo ""
    echo "Examples:"
    echo "  $0 \"fix-alerts\" \"Fix alert threshold calculation\""
    echo "  $0 \"add-feature\" \"Add new oversold indicator\""
    exit 1
fi

BRANCH_NAME="$1"
COMMIT_MSG="$2"

# Check if we're in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}Error: Not in a git repository${NC}"
    exit 1
fi

# Check if gh is authenticated
if ! gh auth status > /dev/null 2>&1; then
    echo -e "${RED}Error: GitHub CLI not authenticated. Run: gh auth login${NC}"
    exit 1
fi

# Check for uncommitted changes
if [ -z "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}No changes to commit. Make some changes first!${NC}"
    exit 0
fi

echo -e "${GREEN}Creating PR for: ${BRANCH_NAME}${NC}"
echo ""

# Make sure we're on main and up to date
echo "→ Switching to main and pulling latest..."
git checkout main 2>/dev/null || git checkout master 2>/dev/null
git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || true

# Create new branch
echo "→ Creating branch: ${BRANCH_NAME}"
git checkout -b "$BRANCH_NAME"

# Stage all changes
echo "→ Staging changes..."
git add -A

# Commit
echo "→ Committing: ${COMMIT_MSG}"
git commit -m "$COMMIT_MSG"

# Push branch
echo "→ Pushing branch to origin..."
git push -u origin "$BRANCH_NAME"

# Create PR
echo "→ Creating pull request..."
PR_URL=$(gh pr create --title "$COMMIT_MSG" --body "Created via create-pr.sh" --head "$BRANCH_NAME" --base main 2>&1)

echo ""
echo -e "${GREEN}✓ Pull request created!${NC}"
echo -e "${GREEN}  ${PR_URL}${NC}"
echo ""
echo "Next steps:"
echo "  1. Review the PR on GitHub"
echo "  2. Merge when ready"
echo "  3. Run: git checkout main && git pull"

