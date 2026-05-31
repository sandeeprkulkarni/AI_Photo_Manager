// frontend/src/components/Deduplicator.tsx
import React, { useState } from "react";

export function Deduplicator() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [feedback, setFeedback] = useState("");

  const handleStartSorting = async () => {
    setIsProcessing(true);
    setFeedback("AI is processing photo variations across location records, blur coefficients, and light parameters...");
    try {
      const response = await fetch("http://localhost:8000/api/photos/deduplicate", {
        method: "POST",
      });
      const payload = await response.json();
      if (payload.status === "success") {
        setFeedback("Success! Best variations have been chosen, and inferior frames are now hidden from face tracking.");
      } else {
        setFeedback("Deduplication processing error occurred.");
      }
    } catch (error) {
      setFeedback("Failed to reach local application backend servers.");
    } finally {
      isProcessing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">AI Smart Sorting & Triage</h1>
        <p className="text-muted-foreground mt-1">
          Isolate repetitive shots and bursts to minimize downstream face processing workloads.
        </p>
      </div>

      <div className="p-6 border rounded-2xl bg-card max-w-xl shadow-sm">
        <h3 className="font-semibold text-base mb-3 text-foreground">AI Ranking Rules Breakdown</h3>
        <ul className="text-sm space-y-2 text-muted-foreground list-disc pl-5 mb-6">
          <li><strong>Location Context:</strong> Prioritizes frames containing valid EXIF mapping data.</li>
          <li><strong>People Counts:</strong> Higher score multiplier matches the volume of detected human subjects.</li>
          <li><strong>Blur Minimization:</strong> OpenCV Laplacian assessment penalizes motion blur artifacts.</li>
          <li><strong>Light Distribution:</strong> Grayscale brightness optimization ensures perfect contrast.</li>
        </ul>

        <button
          onClick={handleStartSorting}
          disabled={isProcessing}
          className="px-5 py-2.5 bg-primary text-primary-foreground font-medium rounded-xl text-sm transition-all hover:opacity-90 disabled:opacity-40"
        >
          {isProcessing ? "Analyzing Library Variants..." : "Sort & Triage Photos"}
        </button>

        {feedback && (
          <div className="mt-4 p-4 rounded-xl bg-muted text-sm text-foreground transition-all">
            {feedback}
          </div>
        )}
      </div>
    </div>
  );
}