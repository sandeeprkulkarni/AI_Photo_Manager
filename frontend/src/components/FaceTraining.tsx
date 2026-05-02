import React, { useState, useEffect } from 'react';
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Card, CardContent } from "./ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { FolderSearch, CheckCircle2 } from "lucide-react";
import UnidentifiedPhotos from "./UnidentifiedPhotos";

// Define the type for our named faces
interface LabeledFace {
  name: string;
  image: string;
}

export default function FaceTraining() {
  const [folderPath, setFolderPath] = useState("");
  const [isScanning, setIsScanning] = useState(false);
  const [labeledFaces, setLabeledFaces] = useState<LabeledFace[]>([]);

  // Fetch the labeled faces when the component mounts or when tabs switch
  const fetchLabeledFaces = async () => {
    try {
      const response = await fetch('/api/faces/labeled');
      const data = await response.json();
      if (data.status === 'success') {
        setLabeledFaces(data.faces);
      }
    } catch (error) {
      console.error("Failed to fetch labeled faces:", error);
    }
  };

  useEffect(() => {
    fetchLabeledFaces();
  }, []);

  const handleScan = async () => {
    if (!folderPath) return;
    setIsScanning(true);
    
    try {
      const response = await fetch('/api/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folder_path: folderPath })
      });
      
      if (!response.ok) throw new Error("Scan failed to start");
      
      alert("Scanning started! Photos and faces will appear in the system shortly.");
      setFolderPath(""); // Clear input on success
    } catch (error) {
      console.error(error);
      alert("Error starting the scan. Please check the folder path.");
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-8 text-slate-900 dark:text-slate-50">
      
      {/* --- Section 1: Folder Scanning --- */}
      <Card className="bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-800">
        <CardContent className="p-6 flex flex-col sm:flex-row items-end gap-4">
          <div className="flex-1 w-full space-y-2">
            <label htmlFor="folderPath" className="text-sm font-semibold">
              Scan New Folder
            </label>
            <Input 
              id="folderPath"
              placeholder="e.g., C:/Users/Photos/WhatsApp Images" 
              value={folderPath}
              onChange={(e) => setFolderPath(e.target.value)}
              className="w-full bg-white dark:bg-slate-950"
            />
          </div>
          <Button 
            onClick={handleScan} 
            disabled={!folderPath || isScanning}
            className="w-full sm:w-auto"
          >
            <FolderSearch className="w-4 h-4 mr-2" />
            {isScanning ? "Scanning..." : "Start Scan"}
          </Button>
        </CardContent>
      </Card>

      {/* --- Section 2: Face Management Tabs --- */}
      <Tabs defaultValue="unidentified" className="w-full">
        <TabsList className="grid w-full sm:w-[400px] grid-cols-2">
          <TabsTrigger value="unidentified">Unidentified Faces</TabsTrigger>
          <TabsTrigger value="named" onClick={fetchLabeledFaces}>
            Named People
          </TabsTrigger>
        </TabsList>

        {/* Tab 1: Your existing Unidentified Faces UI */}
        <TabsContent value="unidentified" className="mt-6">
          <UnidentifiedPhotos />
        </TabsContent>

        {/* Tab 2: The New "Named Faces" Gallery */}
        <TabsContent value="named" className="mt-6">
          {labeledFaces.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-24 text-slate-500">
              <CheckCircle2 className="w-12 h-12 mb-4 opacity-50" />
              <p>You haven't named anyone yet.</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {labeledFaces.map((face, index) => (
                <div key={index} className="flex flex-col items-center space-y-3 p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl hover:shadow-md transition-shadow">
                  <div className="w-24 h-24 rounded-full overflow-hidden bg-slate-100 border-2 border-slate-200 dark:border-slate-700">
                    {/* Note: Ensure your backend serves local files via a static route, or convert to base64 if needed */}
                    <img 
                      src={`/api/image?path=${encodeURIComponent(face.image)}`} 
                      alt={face.name} 
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <span className="font-medium text-sm truncate w-full text-center">
                    {face.name}
                  </span>
                </div>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}