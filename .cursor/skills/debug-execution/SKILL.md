---
name: debug-execution
description: Debug code execution issues, runtime errors, and process problems. Use when code fails to run, produces errors, crashes, hangs, or behaves unexpectedly. Covers systematic debugging approaches, error analysis, and troubleshooting workflows.
environments: [cloud, ide]
---

# Debugging Code Execution

Use this skill to systematically diagnose and fix code execution problems. This covers runtime errors, crashes, hangs, environment issues, and unexpected behavior.

## Debugging Workflow

Follow this systematic approach:

1. **Reproduce** - Verify the error consistently occurs
2. **Isolate** - Identify the smallest failing component
3. **Investigate** - Gather information (logs, errors, state)
4. **Hypothesize** - Form theories about the root cause
5. **Test** - Verify each hypothesis
6. **Fix** - Apply the solution
7. **Verify** - Confirm the fix works

## Environment Setup Issues

Before debugging code, ensure the environment is properly set up. Missing or outdated tools often cause execution failures.

### Version Compatibility Issues

**Check system vs. project requirements:**
```bash
# Node.js version mismatch
# System has: v14.x, project needs: v20.x
node --version                     # Check system version
cat .nvmrc 2>/dev/null            # Check project requirement
grep "engines" package.json 2>/dev/null

# Solution: Use nvm to install correct version
nvm install 20
nvm use 20

# Python version mismatch
python3 --version                  # Check system version
cat .python-version 2>/dev/null   # Check project requirement

# Solution: Use pyenv or install specific version
pyenv install 3.11.5
pyenv local 3.11.5

# Go version mismatch
go version                         # Check system version
grep "^go " go.mod 2>/dev/null    # Check project requirement

# Solution: Install required Go version
# Download from https://go.dev/dl/
```

**Version upgrade decision matrix:**

| Symptom | Action |
|---------|--------|
| Error mentions version/compatibility | Upgrade to project-specified version |
| Module/package not found | Check if version supports the package |
| Syntax errors in dependencies | Version too old, upgrade required |
| Code runs but behaves oddly | Check for version-specific bugs |
| Security warnings | Upgrade to patched version |
| Code runs fine | Keep current version (if not EOL) |

### Missing Runtime Dependencies

**System libraries and headers:**
```bash
# Build errors often indicate missing development libraries

# Python errors like "fatal error: Python.h: No such file or directory"
sudo apt install -y python3-dev

# Node.js native module build failures
sudo apt install -y build-essential

# PostgreSQL client library errors
sudo apt install -y libpq-dev

# MySQL client library errors
sudo apt install -y default-libmysqlclient-dev

# SSL/TLS errors
sudo apt install -y libssl-dev

# Image processing errors (Pillow, etc.)
sudo apt install -y libjpeg-dev libpng-dev

# XML processing errors
sudo apt install -y libxml2-dev libxslt1-dev
```

**Common system package patterns:**
```bash
# For Python data science
sudo apt install -y python3-dev libatlas-base-dev gfortran

# For Node.js native modules
sudo apt install -y build-essential python3

# For Ruby native extensions
sudo apt install -y ruby-dev build-essential

# For Go with CGO
sudo apt install -y gcc libc6-dev
```

### Environment Variables Not Set

**Critical environment variables by framework:**
```bash
# Check what's set
env | sort

# Common missing variables:
# - DATABASE_URL / DB_HOST / DB_PASSWORD
# - API_KEY / SECRET_KEY
# - NODE_ENV / ENVIRONMENT / ENV
# - PORT / HOST
# - AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY

# Diagnose missing variable errors
# Python: KeyError in os.environ
# Node.js: process.env.VAR is undefined
# Error message mentions "environment variable"

# Quick check for common variables
echo "DATABASE_URL: ${DATABASE_URL:-NOT SET}"
echo "NODE_ENV: ${NODE_ENV:-NOT SET}"
echo "PORT: ${PORT:-NOT SET}"
```

**Loading environment files:**
```bash
# Check for env files
ls -la .env* 2>/dev/null

# Common locations:
# .env, .env.local, .env.development, .env.production
# config/.env, .env.example

# Load manually if framework doesn't auto-load
set -a
source .env
set +a

# Verify loaded
env | grep DATABASE_URL
```

### Path and Command Issues

