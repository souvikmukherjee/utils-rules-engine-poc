---
name: run-code
description: Execute code in various languages and frameworks efficiently. Use when you need to run, test, or validate code across different programming environments (Python, Node.js, Java, Go, Rust, etc.), set up runtime environments, manage dependencies, or verify code execution.
environments: [cloud, ide]
---

# Running Code Effectively

Use this skill to run code across different languages, frameworks, and environments. This guide covers best practices for execution, dependency management, environment setup, and verification workflows.

## Quick Reference

| Language/Framework | Basic Execution | With Dependencies | Development Server |
| --- | --- | --- | --- |
| **Python** | `python script.py` | `pip install -r requirements.txt && python script.py` | `python -m http.server 8000` |
| **Node.js** | `node script.js` | `npm install && node script.js` | `npm run dev` or `npm start` |
| **TypeScript** | `npx tsx script.ts` | `npm install && npx tsx script.ts` | `npm run dev` |
| **Java** | `javac Main.java && java Main` | `mvn compile && mvn exec:java` or `gradle run` | `mvn spring-boot:run` |
| **Go** | `go run main.go` | `go mod download && go run main.go` | `go run .` |
| **Rust** | `rustc main.rs && ./main` | `cargo run` | `cargo run --release` |
| **Ruby** | `ruby script.rb` | `bundle install && ruby script.rb` | `rails server` |
| **PHP** | `php script.php` | `composer install && php script.php` | `php -S localhost:8000` |

## Core Principles

1. **Read Before Running**: Always read the code or configuration files to understand what will execute.
2. **Check Dependencies**: Verify dependency files (package.json, requirements.txt, go.mod) exist before installing.
3. **Use tmux for Long-Running Processes**: Servers, watchers, and daemons should run in tmux sessions.
4. **Verify Output**: Check exit codes and examine output for errors.
5. **Clean Environment**: Ensure previous processes are stopped before starting new ones.

## Setting Up Environments from Zero

This section covers installing language runtimes and tools from scratch on a clean system.

### Version Management Philosophy

**Default Approach**: Use the system-provided or recommended stable versions unless the project explicitly requires specific versions.

**When to Upgrade**:
- Project has `.nvmrc`, `.python-version`, `go.mod`, or other version-specification files
- README or documentation specifies version requirements
- Current system version is EOL (end-of-life) or has security issues
- Build/runtime errors specifically indicate version incompatibility

**When NOT to Upgrade**:
- Code runs successfully with current versions
- Project doesn't specify version requirements
- System versions are recent and maintained

### Python Setup from Zero

**Check if installed:**
```bash
python3 --version || echo "Python not installed"
pip3 --version || echo "pip not installed"
```

**Install Python (Ubuntu/Debian):**
```bash
# Update package list
sudo apt update

# Install Python 3
sudo apt install -y python3 python3-pip python3-venv

# Verify installation
python3 --version
pip3 --version
```

**Install specific version with deadsnakes PPA (Ubuntu):**
```bash
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev
python3.11 --version
```

**Install pyenv (version manager):**
```bash
curl https://pyenv.run | bash

# Add to ~/.bashrc
cat >> ~/.bashrc << 'EOF'
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
EOF

source ~/.bashrc

# Install specific version
pyenv install 3.11.5
pyenv global 3.11.5
```

### Node.js Setup from Zero

**Check if installed:**
```bash
node --version || echo "Node not installed"
npm --version || echo "npm not installed"
```

**Install Node.js (Ubuntu/Debian - via NodeSource):**
```bash
# Install Node.js 20.x LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Verify installation
node --version
npm --version
```

**Install nvm (Node Version Manager - recommended):**
```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash

# Load nvm (or restart terminal)
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Install Node.js LTS
nvm install --lts
nvm use --lts

# Or install specific version
nvm install 20.10.0
nvm use 20.10.0

# Set default
nvm alias default 20.10.0
```

**Install pnpm (fast package manager):**
```bash
npm install -g pnpm
# or
curl -fsSL https://get.pnpm.io/install.sh | sh -

pnpm --version
```

