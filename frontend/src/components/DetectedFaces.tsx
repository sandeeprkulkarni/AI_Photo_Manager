// src/components/DetectedFaces.tsx
import { useEffect, useState } from "react";
import { motion } from "motion/react";

export function DetectedFaces() {
  const [faces, setFaces] = useState([]);

  useEffect(() => {
    fetch("http://localhost:8000/api/faces")
      .then(res => res.json())
      .then(data => setFaces(data));
  }, []);

  return (
    <div className="space-y-8">
      <header>
        <h2 className="text-3xl font-bold">Detected Faces</h2>
        <p className="text-muted-foreground">Faces found across your 500GB library, grouped by similarity.</p>
      </header>

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {faces.map((face: any) => (
          <motion.div 
            key={face.id}
            whileHover={{ scale: 1.05 }}
            className="aspect-square bg-card border rounded-xl overflow-hidden shadow-sm"
          >
            <img 
              src={`http://localhost:8000${face.url}`} 
              alt="Detected Face"
              className="w-full h-full object-cover"
              onError={(e) => (e.currentTarget.src = "https://via.placeholder.com/150?text=No+Image")}
            />
            <div className="p-2 text-[10px] text-center bg-background/80 font-mono">
              Cluster: {face.cluster}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}