**Command not found despite being installed:**
```bash
# Check if actually installed
dpkg -l | grep package-name  # Debian/Ubuntu
rpm -qa | grep package-name  # RedHat/CentOS

# Check PATH
echo $PATH

# Find where command is installed
which command-name
find /usr -name "command-name" 2>/dev/null

# Common issues:
# - Installed in non-standard location
# - Not in PATH
# - Shell not reloaded after installation

# Solutions:
# Reload shell
source ~/.bashrc

# Add to PATH temporarily
export PATH=$PATH:/path/to/bin

# Use full path
/full/path/to/command

# Use npx for Node.js packages
npx tsx script.ts  # Instead of tsx script.ts
```

### Service Not Running

**Check if required services are up:**
```bash
# PostgreSQL
sudo systemctl status postgresql
pg_isready  # Quick health check

# MySQL
sudo systemctl status mysql
mysqladmin ping

# Redis
sudo systemctl status redis
redis-cli ping

# MongoDB
sudo systemctl status mongod
mongosh --eval "db.adminCommand('ping')"

# Docker
sudo systemctl status docker
docker ps

# Start service if stopped
sudo systemctl start postgresql
sudo systemctl enable postgresql  # Auto-start on boot
```

### Firewall and Port Access

**Port access issues:**
```bash
# Check if firewall is blocking
sudo ufw status

# Allow port through firewall
sudo ufw allow 3000/tcp

# Check if port is actually listening
sudo netstat -tlnp | grep :3000
sudo lsof -i :3000

# Test connectivity
curl http://localhost:3000
telnet localhost 3000
nc -zv localhost 3000
```

## Quick Diagnostic Commands

| Issue Type | Diagnostic Command | Purpose |
| --- | --- | --- |
| **Process hung** | `ps aux \| grep <process>` | Find process status |
| **Port in use** | `lsof -i :PORT` or `netstat -tlnp \| grep PORT` | Find what's using a port |
| **High CPU** | `top -b -n 1 \| head -20` | Check CPU usage |
| **Memory issues** | `free -h` | Check memory availability |
| **Disk space** | `df -h` | Check disk usage |
| **File not found** | `find . -name "filename"` | Locate files |
| **Permission denied** | `ls -la path/to/file` | Check file permissions |
| **Network issues** | `curl -v http://localhost:PORT` | Test connectivity |
| **DNS issues** | `nslookup domain.com` or `dig domain.com` | Check DNS resolution |
| **Command not found** | `which command` or `command -v command` | Find command location |

## Error Categories and Solutions

### 1. Import/Module Errors

#### Python

**Error patterns:**
```
ModuleNotFoundError: No module named 'package'
ImportError: cannot import name 'function'
```

**Diagnosis:**
```bash
# Check if package is installed
pip list | grep package-name
pip show package-name

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Try importing in Python shell
python -c "import package_name"
```

**Solutions:**
```bash
# Install missing package
pip install package-name

# Reinstall with dependencies
pip install -r requirements.txt

# Check virtual environment activation
which python  # Should show venv path if activated
source venv/bin/activate

# Fix import path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### Node.js

**Error patterns:**
```
Cannot find module 'package'
Error: Cannot find module './file'
Module not found: Can't resolve 'package'
```

**Diagnosis:**
```bash
# Check if package is installed
npm list package-name
ls node_modules/ | grep package

# Check package.json
cat package.json | grep package-name

# Verify node_modules exists
[ -d node_modules ] && echo "node_modules exists" || echo "node_modules missing"
```

**Solutions:**
```bash
# Install dependencies
npm install

# Clean reinstall
rm -rf node_modules package-lock.json
npm install

# Install specific package
npm install package-name

# Check TypeScript paths (tsconfig.json)
cat tsconfig.json | grep paths
```

#### Go

**Error patterns:**
```
package X is not in GOROOT or GOPATH
cannot find package
```

**Solutions:**
```bash
# Download modules
go mod download
go mod tidy

# Verify go.mod exists
[ -f go.mod ] || go mod init module-name

# Clear cache if needed
go clean -modcache
```

### 2. Syntax and Compilation Errors

**Approach:**
1. Read the error message carefully (line number, file, description)
2. Check the specific line and surrounding context
3. Look for common syntax errors (missing brackets, quotes, semicolons)
4. Verify language-specific syntax rules

**Common patterns:**

```bash
# Python syntax errors
python -m py_compile file.py  # Check syntax without running

# JavaScript/TypeScript
npx eslint file.js
npx tsc --noEmit  # Type check only

# Go
go build  # Shows compilation errors
go vet ./...  # Static analysis

# Rust
cargo check  # Fast error checking
cargo clippy  # Linting
```

### 3. Runtime Errors and Exceptions

#### Uncaught Exceptions

**Investigation steps:**
```bash
# 1. Get full stack trace
# Python: already in output
# Node.js: run with --trace-warnings
node --trace-warnings script.js

