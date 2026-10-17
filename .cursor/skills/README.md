# Cursor Agent Skills

This directory contains skills to help AI agents (Cursor and Claude) effectively run and debug code across multiple programming languages and environments.

## Available Skills

### 1. [run-code](./run-code/SKILL.md)
**Purpose**: Execute code in various languages and frameworks efficiently.

**Use when**:
- Running code in any programming language (Python, Node.js, Java, Go, Rust, Ruby, PHP)
- Setting up development servers or applications
- Managing processes and dependencies
- Configuring environments from scratch
- Running tests or validation scripts
- Verifying code functionality

**Key Features**:
- ✅ Environment setup from zero (fresh system installation)
- ✅ Version management guidance (when to upgrade vs. keep current versions)
- ✅ Quick reference tables for common operations
- ✅ Language-specific execution patterns (8+ languages)
- ✅ Framework support (React, Next.js, Django, Flask, Express, Spring Boot, etc.)
- ✅ Process management with tmux
- ✅ Dependency installation workflows
- ✅ Testing patterns by language
- ✅ Database setup (PostgreSQL, MySQL, Redis, MongoDB)
- ✅ Docker installation and setup
- ✅ Comprehensive environment verification script

### 2. [debug-execution](./debug-execution/SKILL.md)
**Purpose**: Debug code execution issues, runtime errors, and process problems systematically.

**Use when**:
- Code fails to run or produces errors
- Applications crash, hang, or behave unexpectedly
- Import/module errors occur
- Environment or configuration issues arise
- Network connections fail
- Processes don't start or stop correctly
- Version compatibility problems
- Tests fail unexpectedly

**Key Features**:
- ✅ Systematic debugging workflow
- ✅ Environment setup troubleshooting (version mismatches, missing dependencies)
- ✅ Quick diagnostic command reference
- ✅ Error category solutions (imports, syntax, runtime, environment, network, permissions)
- ✅ Language-specific debugging (Python, Node.js, Go, Java)
- ✅ Log analysis techniques
- ✅ Interactive debugging approaches
- ✅ Common pitfalls and solutions
- ✅ Advanced techniques (strace, tcpdump, profiling)
- ✅ Emergency debugging checklist

## Philosophy: Version Management

These skills follow a pragmatic approach to version management:

### ✅ **Keep Current Versions When**:
- Code runs successfully with current versions
- Project doesn't specify version requirements
- System versions are recent and maintained
- No security vulnerabilities or compatibility issues

### ⬆️ **Upgrade Versions When**:
- Project has version specification files (`.nvmrc`, `.python-version`, `go.mod`, etc.)
- README or documentation specifies version requirements
- Current system version is EOL (end-of-life) or has security issues
- Build/runtime errors specifically indicate version incompatibility
- Error messages mention version or compatibility problems

### 🚫 **Do NOT Upgrade If**:
- Everything works fine with current setup
- No explicit requirement for newer version
- Upgrade would introduce unnecessary complexity
- System is already on a recent stable version

## Quick Start

### For Agents

When you need to run or debug code:

1. **Read the appropriate skill** based on your task
2. **Check environment requirements** first (versions, dependencies)
3. **Follow language-specific patterns** for the technology stack
4. **Use diagnostic commands** when issues arise
5. **Apply systematic debugging** for errors

### Running the Environment Check

Both skills include comprehensive environment verification. Use this to check what's installed:

```bash
# Quick check
command -v python3 && python3 --version
command -v node && node --version
command -v go && go version

# Comprehensive check (included in run-code skill)
# Copy and run the "Quick Environment Verification" script
```

## Coverage

### Languages
- Python (3.x)
- Node.js / JavaScript / TypeScript
- Go
- Java
- Rust
- Ruby
- PHP

### Frameworks & Tools
- **Web**: React, Next.js, Vite, Express, NestJS, Django, Flask, FastAPI, Rails, Spring Boot
- **Databases**: PostgreSQL, MySQL, MongoDB, Redis
- **Build Tools**: npm, pnpm, yarn, Maven, Gradle, Cargo, Bundler, Composer
- **Containers**: Docker, Docker Compose
- **Version Managers**: nvm, pyenv, rbenv, rustup, SDKMAN

### Operating Systems
Primary focus: Ubuntu/Debian Linux (apt-based systems)
Many patterns apply to other Linux distributions and macOS.

## Skill Structure

Each skill follows this structure:

1. **Frontmatter** - metadata (name, description, environments)
2. **Overview** - what the skill covers
3. **Quick Reference** - tables and cheat sheets
4. **Core Concepts** - fundamental principles
5. **Detailed Guides** - step-by-step instructions
6. **Examples** - real-world scenarios
7. **Troubleshooting** - common issues and solutions
8. **Best Practices** - safety and prevention

## Integration with Cloud Agent Environments

These skills complement the existing Cursor skills ecosystem:

- **env-setup**: Use for Cloud Agent-specific environment configuration
- **run-code**: Use for executing code across languages once environment is set up
- **debug-execution**: Use for troubleshooting runtime and execution issues
- **walkthrough-artifacts**: Use for creating demo evidence after successful execution

## Contributing

When updating these skills:

1. Keep the pragmatic version management philosophy
2. Include both "from zero" setup and quick execution patterns
3. Provide diagnostic commands before solutions
4. Use real-world examples and error messages
5. Test commands on a clean system when possible
6. Update the quick reference tables
7. Add troubleshooting entries for common issues

## Version History

- **v1.0.0** (2026-10-17)
  - Initial release
  - Environment setup from zero
  - Version management guidelines
  - 8+ language coverage
  - Systematic debugging workflows
  - Emergency checklists

## License

Part of the Axiom project. See repository LICENSE.
