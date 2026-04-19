import { useState } from "react";
import { Brain, User, MapPin, Calendar, Trash2, RefreshCw } from "lucide-react";

const trainedFaces = [
  { id: 1, name: "Sarah Chen", photoCount: 234 },
  { id: 2, name: "Michael Park", photoCount: 187 },
  { id: 3, name: "Emma Wilson", photoCount: 156 },
  { id: 4, name: "Yuki Tanaka", photoCount: 98 },
  { id: 5, name: "Oliver Smith", photoCount: 76 },
  { id: 6, name: "Liam Chen", photoCount: 54 },
];

export function Settings() {
  const [aiSettings, setAiSettings] = useState({
    faceRecognition: true,
    locationDetection: true,
    eventClassification: true,
  });

  const toggleSetting = (key: keyof typeof aiSettings) => {
    setAiSettings((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="p-8 max-w-[1000px] mx-auto">
      <div className="mb-8">
        <h1>Settings</h1>
        <p className="text-muted-foreground mt-2">Manage AI features and trained data</p>
      </div>

      {/* AI Configuration */}
      <div className="mb-12">
        <div className="flex items-center gap-2 mb-4">
          <Brain size={20} />
          <h2>AI Features</h2>
        </div>

        <div className="space-y-3">
          <SettingToggle
            icon={User}
            label="Face Recognition"
            description="Automatically detect and recognize people in photos"
            enabled={aiSettings.faceRecognition}
            onToggle={() => toggleSetting("faceRecognition")}
          />
          <SettingToggle
            icon={MapPin}
            label="Location Detection"
            description="Extract location data from photo metadata"
            enabled={aiSettings.locationDetection}
            onToggle={() => toggleSetting("locationDetection")}
          />
          <SettingToggle
            icon={Calendar}
            label="Event Classification"
            description="Group photos by detected events and occasions"
            enabled={aiSettings.eventClassification}
            onToggle={() => toggleSetting("eventClassification")}
          />
        </div>
      </div>

      {/* Trained Faces */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <User size={20} />
            <h2>Trained Faces</h2>
          </div>
          <button className="px-4 py-2 border border-border rounded-lg hover:bg-accent transition-colors text-sm flex items-center gap-2">
            <RefreshCw size={16} />
            Retrain All
          </button>
        </div>

        <div className="border border-border rounded-lg divide-y divide-border">
          {trainedFaces.map((face) => (
            <div key={face.id} className="flex items-center gap-4 p-4 hover:bg-accent/50 transition-colors">
              <div className="w-12 h-12 bg-muted rounded-full flex items-center justify-center">
                <User size={20} className="text-muted-foreground" />
              </div>
              <div className="flex-1">
                <div className="font-medium">{face.name}</div>
                <div className="text-sm text-muted-foreground">{face.photoCount} photos</div>
              </div>
              <button className="p-2 hover:bg-destructive/10 hover:text-destructive rounded-lg transition-colors">
                <Trash2 size={16} />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function SettingToggle({
  icon: Icon,
  label,
  description,
  enabled,
  onToggle,
}: {
  icon: React.ElementType;
  label: string;
  description: string;
  enabled: boolean;
  onToggle: () => void;
}) {
  return (
    <div className="flex items-center gap-4 p-4 border border-border rounded-lg">
      <div className="p-2 bg-primary/10 rounded-lg">
        <Icon size={20} className="text-primary" />
      </div>
      <div className="flex-1">
        <div className="font-medium">{label}</div>
        <div className="text-sm text-muted-foreground">{description}</div>
      </div>
      <button
        onClick={onToggle}
        className={`relative w-12 h-6 rounded-full transition-colors ${
          enabled ? "bg-primary" : "bg-muted"
        }`}
      >
        <div
          className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
            enabled ? "translate-x-7" : "translate-x-1"
          }`}
        />
      </button>
    </div>
  );
}