# 2. Check error type
# - TypeError: wrong type used
# - ReferenceError: undefined variable
# - RangeError: invalid value/index
# - NetworkError: connection issues

# 3. Examine the failing line
# Read the file at the line number from the stack trace
```

**Python debugging:**
```python
# Add try-except for details
try:
    problematic_code()
except Exception as e:
    import traceback
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    traceback.print_exc()
```

**Node.js debugging:**
```javascript
// Add detailed error logging
try {
    problematicCode();
} catch (error) {
    console.error('Error name:', error.name);
    console.error('Error message:', error.message);
    console.error('Stack trace:', error.stack);
}
```

#### Null/Undefined Errors

**Diagnosis:**
```bash
# Add defensive checks
# Python: check for None
if value is not None:
    use(value)

# JavaScript: check for undefined/null
if (value != null) {
    use(value);
}

# Add logging to track where null comes from
```

### 4. Environment and Configuration Issues

#### Missing Environment Variables

**Diagnosis:**
```bash
# Check if variable is set
echo $DATABASE_URL
env | grep DATABASE

# Check .env file
[ -f .env ] && cat .env | grep DATABASE
```

**Solutions:**
```bash
# Set temporarily
export DATABASE_URL="postgresql://localhost:5432/db"

# Load from .env (if framework supports it)
# Many frameworks auto-load, or use:
set -a
source .env
set +a

# Verify it's set
echo $DATABASE_URL
```

#### Configuration File Issues

**Check:**
```bash
# File exists
[ -f config.json ] || echo "Config missing"

# Valid JSON/YAML
python -m json.tool config.json  # JSON
python -c "import yaml; yaml.safe_load(open('config.yaml'))"  # YAML

# Correct permissions
ls -la config.json

# Check for syntax errors
cat config.json  # Look for trailing commas, missing quotes, etc.
```

### 5. Port and Network Issues

#### Port Already in Use

**Diagnosis:**
```bash
# Find what's using the port
lsof -i :3000
netstat -tlnp | grep 3000

# Check if process is yours
ps aux | grep <pid>
```

**Solutions:**
```bash
# Kill the process using the port
lsof -ti:3000 | xargs kill -9 2>/dev/null

# Or use a different port
PORT=3001 npm run dev

# Kill tmux session if server is in tmux
tmux ls
tmux kill-session -t "server-name"
```

#### Connection Refused

**Diagnosis:**
```bash
# Check if server is running
ps aux | grep server-process

# Check if port is listening
lsof -i :PORT || echo "Nothing listening on PORT"

# Try connecting
curl -v http://localhost:PORT
telnet localhost PORT
```

**Solutions:**
```bash
# Ensure server binds to correct interface
# Use 0.0.0.0 for external access, not localhost
node server.js --host 0.0.0.0

# Check firewall
sudo ufw status

# Verify the port in configuration
grep -r "port.*3000" .
```

### 6. Permission and File Access Errors

#### Permission Denied

**Diagnosis:**
```bash
# Check file permissions
ls -la path/to/file

# Check ownership
ls -l path/to/file

# Check directory permissions
ls -ld path/to/directory
```

**Solutions:**
```bash
# Make file executable
chmod +x script.sh

# Change ownership (if appropriate)
sudo chown $USER:$USER file

# Change directory permissions
chmod 755 directory

# Use sudo if necessary (be cautious)
sudo command
```

#### File Not Found

**Diagnosis:**
```bash
# Check if file exists
[ -f path/to/file ] && echo "exists" || echo "not found"

# Find the file
find . -name "filename"
find . -type f -name "*.txt"

# Check current directory
pwd
ls -la

# Check relative vs absolute paths
realpath path/to/file
```

**Solutions:**
```bash
# Use absolute paths
/full/path/to/file

# Check working directory
cd /correct/directory

# Verify file was created
ls -lt | head  # Recently modified files
```

### 7. Process and Resource Issues

#### Process Hung/Not Responding

**Diagnosis:**
```bash
# Check if process is running
ps aux | grep process-name

# Check CPU usage (high = busy, low = hung)
top -b -n 1 -p <pid>

# Check for deadlocks (if applicable)
# Application-specific debugging needed
```

**Solutions:**
```bash
# Graceful termination
kill -TERM <pid>

# Force kill if needed
kill -9 <pid>

# Kill by name
pkill -9 process-name

