#!/bin/bash

echo "🔍 Checking Copilot Fix Progress..."
echo "================================"
echo ""

# Fetch latest from origin
echo "📡 Fetching latest branches..."
git fetch origin 2>/dev/null

echo ""
echo "🌿 Fix Branches Status:"
echo "----------------------"

# Check for expected fix branches
BRANCHES=("fix/security-eval-vulnerability" "fix/slip015-qt-improvements" "fix/test-improvements")
AGENTS=("TestRunner" "Developer" "Tester")

for i in ${!BRANCHES[@]}; do
    BRANCH=${BRANCHES[$i]}
    AGENT=${AGENTS[$i]}
    
    if git branch -r | grep -q "origin/$BRANCH"; then
        echo "✅ $AGENT: origin/$BRANCH EXISTS"
        # Get last commit info
        LAST_COMMIT=$(git log origin/$BRANCH -1 --oneline 2>/dev/null)
        echo "   Last commit: $LAST_COMMIT"
    else
        echo "⏳ $AGENT: origin/$BRANCH NOT FOUND YET"
    fi
    echo ""
done

# Check current time vs deadlines
CURRENT_TIME=$(date +%H:%M)
echo "⏰ Current Time: $CURRENT_TIME"
echo "📅 Deadlines:"
echo "   - Security Fix: 21:35 (TestRunner)"
echo "   - All Fixes: 23:05 (All agents)"
echo ""

# Check if eval() still exists
echo "🔍 Security Check - eval() usage:"
if grep -r "eval(" . --include="*.py" | grep -v "literal_eval" | grep -v "test_" | head -5; then
    echo "⚠️  WARNING: eval() still found in codebase!"
else
    echo "✅ No dangerous eval() usage found"
fi

echo ""
echo "📊 Summary:"
echo "-----------"
FOUND_COUNT=$(git branch -r | grep -c "origin/fix/")
echo "Fix branches found: $FOUND_COUNT / 3"

if [ "$FOUND_COUNT" -eq 3 ]; then
    echo "🎉 All fix branches are ready for integration!"
else
    echo "⏳ Waiting for $(( 3 - $FOUND_COUNT )) more fix branches..."
fi