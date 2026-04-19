import { useState } from "react";
import { MapPin, ChevronRight, User, X } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

const mockLocations = [
  { id: 1, name: "San Francisco, CA", count: 847, people: ["Sarah Chen", "Michael Park"] },
  { id: 2, name: "New York, NY", count: 523, people: ["Emma Wilson"] },
  { id: 3, name: "Tokyo, Japan", count: 412, people: ["Sarah Chen", "Yuki Tanaka"] },
  { id: 4, name: "Paris, France", count: 298, people: ["Michael Park"] },
  { id: 5, name: "London, UK", count: 267, people: ["Emma Wilson", "Oliver Smith"] },
  { id: 6, name: "Barcelona, Spain", count: 189, people: ["Sarah Chen"] },
  { id: 7, name: "Sydney, Australia", count: 156, people: ["Liam Chen"] },
  { id: 8, name: "Amsterdam, Netherlands", count: 134, people: [] },
];

export function LocationGallery() {
  const [selectedLocation, setSelectedLocation] = useState<typeof mockLocations[0] | null>(null);

  return (
    <div className="p-8 max-w-[1400px] mx-auto">
      <div className="mb-8">
        <h1>Locations</h1>
        <p className="text-muted-foreground mt-2">
          {mockLocations.length} locations • {mockLocations.reduce((sum, loc) => sum + loc.count, 0)} photos
        </p>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {mockLocations.map((location) => (
          <LocationCard
            key={location.id}
            location={location}
            onClick={() => setSelectedLocation(location)}
          />
        ))}
      </div>

      {/* Detail Modal */}
      <AnimatePresence>
        {selectedLocation && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/60 z-40"
              onClick={() => setSelectedLocation(null)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="fixed inset-8 bg-card rounded-lg z-50 flex flex-col"
            >
              <div className="flex items-center justify-between p-6 border-b border-border">
                <div>
                  <h2>{selectedLocation.name}</h2>
                  <p className="text-sm text-muted-foreground mt-1">
                    {selectedLocation.count} photos
                  </p>
                </div>
                <button
                  onClick={() => setSelectedLocation(null)}
                  className="w-10 h-10 flex items-center justify-center hover:bg-accent rounded-lg transition-colors"
                >
                  <X size={20} />
                </button>
              </div>

              <div className="flex-1 overflow-auto p-6">
                <div className="grid grid-cols-5 gap-4">
                  {Array.from({ length: 20 }).map((_, i) => (
                    <div key={i} className="aspect-square bg-muted rounded-lg" />
                  ))}
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}

function LocationCard({
  location,
  onClick,
}: {
  location: { name: string; count: number; people: string[] };
  onClick: () => void;
}) {
  return (
    <motion.div
      whileHover={{ y: -4 }}
      className="border border-border rounded-lg overflow-hidden cursor-pointer group"
      onClick={onClick}
    >
      <div className="aspect-[4/3] bg-muted relative">
        <div className="absolute inset-0 grid grid-cols-2 gap-1 p-1">
          <div className="bg-muted-foreground/20 rounded" />
          <div className="bg-muted-foreground/20 rounded" />
          <div className="bg-muted-foreground/20 rounded" />
          <div className="bg-muted-foreground/20 rounded" />
        </div>
      </div>

      <div className="p-4">
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2">
            <MapPin size={16} className="text-primary" />
            <h3 className="text-sm">{location.name}</h3>
          </div>
          <ChevronRight size={16} className="text-muted-foreground group-hover:text-foreground transition-colors" />
        </div>

        <div className="text-sm text-muted-foreground mb-3">{location.count} photos</div>

        {location.people.length > 0 && (
          <div className="flex items-center gap-2">
            <User size={14} className="text-muted-foreground" />
            <div className="text-xs text-muted-foreground">
              {location.people.slice(0, 2).join(", ")}
              {location.people.length > 2 && ` +${location.people.length - 2}`}
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
}
