import { useState } from "react";
import { AlertCircle, UserX, MapPinOff, Grid3x3, Send } from "lucide-react";
import { Link } from "react-router";

const mockUnidentified = Array.from({ length: 18 }, (_, i) => ({
  id: i + 1,
  reason: i % 3 === 0 ? "no-face" : i % 3 === 1 ? "no-location" : "no-event",
}));

const reasonLabels = {
  "no-face": "Face not recognized",
  "no-location": "Location unavailable",
  "no-event": "Event not detected",
};

const reasonIcons = {
  "no-face": UserX,
  "no-location": MapPinOff,
  "no-event": AlertCircle,
};

export function UnidentifiedPhotos() {
  const [selectedPhotos, setSelectedPhotos] = useState<number[]>([]);
  const [filterReason, setFilterReason] = useState<string | null>(null);

  const filteredPhotos = filterReason
    ? mockUnidentified.filter((p) => p.reason === filterReason)
    : mockUnidentified;

  const toggleSelection = (id: number) => {
    setSelectedPhotos((prev) =>
      prev.includes(id) ? prev.filter((photoId) => photoId !== id) : [...prev, id]
    );
  };

  const reasonCounts = {
    "no-face": mockUnidentified.filter((p) => p.reason === "no-face").length,
    "no-location": mockUnidentified.filter((p) => p.reason === "no-location").length,
    "no-event": mockUnidentified.filter((p) => p.reason === "no-event").length,
  };

  return (
    <div className="h-full flex flex-col">
      <div className="border-b border-border bg-card px-8 py-6">
        <div className="max-w-[1400px] mx-auto">
          <div className="mb-6">
            <h1>Unidentified Photos</h1>
            <p className="text-muted-foreground mt-1">
              {filteredPhotos.length} photos need review
            </p>
          </div>

          {/* Filter chips */}
          <div className="flex gap-3 mb-6">
            <button
              onClick={() => setFilterReason(null)}
              className={`px-4 py-2 rounded-lg transition-colors ${
                filterReason === null
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted hover:bg-accent"
              }`}
            >
              All ({mockUnidentified.length})
            </button>
            {Object.entries(reasonCounts).map(([reason, count]) => {
              const Icon = reasonIcons[reason as keyof typeof reasonIcons];
              return (
                <button
                  key={reason}
                  onClick={() => setFilterReason(reason)}
                  className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
                    filterReason === reason
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted hover:bg-accent"
                  }`}
                >
                  <Icon size={16} />
                  {reasonLabels[reason as keyof typeof reasonLabels]} ({count})
                </button>
              );
            })}
          </div>

          {selectedPhotos.length > 0 && (
            <div className="flex items-center gap-3 p-4 bg-primary/10 rounded-lg">
              <div className="flex-1">
                {selectedPhotos.length} photos selected
              </div>
              <Link
                to="/train"
                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity flex items-center gap-2"
              >
                <Send size={16} />
                Send to Training
              </Link>
              <button
                onClick={() => setSelectedPhotos([])}
                className="px-4 py-2 border border-border rounded-lg hover:bg-accent transition-colors"
              >
                Clear
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-auto p-8">
        <div className="max-w-[1400px] mx-auto">
          <div className="grid grid-cols-6 gap-4">
            {filteredPhotos.map((photo) => {
              const Icon = reasonIcons[photo.reason as keyof typeof reasonIcons];
              const isSelected = selectedPhotos.includes(photo.id);

              return (
                <div
                  key={photo.id}
                  onClick={() => toggleSelection(photo.id)}
                  className={`aspect-square rounded-lg overflow-hidden cursor-pointer border-2 transition-all ${
                    isSelected ? "border-primary" : "border-border hover:border-primary/50"
                  }`}
                >
                  <div className="relative w-full h-full bg-muted flex flex-col items-center justify-center gap-2">
                    <Grid3x3 size={32} className="text-muted-foreground" />
                    <div className="absolute bottom-2 left-2 right-2 flex items-center gap-1 text-xs text-muted-foreground bg-background/80 px-2 py-1 rounded">
                      <Icon size={12} />
                      <span className="truncate">{reasonLabels[photo.reason as keyof typeof reasonLabels]}</span>
                    </div>
                    {isSelected && (
                      <div className="absolute inset-0 bg-primary/20 flex items-center justify-center">
                        <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
                          <AlertCircle size={16} className="text-primary-foreground" />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
