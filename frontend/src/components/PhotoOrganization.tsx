import { useState } from "react";
import { Search, Filter, Grid3x3, CheckCircle2, User, MapPin, Calendar } from "lucide-react";
import { motion } from "motion/react";

const mockPhotos = Array.from({ length: 24 }, (_, i) => ({
  id: i + 1,
  hasLocation: i % 3 !== 0,
  hasPeople: i % 2 === 0,
  people: i % 2 === 0 ? ["Sarah Chen", "Michael Park"] : [],
  location: i % 3 !== 0 ? "San Francisco, CA" : undefined,
}));

export function PhotoOrganization() {
  const [selectedPhotos, setSelectedPhotos] = useState<number[]>([]);
  const [filterType, setFilterType] = useState<"all" | "people" | "location" | "untagged">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [processing, setProcessing] = useState(false);

  const filteredPhotos = mockPhotos.filter((photo) => {
    if (filterType === "people" && !photo.hasPeople) return false;
    if (filterType === "location" && !photo.hasLocation) return false;
    if (filterType === "untagged" && (photo.hasLocation || photo.hasPeople)) return false;
    return true;
  });

  const togglePhotoSelection = (id: number) => {
    setSelectedPhotos((prev) =>
      prev.includes(id) ? prev.filter((photoId) => photoId !== id) : [...prev, id]
    );
  };

  const handleBulkOrganize = () => {
    setProcessing(true);
    setTimeout(() => {
      setProcessing(false);
      setSelectedPhotos([]);
    }, 2000);
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="border-b border-border bg-card px-8 py-6">
        <div className="max-w-[1600px] mx-auto">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1>Photo Organization</h1>
              <p className="text-muted-foreground mt-1">
                {filteredPhotos.length} photos • {selectedPhotos.length} selected
              </p>
            </div>

            {selectedPhotos.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex gap-3"
              >
                <button
                  onClick={handleBulkOrganize}
                  disabled={processing}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
                >
                  {processing ? "Processing..." : "Organize Selected"}
                </button>
                <button
                  onClick={() => setSelectedPhotos([])}
                  className="px-4 py-2 border border-border rounded-lg hover:bg-accent transition-colors"
                >
                  Clear Selection
                </button>
              </motion.div>
            )}
          </div>

          {/* Filters */}
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search photos..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-input-background rounded-lg"
              />
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => setFilterType("all")}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  filterType === "all"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-foreground hover:bg-accent"
                }`}
              >
                All
              </button>
              <button
                onClick={() => setFilterType("people")}
                className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
                  filterType === "people"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-foreground hover:bg-accent"
                }`}
              >
                <User size={16} />
                People
              </button>
              <button
                onClick={() => setFilterType("location")}
                className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
                  filterType === "location"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-foreground hover:bg-accent"
                }`}
              >
                <MapPin size={16} />
                Location
              </button>
              <button
                onClick={() => setFilterType("untagged")}
                className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
                  filterType === "untagged"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-foreground hover:bg-accent"
                }`}
              >
                <Filter size={16} />
                Untagged
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Photo Grid */}
      <div className="flex-1 overflow-auto p-8">
        <div className="max-w-[1600px] mx-auto">
          <div className="grid grid-cols-6 gap-4">
            {filteredPhotos.map((photo) => (
              <PhotoCard
                key={photo.id}
                photo={photo}
                selected={selectedPhotos.includes(photo.id)}
                onToggle={() => togglePhotoSelection(photo.id)}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function PhotoCard({
  photo,
  selected,
  onToggle,
}: {
  photo: {
    id: number;
    hasLocation: boolean;
    hasPeople: boolean;
    people: string[];
    location?: string;
  };
  selected: boolean;
  onToggle: () => void;
}) {
  const [hovering, setHovering] = useState(false);

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className={`relative aspect-square rounded-lg overflow-hidden cursor-pointer ${
        selected ? "ring-2 ring-primary" : ""
      }`}
      onMouseEnter={() => setHovering(true)}
      onMouseLeave={() => setHovering(false)}
      onClick={onToggle}
    >
      <div className="w-full h-full bg-muted flex items-center justify-center">
        <Grid3x3 size={32} className="text-muted-foreground" />
      </div>

      {/* Overlay */}
      {(hovering || selected) && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent"
        >
          <div className="absolute bottom-0 left-0 right-0 p-3 text-white space-y-1">
            {photo.people.length > 0 && (
              <div className="flex items-center gap-1 text-xs">
                <User size={12} />
                {photo.people.join(", ")}
              </div>
            )}
            {photo.location && (
              <div className="flex items-center gap-1 text-xs">
                <MapPin size={12} />
                {photo.location}
              </div>
            )}
          </div>
        </motion.div>
      )}

      {/* Selection indicator */}
      {selected && (
        <div className="absolute top-2 right-2 w-6 h-6 bg-primary rounded-full flex items-center justify-center">
          <CheckCircle2 size={16} className="text-primary-foreground" />
        </div>
      )}
    </motion.div>
  );
}
