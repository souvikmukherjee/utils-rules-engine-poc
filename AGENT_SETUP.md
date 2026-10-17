# AI Agent Setup Guide

**For Cursor and Claude agents setting up this project from a fresh git clone.**

This guide helps AI agents (Cursor, Claude, or others) set up and run this project from scratch, including environment setup, dependency installation, and execution.

## 🎯 Quick Start for Agents

When you receive this repository URL, follow these steps:

### 1. Clone and Navigate
```bash
git clone <repository-url>
cd <repository-name>
```

### 2. Read the Agent Skills
This repository includes comprehensive skills for running and debugging code:

📚 **Essential Skills** (in `.cursor/skills/` directory):
- **[run-code](.cursor/skills/run-code/SKILL.md)** - Execute code from zero, including environment setup
- **[debug-execution](.cursor/skills/debug-execution/SKILL.md)** - Systematic debugging and troubleshooting
- **[README](.cursor/skills/README.md)** - Skills overview and philosophy

**⚠️ READ THESE FIRST** before attempting to run code. They contain:
- Environment setup from scratch (Python, Node.js, Java, Go, etc.)
- Version management guidance
- Framework-specific patterns
- Troubleshooting workflows

### 3. Check Project Requirements
```bash
# Check what this project needs
ls -la  # Look for package.json, requirements.txt, go.mod, etc.

# Read the main README
cat README.md | head -50

# Check for version specifications
cat .nvmrc 2>/dev/null          # Node.js version
cat .python-version 2>/dev/null # Python version
grep "^go " go.mod 2>/dev/null  # Go version
```

### 4. Verify Environment
```bash
# Quick environment check
command -v python3 && python3 --version
command -v node && node --version
command -v go && go version
command -v java && java -version

# For comprehensive check, use the script in run-code skill
```

### 5. Install Missing Tools
If tools are missing, **refer to `.cursor/skills/run-code/SKILL.md`** section "Setting Up Environments from Zero" for detailed installation instructions for:
- Python (with pyenv)
- Node.js (with nvm)
- Go
- Java (with Maven/Gradle)
- Rust
- Ruby
- PHP
- Databases (PostgreSQL, MySQL, MongoDB, Redis)
- Docker

### 6. Install Project Dependencies
```bash
# This project uses:
make install-py      # Python packages
make install-web     # Node.js packages
make install-kogito  # Java (Kogito service)

# Or follow the README's "Developer how-to" section
```

### 7. Run the Project
```bash
# Start services
make kogito          # Kogito service on :8081
make api             # Python API on :8000
make web             # Next.js UI on :3000

# Or use tmux for long-running processes (see run-code skill)
```

## 📋 For This Specific Project (Axiom)

### Technology Stack
- **Frontend**: Next.js 15, React, TypeScript
- **Backend**: FastAPI (Python 3.11+)
- **Rules Engine**: GoRules Zen (Python), Kogito (Java/Quarkus)
- **Database**: SQLite (default), PostgreSQL (optional)
- **Build Tools**: pnpm (Node.js), Maven (Java)

### Prerequisites Checklist
- [ ] Node.js 20+ with pnpm
- [ ] Python 3.11+ with pip
- [ ] Java 17+ with Maven (for Kogito)
- [ ] Git

### Installation Steps

**1. Python Environment:**
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python packages
pip install -e packages/rules_engine
pip install -e apps/api

# Or use make
make install-py
```

**2. Node.js Environment:**
```bash
# Install pnpm if needed
npm install -g pnpm

# Install dependencies
pnpm install

# Or use make
make install-web
```

**3. Java Environment (Optional - for Kogito):**
```bash
# Package the Kogito service
make install-kogito
```

### Running the Project

**Option 1: Using Make (Recommended)**
```bash
# Terminal 1: Start Kogito service
make kogito

# Terminal 2: Start Python API
make api

# Terminal 3: Start Next.js frontend
make web
```

**Option 2: Using tmux (for agents)**
```bash
# Create sessions for each service
SESSION="axiom-kogito"
tmux -f /exec-daemon/tmux.portal.conf new-session -d -s "$SESSION" -c "$PWD/apps/kogito"
tmux -f /exec-daemon/tmux.portal.conf send-keys -t "$SESSION:0.0" 'make kogito' C-m

SESSION="axiom-api"
tmux -f /exec-daemon/tmux.portal.conf new-session -d -s "$SESSION" -c "$PWD"
tmux -f /exec-daemon/tmux.portal.conf send-keys -t "$SESSION:0.0" 'make api' C-m

SESSION="axiom-web"
tmux -f /exec-daemon/tmux.portal.conf new-session -d -s "$SESSION" -c "$PWD"
tmux -f /exec-daemon/tmux.portal.conf send-keys -t "$SESSION:0.0" 'make web' C-m

