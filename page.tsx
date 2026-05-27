'use client';
import { useState } from 'react';

export default function SentinodeConsoleViewer() {
  const [githubUrl, setGithubUrl] = useState<string>('');
  const [repoName, setRepoName] = useState<string>('');
  const [rawSchemaText, setRawSchemaText] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [runtimeError, setRuntimeError] = useState<string | null>(null);

  const executePipelineTrigger = async () => {
    setIsProcessing(true);
    setRuntimeError(null);
    setRawSchemaText('');
    
    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ githubUrl, repoName })
      });
      
      const payloadData = await response.json();
      
      if (!response.ok) {
        throw new Error(payloadData.details || payloadData.error || 'Pipeline engine processing error.');
      }
      
      // Store the master manifest exactly as a formatted text block string representation
      setRawSchemaText(JSON.stringify(payloadData, null, 2));
    } catch (err: any) {
      setRuntimeError(err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 font-mono text-xs p-6 select-text">
      <div className="max-w-7xl mx-auto space-y-4">
        
        {/* Workspace Metric Header Row */}
        <header className="border-b border-slate-800 pb-4">
          <h1 className="text-sm font-bold text-emerald-400 tracking-wider">SENTINODE // PROTOCOL SCHEMATIC ENGINE SOURCE</h1>
          <p className="text-[10px] text-slate-500 mt-0.5">Method B Architecture: Host Next.js App Layer ➔ On-Demand Docker Sandbox Workspace Execution</p>
        </header>

        {/* Input Parameters Dynamic Processing Controller */}
        <section className="bg-slate-900 border border-slate-800 p-4 rounded gap-4 grid grid-cols-1 md:grid-cols-3 items-end">
          <div>
            <label className="block text-[10px] text-slate-400 mb-1 font-bold">1. SYSTEM STORAGE WORKSPACE ACCOUNT IDENTITY</label>
            <input 
              type="text" 
              placeholder="e.g., v2-core-vault"
              className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-1.5 focus:outline-none focus:border-emerald-500 text-slate-200"
              value={repoName}
              onChange={(e) => setRepoName(e.target.value)}
              disabled={isProcessing}
            />
          </div>
          <div className="md:col-span-2 flex gap-4 items-end">
            <div className="flex-1">
              <label className="block text-[10px] text-slate-400 mb-1 font-bold">2. RECOVERY PUBLIC TARGET SOURCE GIT ROUTE</label>
              <input 
                type="text" 
                placeholder="https://github.com"
                className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-1.5 focus:outline-none focus:border-emerald-500 text-slate-200"
                value={githubUrl}
                onChange={(e) => setGithubUrl(e.target.value)}
                disabled={isProcessing}
              />
            </div>
            <button 
              onClick={executePipelineTrigger}
              disabled={isProcessing || !githubUrl || !repoName}
              className="bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 text-slate-950 disabled:text-slate-600 font-bold px-6 h-[32px] rounded transition-all tracking-wide text-[10px]"
            >
              {isProcessing ? 'SCANNING ENGINE...' : 'RUN PIPELINE LOOP'}
            </button>
          </div>
        </section>

        {/* Real-time Task Activity Log Tracker */}
        {isProcessing && (
          <div className="bg-slate-900 border border-amber-500/30 text-amber-400 p-3 rounded flex items-center gap-3 animate-pulse">
            <span className="h-2 w-2 rounded-full bg-amber-400"></span>
            <span>CONTAINER TRIGGERED: Checking Workspace ➔ Invoking Master Core Manifest Output...</span>
          </div>
        )}

        {/* Runtime Diagnostics Fault Handling Banner */}
        {runtimeError && (
          <div className="bg-rose-950/40 border border-rose-900 text-rose-300 rounded p-4 text-[11px] space-y-1">
            <span className="font-bold text-rose-400 block text-xs">Sandbox Environment Build Error:</span>
            <p className="opacity-90">{runtimeError}</p>
          </div>
        )}

        {/* Clean Schema Raw Text Screen Frame */}
        {rawSchemaText && !isProcessing && (
          <article className="space-y-2">
            <div className="bg-slate-900 border border-slate-800 rounded px-4 py-2 flex justify-between items-center text-[10px]">
              <span className="text-emerald-400 font-bold">✓ EXPORT VERIFIED: vault_workspace/{repoName}/sentinode_master_manifest.json</span>
              <span className="text-slate-500">Character Size Footprint: {rawSchemaText.length.toLocaleString()} bytes</span>
            </div>
            <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 shadow-2xl relative">
              <div className="absolute top-2 right-4 text-[9px] text-slate-600 font-bold tracking-widest select-none">
                RAW_MANIFEST_STRINGIFY_OUTPUT
              </div>
              <pre className="max-h-[66vh] overflow-y-auto text-emerald-300/90 font-mono text-[11px] leading-relaxed p-1 scrollbar-thin scrollbar-thumb-slate-800 scrollbar-track-transparent">
                <code>{rawSchemaText}</code>
              </pre>
            </div>
          </article>
        )}
      </div>
    </main>
  );
}
