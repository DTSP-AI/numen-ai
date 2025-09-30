#!/usr/bin/env node

const { execSync, spawn } = require('child_process');
const net = require('net');

const PREFERRED_PORTS = [3002, 3003];

/**
 * Check if a port is in use
 */
function isPortInUse(port) {
  return new Promise((resolve) => {
    const server = net.createServer();

    server.once('error', (err) => {
      if (err.code === 'EADDRINUSE') {
        resolve(true);
      } else {
        resolve(false);
      }
    });

    server.once('listening', () => {
      server.close();
      resolve(false);
    });

    server.listen(port, '127.0.0.1');
  });
}

/**
 * Kill process using a specific port (Windows & Unix compatible)
 */
function killPort(port) {
  try {
    if (process.platform === 'win32') {
      // Windows: netstat + taskkill
      const output = execSync(`netstat -ano | findstr :${port}`, { encoding: 'utf8' });
      const lines = output.split('\n').filter(line => line.includes('LISTENING'));

      const pids = new Set();
      lines.forEach(line => {
        const parts = line.trim().split(/\s+/);
        const pid = parts[parts.length - 1];
        if (pid && !isNaN(pid)) {
          pids.add(pid);
        }
      });

      pids.forEach(pid => {
        try {
          execSync(`taskkill /PID ${pid} /F`, { stdio: 'ignore' });
          console.log(`✓ Killed process ${pid} on port ${port}`);
        } catch (e) {
          // Process might already be dead
        }
      });
    } else {
      // Unix/Mac: lsof + kill
      const output = execSync(`lsof -ti:${port}`, { encoding: 'utf8' }).trim();
      if (output) {
        const pids = output.split('\n');
        pids.forEach(pid => {
          try {
            execSync(`kill -9 ${pid}`, { stdio: 'ignore' });
            console.log(`✓ Killed process ${pid} on port ${port}`);
          } catch (e) {
            // Process might already be dead
          }
        });
      }
    }
  } catch (error) {
    // No process found or error - that's okay
  }
}

/**
 * Find available port or kill occupied one
 */
async function findAndPreparePort() {
  console.log('🔍 Checking ports...\n');

  for (const port of PREFERRED_PORTS) {
    const inUse = await isPortInUse(port);

    if (!inUse) {
      console.log(`✓ Port ${port} is available\n`);
      return port;
    } else {
      console.log(`⚠ Port ${port} is occupied`);
    }
  }

  // All ports occupied - kill the first one and use it
  const portToUse = PREFERRED_PORTS[0];
  console.log(`\n🧹 Clearing port ${portToUse}...`);
  killPort(portToUse);

  // Wait a moment for port to be released
  await new Promise(resolve => setTimeout(resolve, 1000));

  console.log(`✓ Port ${portToUse} cleared\n`);
  return portToUse;
}

/**
 * Start Next.js dev server
 */
async function startDevServer() {
  const port = await findAndPreparePort();

  console.log(`🚀 Starting Next.js on port ${port}...\n`);

  const devProcess = spawn('npx', ['next', 'dev', '-p', port.toString()], {
    stdio: 'inherit',
    shell: true,
    cwd: __dirname
  });

  // Handle clean shutdown
  process.on('SIGINT', () => {
    console.log('\n🛑 Shutting down dev server...');
    devProcess.kill('SIGINT');
    process.exit(0);
  });

  process.on('SIGTERM', () => {
    devProcess.kill('SIGTERM');
    process.exit(0);
  });

  devProcess.on('exit', (code) => {
    process.exit(code || 0);
  });
}

// Run
startDevServer().catch(error => {
  console.error('❌ Error starting dev server:', error);
  process.exit(1);
});