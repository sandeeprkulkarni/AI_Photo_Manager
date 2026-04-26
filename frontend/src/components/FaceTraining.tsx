// src/components/FaceTraining.tsx
import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Upload, UserCheck, Search, RefreshCw, X } from 'lucide-react';
import { motion, AnimatePresence } from "motion/react";

export function FaceTraining() {
  const [name, setName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  
  // NEW: State to track which face is clicked from the grid
  const [selectedFace, setSelectedFace] = useState<any | null>(null); 
  
  const [loading, setLoading] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);
  const [detectedFaces, setDetectedFaces] = useState<any[]>([]);

  const fetchFaces = () => {
    fetch("http://localhost:8000/api/faces/unlabeled")
      .then(res => res.json())
      .then(data => setDetectedFaces(data))
      .catch(err => console.error("Error fetching faces:", err));
  };

  useEffect(() => {
    fetchFaces();
  }, []);

  const handleScanLibrary = async () => {
    setIsScanning(true);
    try {
      await fetch("http://localhost:8000/api/scan", { method: "POST" });
      fetchFaces();
    } catch (error) {
      console.error("Failed to scan library", error);
    } finally {
      setIsScanning(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) setFile(e.target.files[0]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // Validate inputs based on mode
    if (!name || (!file && !selectedFace)) return; 
    setLoading(true);

    const formData = new FormData();
    formData.append("name", name);

    try {
      let response;
      
      // BRANCH LOGIC: Are we labeling an existing face, or uploading a new one?
      if (selectedFace) {
        // Mode 1: Labeling a clicked face
        response = await fetch(`http://localhost:8000/api/faces/${selectedFace.id}/label`, {
          method: "POST",
          body: formData,
        });
      } else if (file) {
        // Mode 2: Uploading a new photo
        formData.append("file", file);
        response = await fetch("http://localhost:8000/api/train", { 
          method: "POST", 
          body: formData 
        });
      }

      const data = await response?.json();
      setMessage({ type: data.status === "success" ? 'success' : 'error', text: data.message });
      
      if (data.status === "success") { 
        setName(""); 
        setFile(null);
        setSelectedFace(null); // Clear selection
        fetchFaces(); // Refresh the grid (the named face will disappear!)
      }
    } catch (error) {
      setMessage({ type: 'error', text: "Backend server connection failed." });
    } finally { 
      setLoading(false); 
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <header className="mb-8 flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-bold">Face Detection Module</h2>
          <p className="text-muted-foreground mt-1">Manage identities and review detected clusters.</p>
        </div>
        
        <Button 
          onClick={handleScanLibrary} 
          disabled={isScanning}
          variant="outline" 
          className="gap-2 rounded-xl h-10"
        >
          <RefreshCw className={`w-4 h-4 ${isScanning ? 'animate-spin' : ''}`} />
          {isScanning ? 'Scanning Directory...' : 'Scan Library'}
        </Button>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        
        {/* Left Column: Contextual Training Form */}
        <div className="lg:col-span-1 sticky top-6">
          <Card className={`border-border shadow-sm transition-colors ${selectedFace ? 'ring-2 ring-primary' : ''}`}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-primary">
                <UserCheck className="w-5 h-5" /> 
                {selectedFace ? "Assign Name to Face" : "Train New Identity"}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                
                {/* DYNAMIC IMAGE AREA */}
                <div className="space-y-2">
                  <Label>{selectedFace ? "Selected Face" : "Training Image"}</Label>
                  <AnimatePresence mode="wait">
                    {selectedFace ? (
                      // SHOW SELECTED FACE
                      <motion.div 
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        className="relative w-full h-48 rounded-2xl overflow-hidden bg-muted/30 border border-border"
                      >
                        <img 
                          src={`http://localhost:8000${selectedFace.url}`} 
                          alt="Selected face" 
                          className="w-full h-full object-contain"
                        />
                        <Button
                          type="button"
                          variant="destructive"
                          size="icon"
                          className="absolute top-2 right-2 h-8 w-8 rounded-full"
                          onClick={() => setSelectedFace(null)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </motion.div>
                    ) : (
                      // SHOW UPLOAD BOX
                      <motion.label 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="flex flex-col items-center justify-center w-full h-40 border-2 border-dashed rounded-2xl cursor-pointer bg-muted/30 hover:bg-muted/50 border-border transition-colors"
                      >
                        <div className="flex flex-col items-center justify-center pt-5 pb-6 px-4 text-center">
                          <Upload className="w-10 h-10 mb-3 text-muted-foreground/60" />
                          <p className="text-sm text-muted-foreground line-clamp-2">
                            {file ? file.name : "Upload a clear photo"}
                          </p>
                        </div>
                        <input type="file" className="hidden" accept="image/*" onChange={handleFileChange} />
                      </motion.label>
                    )}
                  </AnimatePresence>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="name">Full Name</Label>
                  <Input 
                    id="name" 
                    value={name} 
                    onChange={(e) => setName(e.target.value)} 
                    placeholder="e.g. Sarah Chen" 
                    required 
                    autoFocus={!!selectedFace} // Auto-focus input when face is clicked
                  />
                </div>
                
                {message && (
                  <div className={`p-4 rounded-xl flex items-center gap-3 ${message.type === 'success' ? 'bg-green-500/10 text-green-600' : 'bg-red-500/10 text-red-600'}`}>
                    <span className="text-sm font-medium">{message.text}</span>
                  </div>
                )}
                
                <Button 
                  type="submit" 
                  className="w-full h-12 rounded-xl" 
                  disabled={loading || !name || (!file && !selectedFace)}
                >
                  {loading ? "Processing..." : (selectedFace ? "Assign Name" : "Train Model")}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Detected Faces Grid */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-semibold flex items-center gap-3">
              Unidentified Faces
              <span className="bg-primary/10 text-primary text-xs px-3 py-1 rounded-full font-medium">
                {detectedFaces.length} found
              </span>
            </h3>
            <p className="text-sm text-muted-foreground">Click a face to label it</p>
          </div>

          <div className="bg-card border rounded-2xl p-6 shadow-sm min-h-[500px]">
            <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
              {detectedFaces.length > 0 ? (
                detectedFaces.map((face: any) => (
                  <motion.div 
                    key={face.id} 
                    whileHover={{ y: -4 }} 
                    onClick={() => setSelectedFace(face)} // NEW: Click handler
                    className={`group relative bg-muted/30 border-2 rounded-2xl overflow-hidden shadow-sm aspect-square cursor-pointer transition-all ${
                      selectedFace?.id === face.id ? 'border-primary ring-2 ring-primary/50' : 'border-transparent'
                    }`}
                  >
                    <img 
                      src={`http://localhost:8000${face.url}`} 
                      alt="Face cluster" 
                      className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105" 
                      loading="lazy"
                    />
                    <div className={`absolute inset-x-0 bottom-0 p-2 transition-colors ${
                      selectedFace?.id === face.id ? 'bg-primary' : 'bg-gradient-to-t from-black/80 to-transparent'
                    }`}>
                      <p className="text-[10px] text-center text-white/90 font-mono">
                        {selectedFace?.id === face.id ? 'Selected' : `Cluster: ${face.cluster}`}
                      </p>
                    </div>
                  </motion.div>
                ))
              ) : (
                <div className="col-span-full flex flex-col items-center justify-center py-24 text-center text-muted-foreground">
                  <Search className="w-16 h-16 mb-4 opacity-20" />
                  <p className="font-medium text-foreground">No faces detected yet.</p>
                  <p className="text-sm opacity-80 mt-1">Click "Scan Library" above to search your photos.</p>
                </div>
              )}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}