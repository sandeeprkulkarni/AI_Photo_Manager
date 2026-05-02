import React, { useState, useEffect } from 'react';
import { Card, CardContent } from "./ui/card";
import { Input } from "./ui/input";
import { Button } from "./ui/button";
import { Check, UserPlus, Loader2, CheckCircle2 } from "lucide-react";

interface UnlabeledFace {
  id: number;
  image: string; 
}

interface UnidentifiedPhotosProps {
  refreshTrigger?: number;
}

export const UnidentifiedPhotos: React.FC<UnidentifiedPhotosProps> = ({ refreshTrigger = 0 }) => {
  const [faces, setFaces] = useState<UnlabeledFace[]>([]);
  const [loading, setLoading] = useState(true);
  const [trainingId, setTrainingId] = useState<number | null>(null);
  const [nameInputs, setNameInputs] = useState<{ [key: number]: string }>({});

  const fetchUnlabeledFaces = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/faces/unlabeled');
      const data = await response.json();
      if (data.status === 'success') {
        setFaces(data.faces);
      }
    } catch (error) {
      console.error("Failed to fetch unlabeled faces:", error);
    } finally {
      setLoading(false);
    }
  };

  // Re-fetch when the refreshTrigger changes (e.g., scan completes)
  useEffect(() => {
    fetchUnlabeledFaces();
  }, [refreshTrigger]);

  const handleNameChange = (id: number, value: string) => {
    setNameInputs(prev => ({ ...prev, [id]: value }));
  };

  const handleTrainFace = async (faceId: number) => {
    const nameToAssign = nameInputs[faceId];
    if (!nameToAssign || nameToAssign.trim() === "") return;

    setTrainingId(faceId);
    
    try {
      const response = await fetch('/api/train', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ face_id: faceId, name: nameToAssign.trim() })
      });

      if (response.ok) {
        setFaces(prev => prev.filter(face => face.id !== faceId));
        const newInputs = { ...nameInputs };
        delete newInputs[faceId];
        setNameInputs(newInputs);
      } else {
        alert("Failed to train face. Please try again.");
      }
    } catch (error) {
      console.error("Training error:", error);
    } finally {
      setTrainingId(null);
    }
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center text-slate-500">
        <Loader2 className="h-8 w-8 animate-spin mr-2" />
        <span>Finding unidentified faces...</span>
      </div>
    );
  }

  if (faces.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-slate-500">
        <CheckCircle2 className="w-12 h-12 mb-4 text-green-500 opacity-80" />
        <h3 className="text-lg font-medium text-slate-700 dark:text-slate-300">All caught up!</h3>
        <p>No unidentified faces found. Try scanning more photos.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
      {faces.map((face) => (
        <Card key={face.id} className="overflow-hidden bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:shadow-lg transition-all group">
          
          <div className="aspect-square relative bg-slate-100 dark:bg-slate-800">
            <img 
              src={`/api/image?path=${encodeURIComponent(face.image)}`} 
              alt="Unidentified face" 
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-3">
               <span className="text-white text-xs font-medium flex items-center">
                 <UserPlus className="w-3 h-3 mr-1" /> Who is this?
               </span>
            </div>
          </div>

          <CardContent className="p-3 bg-slate-50 dark:bg-slate-950">
            <div className="flex gap-2">
              <Input 
                placeholder="Enter name..." 
                className="h-9 text-sm bg-white dark:bg-slate-900 focus-visible:ring-1"
                value={nameInputs[face.id] || ""}
                onChange={(e) => handleNameChange(face.id, e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleTrainFace(face.id);
                }}
                disabled={trainingId === face.id}
              />
              <Button 
                size="icon" 
                className="h-9 w-9 shrink-0" 
                onClick={() => handleTrainFace(face.id)}
                disabled={!nameInputs[face.id] || trainingId === face.id}
              >
                {trainingId === face.id ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Check className="h-4 w-4" />
                )}
              </Button>
            </div>
          </CardContent>
          
        </Card>
      ))}
    </div>
  );
};