# List sessions
tmux -f /exec-daemon/tmux.portal.conf ls
```

**Option 3: Manual Commands**
```bash
# Kogito (Terminal 1)
cd apps/kogito
mvn quarkus:dev

# API (Terminal 2)
source .venv/bin/activate
PYTHONPATH=packages/rules_engine/src:apps/api/src \
  uvicorn rules_api.main:app --reload --host 127.0.0.1 --port 8000

# Web (Terminal 3)
cd apps/web
pnpm dev
```

### Verification
```bash
# Check services are running
curl http://localhost:8081/q/health  # Kogito
curl http://localhost:8000/docs      # API (OpenAPI docs)
curl http://localhost:3000           # Web UI

# Or open in browser
# Web UI: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

## 🐛 If Something Fails

1. **Read the error message carefully** - note the error type and location
2. **Consult `.cursor/skills/debug-execution/SKILL.md`** - systematic debugging guide
3. **Check environment issues**:
   - Version mismatches (see debug-execution skill)
   - Missing dependencies (see run-code skill)
   - Ports already in use: `lsof -ti:3000 | xargs kill -9`
   - Services not running: check with `ps aux | grep <service>`

4. **Common Issues**:
   ```bash
   # Port already in use
   lsof -ti:3000 | xargs kill -9
   
   # Python module not found
   pip install -e packages/rules_engine -e apps/api
   
   # Node modules missing
   rm -rf node_modules && pnpm install
   
   # Permission denied
   chmod +x script.sh
   ```

## 🤖 Philosophy: Version Management

From the skills documentation:

**✅ Keep current versions when:**
- Code runs successfully
- No explicit version requirements in project
- System versions are recent and maintained

**⬆️ Upgrade versions when:**
- Project has `.nvmrc`, `.python-version`, or similar
- README specifies version requirements
- Build/runtime errors indicate version incompatibility
- Current version is EOL or has security issues

**🚫 Don't upgrade if:**
- Everything works fine
- No explicit requirements
- Would introduce unnecessary complexity

## 📚 Additional Resources

### In This Repository
- [Main README](README.md) - Project overview and product tour
- [Product Documentation](docs/PRODUCT.md) - Product vision
- [Architecture](docs/ARCHITECTURE.md) - Technical architecture
- [Skills README](.cursor/skills/README.md) - Agent skills overview

### Skills Directory
```
.cursor/skills/
├── README.md                      # Overview
├── run-code/
│   └── SKILL.md                   # Execution guide (675 lines)
└── debug-execution/
    └── SKILL.md                   # Debugging guide (855 lines)
```

### What Each Skill Covers

**run-code (675 lines):**
- Environment setup from zero
- Language-specific execution (8+ languages)
- Framework patterns (20+ frameworks)
- Database setup
- Docker installation
- Process management with tmux
- Testing patterns
- Dependency management

**debug-execution (855 lines):**
- Systematic debugging workflow
- Environment troubleshooting
- Error category solutions
- Import/module errors
- Version compatibility
- Network and port issues
- Permission problems
- Advanced debugging techniques

## 🎓 For Claude Specifically

When Claude receives just a git URL:

1. **Clone the repository**
2. **Read this file first** (`AGENT_SETUP.md`)
3. **Read `.cursor/skills/run-code/SKILL.md`** for environment setup
4. **Check project requirements** (package.json, requirements.txt, etc.)
5. **Verify environment** or install missing tools
6. **Follow project-specific installation** (above)
7. **Run the project** and verify
8. **If issues occur**, read `.cursor/skills/debug-execution/SKILL.md`

## 🚀 Success Criteria

You've successfully set up the project when:

- [ ] All required tools are installed and correct versions
- [ ] All dependencies are installed without errors
- [ ] All three services start successfully (Kogito, API, Web)
- [ ] Web UI loads at http://localhost:3000
- [ ] API responds at http://localhost:8000/docs
- [ ] Kogito responds at http://localhost:8081/q/health
- [ ] You can evaluate a test case in the UI

## ℹ️ About This Guide

This guide is designed for AI agents (Cursor, Claude, or others) to autonomously:
- Clone and set up projects from scratch
- Install missing tools and dependencies
- Run multi-service applications
- Debug issues systematically
- Follow best practices for version management

The comprehensive skills in `.cursor/skills/` provide language-agnostic guidance applicable to any project, while this guide is specific to the Axiom repository.

---

**Questions or Issues?**
- Check the skills: `.cursor/skills/run-code/SKILL.md` and `.cursor/skills/debug-execution/SKILL.md`
- Read the main README: `README.md`
- Check the Makefile: `Makefile`
