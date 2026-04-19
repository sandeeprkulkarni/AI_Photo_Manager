import { useState } from "react";
import { Calendar, ChevronRight, Users, X } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

const mockEvents = [
  { id: 1, name: "Summer Wedding 2025", type: "Wedding", date: "Jun 15, 2025", count: 342, attendees: 12 },
  { id: 2, name: "Tech Conference", type: "Conference", date: "Mar 22, 2025", count: 187, attendees: 8 },
  { id: 3, name: "Birthday Party", type: "Party", date: "Feb 8, 2025", count: 156, attendees: 6 },
  { id: 4, name: "Music Festival", type: "Festival", date: "Aug 12, 2024", count: 289, attendees: 4 },
  { id: 5, name: "Holiday Gathering", type: "Party", date: "Dec 25, 2024", count: 203, attendees: 15 },
  { id: 6, name: "Graduation Ceremony", type: "Ceremony", date: "May 18, 2024", count: 178, attendees: 9 },
];

const eventColors = {
  Wedding: "bg-pink-500/10 text-pink-700 dark:text-pink-400",
  Conference: "bg-blue-500/10 text-blue-700 dark:text-blue-400",
  Party: "bg-purple-500/10 text-purple-700 dark:text-purple-400",
  Festival: "bg-orange-500/10 text-orange-700 dark:text-orange-400",
  Ceremony: "bg-green-500/10 text-green-700 dark:text-green-400",
};

export function EventGallery() {
  const [selectedEvent, setSelectedEvent] = useState<typeof mockEvents[0] | null>(null);

  return (
    <div className="p-8 max-w-[1400px] mx-auto">
      <div className="mb-8">
        <h1>Events</h1>
        <p className="text-muted-foreground mt-2">
          {mockEvents.length} events • {mockEvents.reduce((sum, evt) => sum + evt.count, 0)} photos
        </p>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {mockEvents.map((event) => (
          <EventCard
            key={event.id}
            event={event}
            onClick={() => setSelectedEvent(event)}
          />
        ))}
      </div>

      {/* Detail Modal */}
      <AnimatePresence>
        {selectedEvent && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/60 z-40"
              onClick={() => setSelectedEvent(null)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="fixed inset-8 bg-card rounded-lg z-50 flex flex-col"
            >
              <div className="flex items-center justify-between p-6 border-b border-border">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <h2>{selectedEvent.name}</h2>
                    <span
                      className={`px-2 py-1 rounded text-xs ${
                        eventColors[selectedEvent.type as keyof typeof eventColors]
                      }`}
                    >
                      {selectedEvent.type}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {selectedEvent.date} • {selectedEvent.count} photos • {selectedEvent.attendees} people
                  </p>
                </div>
                <button
                  onClick={() => setSelectedEvent(null)}
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

function EventCard({
  event,
  onClick,
}: {
  event: { name: string; type: string; date: string; count: number; attendees: number };
  onClick: () => void;
}) {
  return (
    <motion.div
      whileHover={{ y: -4 }}
      className="border border-border rounded-lg overflow-hidden cursor-pointer group"
      onClick={onClick}
    >
      <div className="aspect-[4/3] bg-muted relative">
        <div className="absolute inset-0 flex items-center justify-center">
          <Calendar size={48} className="text-muted-foreground/40" />
        </div>
      </div>

      <div className="p-4">
        <div className="flex items-start justify-between mb-2">
          <div>
            <h3 className="text-sm mb-1">{event.name}</h3>
            <span
              className={`px-2 py-0.5 rounded text-xs ${
                eventColors[event.type as keyof typeof eventColors]
              }`}
            >
              {event.type}
            </span>
          </div>
          <ChevronRight size={16} className="text-muted-foreground group-hover:text-foreground transition-colors" />
        </div>

        <div className="text-xs text-muted-foreground mb-3">{event.date}</div>

        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <div>{event.count} photos</div>
          <div className="flex items-center gap-1">
            <Users size={14} />
            {event.attendees} people
          </div>
        </div>
      </div>
    </motion.div>
  );
}
