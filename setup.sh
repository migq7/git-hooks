REPO_ROOT=$(git rev-parse --show-toplevel)

# check if this repo already has an pre-commit git hook
if [ -f "$REPO_ROOT/.git/hooks/pre-commit" ]; then
  echo "pre-commit hook already exists. Skipping..."
  exit 0
fi

# create a pre-commit hook
echo "#!/bin/bash" > "$REPO_ROOT/.git/hooks/pre-commit"
echo "bash git_hook/one-shot-script/format-changed-files.sh" >> "$REPO_ROOT/.git/hooks/pre-commit"
echo "bash git_hook/one-shot-script/add-header-to-changed-files.sh" >> "$REPO_ROOT/.git/hooks/pre-commit"
chmod +x "$REPO_ROOT/.git/hooks/pre-commit"

# check if there is a .fileheaderignore file
if [ -f "$REPO_ROOT/.fileheaderignore" ]; then
  echo ".fileheaderignore file already exists. Skipping..."
else
  # add .fileheaderignore file to git root
  echo "3rdparty" >> "$REPO_ROOT/.fileheaderignore"
  echo "build" >> "$REPO_ROOT/.fileheaderignore"
  echo "arith" >> "$REPO_ROOT/.fileheaderignore"
  echo "contrib" >> "$REPO_ROOT/.fileheaderignore"
  echo "driver" >> "$REPO_ROOT/.fileheaderignore"
  echo "ir" >> "$REPO_ROOT/.fileheaderignore"
  echo "node" >> "$REPO_ROOT/.fileheaderignore"
  echo "parser" >> "$REPO_ROOT/.fileheaderignore"
  echo "printer" >> "$REPO_ROOT/.fileheaderignore"
  echo "relay" >> "$REPO_ROOT/.fileheaderignore"
  echo "runtime" >> "$REPO_ROOT/.fileheaderignore"
  echo "support" >> "$REPO_ROOT/.fileheaderignore"
  echo "target" >> "$REPO_ROOT/.fileheaderignore"
  echo "te" >> "$REPO_ROOT/.fileheaderignore"
  echo "tir" >> "$REPO_ROOT/.fileheaderignore"
  echo "topi" >> "$REPO_ROOT/.fileheaderignore"
fi

# check if there is a .formatignore file
if [ -f "$REPO_ROOT/.formatignore" ]; then
  echo ".formatignore file already exists. Skipping..."
else
  # add .formatignore file to git root
  echo "3rdparty" >> "$REPO_ROOT/.formatignore"
  echo "build" >> "$REPO_ROOT/.formatignore"
  echo "arith" >> "$REPO_ROOT/.formatignore"
  echo "contrib" >> "$REPO_ROOT/.formatignore"
  echo "driver" >> "$REPO_ROOT/.formatignore"
  echo "ir" >> "$REPO_ROOT/.formatignore"
  echo "node" >> "$REPO_ROOT/.formatignore"
  echo "parser" >> "$REPO_ROOT/.formatignore"
  echo "printer" >> "$REPO_ROOT/.formatignore"
  echo "relay" >> "$REPO_ROOT/.formatignore"
  echo "runtime" >> "$REPO_ROOT/.formatignore"
  echo "support" >> "$REPO_ROOT/.formatignore"
  echo "target" >> "$REPO_ROOT/.formatignore"
  echo "te" >> "$REPO_ROOT/.formatignore"
  echo "tir" >> "$REPO_ROOT/.formatignore"
  echo "topi" >> "$REPO_ROOT/.formatignore"
fi

echo "pre-commit hook created successfully."