**Install yarn:**
```bash
npm install -g yarn
# or via corepack
corepack enable
corepack prepare yarn@stable --activate
```

### Go Setup from Zero

**Check if installed:**
```bash
go version || echo "Go not installed"
```

**Install Go (Ubuntu/Debian):**
```bash
# Download latest Go (check https://go.dev/dl/ for current version)
GO_VERSION=1.21.5
wget https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz

# Remove old installation and extract
sudo rm -rf /usr/local/go
sudo tar -C /usr/local -xzf go${GO_VERSION}.linux-amd64.tar.gz

# Add to PATH
cat >> ~/.bashrc << 'EOF'
export PATH=$PATH:/usr/local/go/bin
export GOPATH=$HOME/go
export PATH=$PATH:$GOPATH/bin
EOF

source ~/.bashrc

# Verify
go version
```

### Java Setup from Zero

**Check if installed:**
```bash
java -version || echo "Java not installed"
javac -version || echo "javac not installed"
```

**Install Java (Ubuntu/Debian):**
```bash
# OpenJDK 17 (LTS)
sudo apt update
sudo apt install -y openjdk-17-jdk openjdk-17-jre

# Verify
java -version
javac -version

# Set JAVA_HOME
cat >> ~/.bashrc << 'EOF'
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH=$PATH:$JAVA_HOME/bin
EOF

source ~/.bashrc
```

**Install Maven:**
```bash
sudo apt update
sudo apt install -y maven
mvn --version
```

**Install Gradle:**
```bash
# Via SDKMAN (recommended)
curl -s "https://get.sdkman.io" | bash
source "$HOME/.sdkman/bin/sdkman-init.sh"
sdk install gradle
gradle --version

# Or via apt
sudo apt install -y gradle
```

### Rust Setup from Zero

**Check if installed:**
```bash
rustc --version || echo "Rust not installed"
cargo --version || echo "Cargo not installed"
```

**Install Rust (rustup - recommended):**
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Follow prompts, then reload shell
source $HOME/.cargo/env

# Verify
rustc --version
cargo --version

# Update Rust
rustup update
```

### Ruby Setup from Zero

**Check if installed:**
```bash
ruby --version || echo "Ruby not installed"
gem --version || echo "gem not installed"
```

**Install Ruby (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install -y ruby-full
ruby --version
```

**Install rbenv (version manager - recommended):**
```bash
# Install dependencies
sudo apt update
sudo apt install -y git curl libssl-dev libreadline-dev zlib1g-dev \
  autoconf bison build-essential libyaml-dev libreadline-dev \
  libncurses5-dev libffi-dev libgdbm-dev

# Install rbenv
curl -fsSL https://github.com/rbenv/rbenv-installer/raw/HEAD/bin/rbenv-installer | bash

# Add to PATH
cat >> ~/.bashrc << 'EOF'
export PATH="$HOME/.rbenv/bin:$PATH"
eval "$(rbenv init -)"
EOF

source ~/.bashrc

# Install Ruby version
rbenv install 3.2.2
rbenv global 3.2.2
ruby --version
```

**Install Bundler:**
```bash
gem install bundler
bundle --version
```

### PHP Setup from Zero

**Check if installed:**
```bash
php --version || echo "PHP not installed"
composer --version || echo "Composer not installed"
```

