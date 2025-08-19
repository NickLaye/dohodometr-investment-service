#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

function safeExec(cmd) {
  try {
    return execSync(cmd, { stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim();
  } catch {
    return '';
  }
}

function main() {
  const projectRoot = process.cwd();
  const publicDir = path.join(projectRoot, 'public');
  const versionFile = path.join(publicDir, 'version.json');

  const envSha = process.env.GIT_SHA || process.env.VCS_REF || '';
  const envBranch = process.env.GIT_BRANCH || process.env.BRANCH || '';

  // Attempt to read from git if env vars are absent and .git is available
  const gitSha = envSha || safeExec('git rev-parse --short HEAD');
  const gitBranch = envBranch || safeExec('git rev-parse --abbrev-ref HEAD');
  const isoDate = new Date().toISOString();

  const meta = {
    commit: gitSha || 'unknown',
    date: isoDate,
    branch: gitBranch || 'unknown',
  };

  if (!fs.existsSync(publicDir)) {
    fs.mkdirSync(publicDir, { recursive: true });
  }

  fs.writeFileSync(versionFile, JSON.stringify(meta, null, 2) + '\n', 'utf8');

  // Also emit a plain text stamp for quick grepping if needed
  fs.writeFileSync(
    path.join(publicDir, 'version.txt'),
    `${meta.commit} ${meta.date} ${meta.branch}\n`,
    'utf8'
  );

  console.log(`[build-meta] Wrote ${path.relative(projectRoot, versionFile)}:`, meta);
}

main();


