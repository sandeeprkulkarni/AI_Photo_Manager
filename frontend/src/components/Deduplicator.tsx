// frontend/src/components/Deduplicator.tsx
import React, { useState, useEffect, useRef } from "react";

interface DedupStatus {
  is_processing: boolean;
  current: number;
  total: number;
  duplicates_found: number;
  message: string;
}

export function Deduplicator() {
  const [folderPath, setFolderPath] = useState("");
  const [status, setStatus] = useState<DedupStatus>({
    is_processing: false,
    current: 0,
    total: 0,
    duplicates_found: 0,
    message: "System ready. Input a target directory folder path to evaluate.",
  });

  // Using standard number ID for browser environments to satisfy Vite/TypeScript
  const timerRef = useRef<number | null>(null);

  const pollStatus = async () => {
    try {
      const response = await fetch("/api/photos/deduplicate/status");
      const data = await response.json();
      setStatus(data);

      if (data.is_processing) {
        timerRef.current = window.setTimeout(pollStatus, 1000);
      }
    } catch (err) {
      console.error("Error polling deduplication progress state:", err);
    }
  };

  useEffect(() => {
    pollStatus();
    return () => {
      if (timerRef.current !== null) {
        window.clearTimeout(timerRef.current);
      }
    };
  }, []);

  const handleStartSorting = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!folderPath || !folderPath.trim()) {
      alert("Please provide a valid file system directory path first.");
      return;
    }

    try {
      const response = await fetch("/api/photos/deduplicate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ folder_path: folderPath.trim() }),
      });

      if (!response.ok) {
        const errData = await response.json();
        alert(errData.detail || "Failed to trigger sorting workspace optimization pass.");
        return;
      }

      pollStatus();
    } catch (error) {
      alert("Failed to communicate with local application backend.");
    }
  };

  const completionPercentage = status.total > 0 ? Math.round((status.current / status.total) * 100) : 0;

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">AI Smart Sorting & Triage</h1>
        <p className="text-muted-foreground mt-1">
          Provide a workspace folder path to group burst shots together and isolate low-quality matching frames.
        </p>
      </div>

      {/* Realtime Stats Grid Display */}
      <div className="grid grid-cols-2 gap-4">
        <div className="p-5 border rounded-2xl bg-card shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Photos Processed</p>
          <p className="text-2xl font-bold mt-1 text-foreground">
            {status.current} <span className="text-sm font-normal text-muted-foreground">/ {status.total}</span>
          </p>
        </div>
        <div className="p-5 border rounded-2xl bg-card shadow-sm border-amber-500/20 bg-amber-500/5">
          <p className="text-xs font-semibold uppercase tracking-wider text-amber-600 dark:text-amber-400">Duplicates Isolated</p>
          <p className="text-2xl font-bold mt-1 text-amber-600 dark:text-amber-400">{status.duplicates_found}</p>
        </div>
      </div>

      {/* Target Selection Folder Entry Panel */}
      <div className="p-6 border rounded-2xl bg-card shadow-sm space-y-4">
        <form onSubmit={handleStartSorting} className="space-y-3">
          <label className="block text-sm font-medium text-foreground">Target Directory Folder Path</label>
          <div className="flex gap-3">
            <input
              type="text"
              value={folderPath}
              onChange={(e) => setFolderPath(e.target.value)}
              disabled={status.is_processing}
              placeholder="E:/AI Practice/Photos"
              className="flex-1 min-w-0 px-4 py-2 bg-background border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={status.is_processing || !folderPath}
              className="px-5 py-2 bg-primary text-primary-foreground font-medium rounded-xl text-sm transition-all hover:opacity-90 disabled:opacity-40 whitespace-nowrap"
            >
              {status.is_processing ? "Processing..." : "Run AI Triage"}
            </button>
          </div>
        </form>

        {/* Live Loading Bar Progress Components */}
        {(status.is_processing || (status.total > 0 && status.current === status.total)) && (
          <div className="space-y-2 pt-2 border-t border-dashed">
            <div className="flex justify-between text-xs font-medium">
              <span className="text-muted-foreground">Evaluation Progress</span>
              <span className="text-foreground font-semibold">{completionPercentage}%</span>
            </div>
            <div className="w-full bg-muted h-2.5 rounded-full overflow-hidden">
              <div
                className="bg-primary h-full transition-all duration-300 ease-out"
                style={{ width: `${completionPercentage}%` }}
              />
            </div>
          </div>
        )}

        {/* Informative Status Message Strip */}
        {status.message && (
          <div className="p-4 rounded-xl bg-muted text-sm text-foreground transition-all">
            <div className="flex items-center gap-2">
              {status.is_processing && <span className="animate-spin text-xs">⏳</span>}
              <p className="font-medium">{status.message}</p>
            </div>
          </div>
        )}
      </div>

      {/* Static Multi Criteria Reference Breakdown */}
      <div className="p-5 border rounded-2xl bg-card shadow-sm bg-muted/30">
        <h3 className="font-semibold text-sm mb-2 text-foreground">AI Ranking Rules Applied</h3>
        <ul className="text-xs space-y-1.5 text-muted-foreground list-disc pl-5">
          <li><strong>Location Context:</strong> Prioritizes frames containing valid EXIF mapping data.</li>
          <li><strong>People Counts:</strong> Higher score multiplier matches the volume of detected human subjects.</li>
          <li><strong>Blur Minimization:</strong> OpenCV Laplacian assessment penalizes motion blur artifacts.</li>
          <li><strong>Light Distribution:</strong> Grayscale brightness optimization ensures perfect contrast.</li>
        </ul>
      </div>
    </div>
  );
}