**Install PHP (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install -y php php-cli php-fpm php-json php-mbstring \
  php-xml php-curl php-zip php-gd

php --version
```

**Install Composer:**
```bash
curl -sS https://getcomposer.org/installer | php
sudo mv composer.phar /usr/local/bin/composer
sudo chmod +x /usr/local/bin/composer
composer --version
```

### Database Setup from Zero

**PostgreSQL:**
```bash
sudo apt update
sudo apt install -y postgresql postgresql-contrib

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create user and database
sudo -u postgres createuser --interactive
sudo -u postgres createdb mydb
```

**MySQL:**
```bash
sudo apt update
sudo apt install -y mysql-server

# Start service
sudo systemctl start mysql
sudo systemctl enable mysql

# Secure installation
sudo mysql_secure_installation
```

**Redis:**
```bash
sudo apt update
sudo apt install -y redis-server

# Start service
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Test
redis-cli ping
```

**MongoDB:**
```bash
# Import public key
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
  sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor

# Add repository
echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | \
  sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

sudo apt update
sudo apt install -y mongodb-org

# Start service
sudo systemctl start mongod
sudo systemctl enable mongod
```

### Docker Setup from Zero

**Install Docker:**
```bash
# Update package index
sudo apt update

# Install dependencies
sudo apt install -y ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER

# Verify installation
sudo docker --version
sudo docker compose version
```

### Essential Build Tools

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y build-essential git curl wget \
  ca-certificates gnupg lsb-release software-properties-common \
  pkg-config libssl-dev
```

**Check what's installed:**
```bash
gcc --version      # C compiler
g++ --version      # C++ compiler
make --version     # Make build tool
git --version      # Git
curl --version     # curl
wget --version     # wget
```

### Checking Project-Specific Version Requirements

**Look for version specification files:**
```bash
# Node.js
[ -f .nvmrc ] && cat .nvmrc
[ -f .node-version ] && cat .node-version
grep "engines" package.json 2>/dev/null

# Python
[ -f .python-version ] && cat .python-version
[ -f runtime.txt ] && cat runtime.txt
grep "python_requires" setup.py 2>/dev/null

# Ruby
[ -f .ruby-version ] && cat .ruby-version
grep "ruby" Gemfile 2>/dev/null

# Go
[ -f go.mod ] && grep "^go " go.mod

# Rust
[ -f rust-toolchain ] && cat rust-toolchain
grep "rust-version" Cargo.toml 2>/dev/null
```

**README and documentation:**
```bash
# Check README for version requirements
[ -f README.md ] && grep -i "version\|require" README.md | head -10
[ -f CONTRIBUTING.md ] && grep -i "version\|require" CONTRIBUTING.md | head -10
```

### Quick Environment Verification

Run this comprehensive check before starting:
```bash
#!/bin/bash
echo "=== Environment Check ==="
echo "OS: $(uname -s) $(uname -r)"
echo ""

# Languages
echo "--- Languages ---"
command -v python3 >/dev/null && python3 --version || echo "Python: not installed"
command -v node >/dev/null && node --version || echo "Node.js: not installed"
command -v npm >/dev/null && npm --version || echo "npm: not installed"
command -v go >/dev/null && go version || echo "Go: not installed"
command -v java >/dev/null && java -version 2>&1 | head -1 || echo "Java: not installed"
command -v rustc >/dev/null && rustc --version || echo "Rust: not installed"
command -v ruby >/dev/null && ruby --version || echo "Ruby: not installed"
command -v php >/dev/null && php --version | head -1 || echo "PHP: not installed"
echo ""

# Build tools
echo "--- Build Tools ---"
command -v gcc >/dev/null && gcc --version | head -1 || echo "gcc: not installed"
command -v make >/dev/null && make --version | head -1 || echo "make: not installed"
command -v git >/dev/null && git --version || echo "git: not installed"
echo ""

# Package managers
echo "--- Package Managers ---"
command -v pip3 >/dev/null && pip3 --version || echo "pip: not installed"
command -v pnpm >/dev/null && pnpm --version || echo "pnpm: not installed"
command -v yarn >/dev/null && yarn --version || echo "yarn: not installed"
command -v cargo >/dev/null && cargo --version || echo "cargo: not installed"
command -v composer >/dev/null && composer --version || echo "composer: not installed"
command -v bundle >/dev/null && bundle --version || echo "bundle: not installed"
echo ""

# Databases
echo "--- Databases ---"
command -v psql >/dev/null && psql --version || echo "PostgreSQL: not installed"
command -v mysql >/dev/null && mysql --version || echo "MySQL: not installed"
command -v redis-cli >/dev/null && redis-cli --version || echo "Redis: not installed"
command -v mongod >/dev/null && mongod --version | head -1 || echo "MongoDB: not installed"
echo ""

# Docker
echo "--- Containerization ---"
command -v docker >/dev/null && docker --version || echo "Docker: not installed"
command -v docker >/dev/null && docker compose version 2>/dev/null || echo "Docker Compose: not installed"
echo ""

echo "=== Environment Check Complete ==="
```

## Language-Specific Execution

### Python

**Basic execution:**
```bash
python script.py
# or for Python 3 specifically
python3 script.py
```

**With virtual environment (recommended):**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python script.py
```

**Running as module:**
```bash
python -m package.module
```

**Common frameworks:**
```bash
# Flask
flask run --host 0.0.0.0 --port 5000

# Django
python manage.py runserver 0.0.0.0:8000

# FastAPI
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Streamlit
streamlit run app.py --server.port 8501
```

### Node.js / JavaScript / TypeScript

**Basic execution:**
```bash
# JavaScript
node script.js

# TypeScript (using tsx)
npx tsx script.ts

# TypeScript (compile first)
npx tsc && node dist/script.js
```

**Package manager workflows:**
```bash
# npm
npm install
npm run dev  # or npm start, npm run build, npm test

# pnpm
pnpm install
pnpm dev

# yarn
yarn install
yarn dev

# bun
bun install
bun run script.ts
```

**Common frameworks:**
```bash
# Next.js
npm run dev -- --port 3000

# React (Vite)
npm run dev -- --host 0.0.0.0 --port 3000

# Express
node server.js

# NestJS
npm run start:dev
```

### Java

**Basic compilation and execution:**
```bash
# Single file
javac Main.java
java Main

# With classpath
javac -cp "lib/*" Main.java
java -cp ".:lib/*" Main
```

**Build tools:**
```bash
# Maven
mvn clean install
mvn exec:java -Dexec.mainClass="com.example.Main"
mvn spring-boot:run

# Gradle
gradle build
gradle run
gradle bootRun
```

### Go

**Basic execution:**
```bash
# Run directly
go run main.go

# Run package
go run .

# Build and run
go build -o app
./app
```

**With modules:**
```bash
go mod download
go mod tidy
go run .
```

**Testing:**
```bash
go test ./...
go test -v ./...
```

### Rust

**Using Cargo:**
```bash
# Run in debug mode
cargo run

# Run in release mode
cargo run --release

# Build only
cargo build
cargo build --release

# Test
cargo test
```

### Ruby

**Basic execution:**
```bash
ruby script.rb
```

**With Bundler:**
```bash
bundle install
bundle exec ruby script.rb
```

**Rails:**
```bash
bundle install
rails db:migrate
rails server -b 0.0.0.0 -p 3000
```

### PHP

**Basic execution:**
```bash
php script.php
```

**Development server:**
```bash
php -S localhost:8000 -t public
```

**Composer:**
```bash
composer install
php artisan serve  # Laravel
```

## Managing Long-Running Processes

Always use tmux for servers, watchers, and daemons that need to persist.

### Starting a development server in tmux

```bash
# Create or attach to session
SESSION_NAME="dev-server"
tmux -f /exec-daemon/tmux.portal.conf has-session -t "=$SESSION_NAME" 2>/dev/null || \
  tmux -f /exec-daemon/tmux.portal.conf new-session -d -s "$SESSION_NAME" -c "$PWD" -- "${SHELL:-zsh}" -l

# Send command to session
tmux -f /exec-daemon/tmux.portal.conf send-keys -t "$SESSION_NAME:0.0" 'npm run dev' C-m

# Attach to see output
tmux -f /exec-daemon/tmux.portal.conf attach-session -t "$SESSION_NAME"
```

### Listing and managing sessions

```bash
# List active sessions
tmux -f /exec-daemon/tmux.portal.conf ls

# Kill a specific session
tmux -f /exec-daemon/tmux.portal.conf kill-session -t "dev-server"

# Kill all sessions
tmux -f /exec-daemon/tmux.portal.conf kill-server
```

## Dependency Management

### Before installing dependencies

1. **Check if files exist:**
   ```bash
   # Node.js
   [ -f package.json ] && echo "Found package.json"
   
   # Python
   [ -f requirements.txt ] && echo "Found requirements.txt"
   
   # Go
   [ -f go.mod ] && echo "Found go.mod"
   ```

2. **Check for lockfiles:**
   ```bash
   # Prefer lockfiles for reproducible installs
   [ -f package-lock.json ] && npm ci    # Use ci instead of install
   [ -f pnpm-lock.yaml ] && pnpm install --frozen-lockfile
   [ -f yarn.lock ] && yarn install --frozen-lockfile
   ```

3. **Verify package manager availability:**
   ```bash
   command -v npm >/dev/null || echo "npm not found"
   command -v python3 >/dev/null || echo "python3 not found"
   ```

### Common installation commands

```bash
# Node.js - prefer locked installs
npm ci                           # Use lockfile exactly
npm install                      # Update packages
pnpm install --frozen-lockfile  # Locked pnpm install

# Python
pip install -r requirements.txt
pip install -e .                # Editable install
poetry install                  # Poetry

# Go
go mod download
go mod tidy

# Rust
cargo fetch
cargo build

# Ruby
bundle install

# PHP
composer install
```

## Testing Code

### Running tests by language

```bash
# Node.js
npm test
npm run test:unit
npm run test:e2e
npx jest
npx vitest

# Python
pytest
pytest -v tests/
python -m unittest discover

# Go
go test ./...
go test -v -cover ./...

# Rust
cargo test
cargo test -- --nocapture

# Java
mvn test
gradle test

# Ruby
bundle exec rspec
rails test
```

### Test output verification

Always check:
1. Exit code: `$?` should be 0 for success
2. Test count: number of tests run, passed, failed
3. Coverage information (if available)
4. Error messages and stack traces

## Environment Variables and Configuration

### Setting environment variables

```bash
# Inline for single command
PORT=3000 npm run dev

# Export for session
export DATABASE_URL="postgresql://localhost:5432/mydb"
export NODE_ENV=development

# From .env file (if supported)
# Many frameworks auto-load .env files
# or use: source .env

# Multiple variables
env PORT=3000 NODE_ENV=production node server.js
```

### Configuration file formats

Common locations to check:
- `.env`, `.env.local`, `.env.development`
- `config.json`, `config.yaml`, `config.toml`
- `.npmrc`, `.yarnrc`, `.python-version`
- Language-specific: `tsconfig.json`, `pyproject.toml`, `Cargo.toml`

## Verification and Debugging

### Check if a process is running

```bash
# By port
lsof -ti:3000 || echo "Port 3000 is free"
netstat -tlnp | grep :3000

# By name
ps aux | grep "node.*dev"
pgrep -f "python.*app.py"
```

### Stop running processes

```bash
# By port
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

# By PID
kill -TERM <pid>   # Graceful
kill -9 <pid>      # Force

# Stop tmux session
tmux kill-session -t "dev-server"
```

### Verify successful execution

```bash
# Check exit code
python script.py
if [ $? -eq 0 ]; then
  echo "Success"
else
  echo "Failed with code $?"
fi

# With error handling
set -e  # Exit on any error
npm install
npm test
npm run build
```

## Common Execution Patterns

### Quick script execution

For one-off scripts that complete quickly:
```bash
# Python one-liner
python -c "print('Hello, World')"

# Node.js one-liner
node -e "console.log('Hello, World')"

# Execute and capture output
OUTPUT=$(python script.py)
echo "Result: $OUTPUT"
```

### Background execution (avoid this pattern)

**Do NOT use `&` for backgrounding.** Use tmux instead:
```bash
# BAD - loses process management
npm run dev &

# GOOD - use tmux
SESSION_NAME="dev-server"
tmux -f /exec-daemon/tmux.portal.conf new-session -d -s "$SESSION_NAME"
tmux -f /exec-daemon/tmux.portal.conf send-keys -t "$SESSION_NAME:0.0" 'npm run dev' C-m
```

### Chaining commands

```bash
# Sequential (stop on failure)
npm install && npm run build && npm start

# Sequential (continue on failure)
npm install ; npm run build ; npm start

# Conditional
npm run build && echo "Build succeeded" || echo "Build failed"
```

## Framework-Specific Patterns

### React / Next.js / Vite

```bash
# Install and run
npm install
npm run dev -- --host 0.0.0.0 --port 3000

# Build for production
npm run build
npm run start  # Or serve the build output
```

### Django / Flask

```bash
# Django
python manage.py migrate
python manage.py createsuperuser  # Interactive
python manage.py runserver 0.0.0.0:8000

# Flask
export FLASK_APP=app.py
export FLASK_ENV=development
flask run --host 0.0.0.0 --port 5000
```

### Express / NestJS

```bash
# Express
npm install
node server.js
# or with nodemon for development
npx nodemon server.js

# NestJS
npm install
npm run start:dev
```

### Spring Boot

```bash
# Maven
mvn clean install
mvn spring-boot:run -Dspring-boot.run.profiles=dev

# Gradle
gradle bootRun --args='--spring.profiles.active=dev'
```

## Troubleshooting Common Issues

### Port already in use

```bash
# Find and kill process on port
PORT=3000
lsof -ti:$PORT | xargs kill -9 2>/dev/null || echo "Port $PORT is free"
```

### Permission denied

```bash
# Make script executable
chmod +x script.sh
./script.sh

# Or run with interpreter
bash script.sh
python script.py
```

### Module not found

```bash
# Verify installation
npm list package-name
pip show package-name

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Python: check Python path
python -c "import sys; print(sys.path)"
```

### Command not found

```bash
# Check if command exists
command -v npm || echo "npm not installed"

# Use npx for Node.js packages
npx tsx script.ts  # Instead of tsx script.ts

# Check PATH
echo $PATH
which node
```

## Quick Execution Checklist

Before running code, verify:
1. [ ] Read the code/config to understand what will run
2. [ ] Check if dependencies need to be installed
3. [ ] Verify no conflicting processes are running (ports)
4. [ ] Use tmux for long-running processes
5. [ ] Set required environment variables
6. [ ] Check file permissions if needed
7. [ ] Monitor output for errors
8. [ ] Verify exit code after completion

## Examples

### Example 1: Run a Python web app

```bash
# 1. Check for requirements
[ -f requirements.txt ] && echo "Found dependencies"

# 2. Set up virtual environment
python -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run in tmux (long-running)
SESSION_NAME="flask-app"
tmux -f /exec-daemon/tmux.portal.conf new-session -d -s "$SESSION_NAME"
tmux -f /exec-daemon/tmux.portal.conf send-keys -t "$SESSION_NAME:0.0" 'source venv/bin/activate && flask run --host 0.0.0.0 --port 5000' C-m

# 5. Verify it's running
sleep 2
curl -f http://localhost:5000 || echo "Server not responding yet"
```

### Example 2: Run and test a Node.js app

```bash
# 1. Install dependencies
npm ci  # Use lockfile

# 2. Run tests
npm test
if [ $? -ne 0 ]; then
  echo "Tests failed!"
  exit 1
fi

# 3. Build
npm run build

# 4. Start in tmux
SESSION_NAME="node-app"
tmux -f /exec-daemon/tmux.portal.conf new-session -d -s "$SESSION_NAME"
tmux -f /exec-daemon/tmux.portal.conf send-keys -t "$SESSION_NAME:0.0" 'npm start' C-m
```

### Example 3: Run a Go application

```bash
# 1. Download dependencies
go mod download

# 2. Run tests
go test -v ./...

# 3. Run the application
go run .
# or build and run
go build -o app && ./app
```

## Safety Notes

- **Never run untrusted code** without reviewing it first
- **Check for sensitive operations**: file deletion, network calls, system commands
- **Verify ports** before binding servers (use 0.0.0.0 for external access)
- **Use appropriate permissions**: don't run everything as root/sudo
- **Monitor resource usage**: long-running processes can consume memory/CPU
- **Clean up**: stop processes and remove temporary files when done

## When to Use This Skill

Use this skill when:
- You need to run code in any programming language
- Setting up a development server or application
- Running tests or validation scripts
- Managing processes and dependencies
- Troubleshooting execution issues
- Verifying code functionality

For debugging runtime errors, also see the `debug-execution` skill.
