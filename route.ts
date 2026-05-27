import { NextResponse } from 'next/server';
import { execSync } from 'child_process';
import path from 'path';
import fs from 'fs';

export async function POST(request: Request) {
  try {
    const { githubUrl, repoName } = await request.json();
    
    if (!githubUrl || !repoName) {
      return NextResponse.json(
        { error: "Missing required parameters: githubUrl and repoName are required." }, 
        { status: 400 }
      );
    }

    // Sanitize the workspace handle to avoid path bleeding characters
    const cleanRepoName = repoName.replace(/[^a-zA-Z0-9_-]/g, '');
    const baseProjectDir = process.cwd();
    const hostWorkspacePath = path.join(baseProjectDir, 'vault_workspace', cleanRepoName);

    // FAST-PATH CACHE CHECK: Optimize repository retrieval lifecycle
    if (fs.existsSync(hostWorkspacePath) && fs.existsSync(path.join(hostWorkspacePath, '.git'))) {
      console.log(`[SENTINODE UI] Target workspace directory detected. Running fast-update...`);
      try {
        // Fetch only new structural commits instead of redownloading the entire repository
        execSync(`cd ${hostWorkspacePath} && git pull`, { stdio: 'inherit' });
      } catch (pullError) {
        console.log(`[SENTINODE UI] Git pull failed (forcing clean re-clone fallback)...`);
        fs.rmSync(hostWorkspacePath, { recursive: true, force: true });
        fs.mkdirSync(hostWorkspacePath, { recursive: true });
        execSync(`git clone ${githubUrl} ${hostWorkspacePath}`, { stdio: 'inherit' });
      }
    } else {
      console.log(`[SENTINODE UI] Initializing brand-new workspace slot: ${hostWorkspacePath}`);
      if (fs.existsSync(hostWorkspacePath)) {
        fs.rmSync(hostWorkspacePath, { recursive: true, force: true });
      }
      fs.mkdirSync(hostWorkspacePath, { recursive: true });
      execSync(`git clone ${githubUrl} ${hostWorkspacePath}`, { stdio: 'inherit' });
    }

    console.log("[SENTINODE UI] Spawning isolated tool container to execute engine pipeline loop...");
    
    // Trigger your pre-baked fast-path Docker container toolchain engine
    execSync(
      `docker compose run --rm sentinode-engine /app/orchestrator.sh /app/vault_workspace/${cleanRepoName}`, 
      { stdio: 'inherit', cwd: baseProjectDir }
    );

    // Track down the output schematic manifest payload file
    const manifestFileTarget = path.join(hostWorkspacePath, 'sentinode_master_manifest.json');
    
    if (!fs.existsSync(manifestFileTarget)) {
      return NextResponse.json({ 
        error: "Pipeline execution completed but 'sentinode_master_manifest.json' was not generated inside the workspace." 
      }, { status: 500 });
    }

    // Read the master manifest JSON schema straight from disk storage
    const compiledPayloadRaw = fs.readFileSync(manifestFileTarget, 'utf8');
    
    return NextResponse.json(JSON.parse(compiledPayloadRaw));

  } catch (error: any) {
    console.error("[SENTINODE UI API EXCEPTION]:", error);
    return NextResponse.json(
      { error: "Static analysis execution failed inside the sandbox tool container", details: error.message }, 
      { status: 500 }
    );
  }
}
