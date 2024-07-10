REPO_ROOT=$(git rev-parse --show-toplevel)

# check if this repo already has an pre-commit git hook
if [ -f "$REPO_ROOT/.git/hooks/pre-commit" ]; then
  echo "pre-commit hook already exists. Skipping..."
  exit 0
fi

# create a pre-commit hook
echo "#!/bin/bash" > "$REPO_ROOT/.git/hooks/pre-commit"
echo "bash git-hooks/one-shot-script/format-changed-files.sh" >> "$REPO_ROOT/.git/hooks/pre-commit"
echo "bash git-hooks/one-shot-script/add-header-to-changed-files.sh" >> "$REPO_ROOT/.git/hooks/pre-commit"
chmod +x "$REPO_ROOT/.git/hooks/pre-commit"

echo "pre-commit hook created successfully."