# Kill tmux session
tmux kill-session -t "session-name"
```

#### Out of Memory

**Diagnosis:**
```bash
# Check memory usage
free -h
top -b -n 1 | head -20

# Check process memory
ps aux --sort=-%mem | head -10

# Check for memory leaks
# Monitor memory over time
watch -n 1 free -h
```

**Solutions:**
```bash
# Increase memory limits (if applicable)
# Node.js
node --max-old-space-size=4096 script.js

# Check for leaks in code
# Python: use memory_profiler
# Node.js: use --inspect and Chrome DevTools

# Optimize code to use less memory
# - Process data in chunks
# - Clear large objects
# - Use generators/streams
```

#### Disk Space Full

**Diagnosis:**
```bash
# Check disk usage
df -h

# Find large files
du -h --max-depth=1 | sort -h
find . -type f -size +100M

# Check specific directory
du -sh directory/*
```

**Solutions:**
```bash
# Clear workspace-specific temporary files only
# NEVER run rm -rf /tmp/* - it breaks shared system resources
find . -name "*.tmp" -type f -delete
find . -name ".cache" -type d -prune -exec rm -rf '{}' +

# Clear node_modules if needed
find . -name "node_modules" -type d -prune -exec rm -rf '{}' +

# Clear build artifacts
rm -rf build/ dist/ out/ .next/

# Clean package manager caches
npm cache clean --force
pip cache purge
```

## Language-Specific Debugging

### Python Debugging

```bash
# Run with debugging output
python -v script.py  # Verbose import info
python -u script.py  # Unbuffered output

# Use pdb debugger
python -m pdb script.py

# Add breakpoint in code
# Python 3.7+
# breakpoint()

# Check for syntax errors
python -m py_compile script.py

# Profile performance
python -m cProfile script.py
```

### Node.js Debugging

```bash
# Run with debugging
node --inspect script.js
node --inspect-brk script.js  # Break on start

# Trace warnings and deprecations
node --trace-warnings script.js
node --trace-deprecation script.js

# Check for issues
npx eslint .
npm audit

# Verbose npm
npm run dev --verbose
```

### Go Debugging

```bash
# Run with race detector
go run -race main.go

# Verbose output
go run -v main.go

# Build with debugging info
go build -gcflags="-N -l" -o app
dlv exec ./app  # Use delve debugger

# Check for issues
go vet ./...
golint ./...
```

### Java Debugging

```bash
# Run with debug output
java -verbose:class Main

# Enable remote debugging
java -agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=5005 Main

# Check classpath
java -cp ".:lib/*" Main -verbose

# Maven debug
mvn -X exec:java  # Debug output
```

## Log Analysis

### Finding Relevant Logs

```bash
# Application logs
tail -f app.log
tail -f /var/log/application.log

# tmux session output
# Attach to see live output
tmux attach -t session-name

# Docker logs (if applicable)
docker logs container-name
docker logs -f container-name  # Follow

# System logs
journalctl -u service-name
dmesg | tail
```

### Parsing Error Messages

**Structure of error messages:**
1. **Error type/class** - What kind of error
2. **Message** - Human-readable description
3. **Location** - File, line number, function
4. **Stack trace** - Call chain leading to error
5. **Context** - Variable values, state

**Focus on:**
- First error (others may be consequences)
- File and line number
- Error type (syntax vs runtime vs logical)
- Recent changes to the code

## Interactive Debugging

### Adding Debug Output

```python
# Python - use logging
import logging
logging.basicConfig(level=logging.DEBUG)
logging.debug(f"Variable value: {var}")

# Print debugging
print(f"DEBUG: var={var}, type={type(var)}")
```

```javascript
// Node.js - use debug module or console
console.log('DEBUG:', { var, type: typeof var });
console.trace('Call stack');

// Debug module
const debug = require('debug')('app:module');
debug('Variable value:', var);
```

```go
// Go - use log package
import "log"
log.Printf("DEBUG: var=%+v\n", var)

// Or fmt for simple cases
import "fmt"
fmt.Printf("DEBUG: var=%+v\n", var)
```

### Binary Search Debugging

For complex issues, narrow down systematically:

1. **Add checkpoint logging** at different stages
2. **Run and observe** which checkpoint is reached
3. **Narrow the search** to code between checkpoints
4. **Repeat** until you find the problematic line

```bash
# Example: Add numbered debug points
echo "DEBUG 1: Starting"
code_block_1
echo "DEBUG 2: After block 1"
code_block_2
echo "DEBUG 3: After block 2"
```

## Verification After Fixes

**Always verify:**

1. **Error is gone** - Run the original failing case
2. **Tests pass** - Run test suite
3. **No side effects** - Check related functionality
4. **Root cause addressed** - Not just symptom
5. **Reproducibility** - Run multiple times

```bash
# Run tests
npm test
pytest
go test ./...

# Try edge cases
# Test with different inputs, configurations

# Check for regressions
# Run full test suite, not just affected tests
```

## Common Pitfalls

### 1. Wrong Working Directory

```bash
# Symptom: File not found despite existing
# Fix: Check and change directory
pwd
cd /correct/directory
```

### 2. Cached/Stale Data

```bash
# Clear various caches
# Node.js
rm -rf node_modules package-lock.json && npm install

# Python
find . -type d -name __pycache__ -exec rm -rf {} +
pip cache purge

# Go
go clean -cache -modcache

# Browser cache (for web apps)
# Use incognito mode or hard refresh (Ctrl+Shift+R)
```

### 3. Version Mismatches

```bash
# Check versions
node --version
python --version
go version

# Check package versions
npm list package-name
pip show package-name

# Update if needed
npm update
pip install --upgrade package-name
```

### 4. Asynchronous Issues

**JavaScript Promise problems:**
```javascript
// Forgot await
const data = fetchData();  // BAD - Promise object

// Correct
const data = await fetchData();  // GOOD

// Unhandled promise rejection
promise.catch(err => console.error(err));
```

**Python async issues:**
```python
# Forgot await
data = fetch_data()  # BAD - coroutine object

# Correct
data = await fetch_data()  # GOOD
```

### 5. Encoding Issues

```bash
# File encoding problems
# Check encoding
file -i filename

# Convert encoding
iconv -f ISO-8859-1 -t UTF-8 input.txt > output.txt

# Python: specify encoding
with open('file.txt', 'r', encoding='utf-8') as f:
    content = f.read()
```

## Emergency Debugging Checklist

When stuck, work through this list:

- [ ] Read the **full error message** (don't stop at first line)
- [ ] Identify the **exact line** that's failing
- [ ] Check if **recent changes** caused it (use git diff)
- [ ] Verify **dependencies are installed**
- [ ] Check **environment variables** are set
- [ ] Look for **typos** in variable/function names
- [ ] Verify **file paths** are correct (absolute vs relative)
- [ ] Check **permissions** on files/directories
- [ ] Ensure **ports aren't in use**
- [ ] Check **process is actually running**
- [ ] Verify **configuration files** are valid
- [ ] Look at **logs** (application and system)
- [ ] Try the **simplest possible test case**
- [ ] **Search the error message** (web search exact error)
- [ ] Check **documentation** for the library/framework

## Advanced Debugging Techniques

### Using strace (Linux)

```bash
# Trace system calls
strace -o trace.log python script.py

# Trace file operations
strace -e trace=open,read,write python script.py

# Trace network
strace -e trace=network python script.py
```

### Using tcpdump for Network Issues

```bash
# Capture network traffic
sudo tcpdump -i any -w capture.pcap port 3000

# Monitor HTTP traffic
sudo tcpdump -i any -A port 80
```

### CPU Profiling

```bash
# Python
python -m cProfile -o profile.stats script.py
python -m pstats profile.stats

# Node.js
node --prof script.js
node --prof-process isolate-*.log > profile.txt

# Go
go test -cpuprofile cpu.prof
go tool pprof cpu.prof
```

## When to Use This Skill

Use this skill when:
- Code fails with runtime errors
- Applications crash or hang
- Dependencies fail to load
- Configuration issues arise
- Processes don't start or stop
- Network connections fail
- Performance is degraded
- Tests fail unexpectedly
- Logs show errors or warnings

For setting up and running code initially, see the `run-code` skill.

## Prevention

**Best practices to avoid issues:**

1. **Write tests** - Catch issues early
2. **Use linters** - Enforce code quality
3. **Add logging** - Track execution flow
4. **Handle errors** - Don't ignore exceptions
5. **Validate input** - Check assumptions
6. **Document dependencies** - Clear requirements
7. **Version control** - Track changes
8. **Use type checking** - Catch type errors (TypeScript, mypy)

## Summary

Debugging is systematic:
1. **Understand** the error message
2. **Locate** the failing component
3. **Investigate** with tools and logs
4. **Fix** the root cause
5. **Verify** the solution works

Most issues fall into a few categories: missing dependencies, configuration errors, environment problems, or logic bugs. Use the appropriate diagnostic commands, read error messages carefully, and work systematically from general to specific.
