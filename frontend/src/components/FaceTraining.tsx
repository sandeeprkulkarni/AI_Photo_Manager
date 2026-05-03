import React, { useState, useEffect } from 'react';
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Card, CardContent } from "./ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { FolderSearch, CheckCircle2, Loader2, XCircle } from "lucide-react";
import { Progress } from "./ui/progress"; 
import { UnidentifiedPhotos } from "./UnidentifiedPhotos";

interface LabeledFace {
  name: string;
  image: string;
}

export const FaceTraining = () => {
  const [folderPath, setFolderPath] = useState("");
  const [isScanning, setIsScanning] = useState(false);
  const [scanStats, setScanStats] = useState({ current: 0, total: 0, message: "" }); 
  const [labeledFaces, setLabeledFaces] = useState<LabeledFace[]>([]);
  const [refreshKey, setRefreshKey] = useState(0); 

  const fetchLabeledFaces = async () => {
    try {
      // FIX: Added timestamp here as well so your new tags always appear instantly!
      const response = await fetch(`/api/faces/labeled?t=${Date.now()}`);
      const text = await response.text(); 
      if (!text) return; 
      
      const data = JSON.parse(text);
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

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isScanning) {
      interval = setInterval(async () => {
        try {
          const res = await fetch('/api/scan/status');
          const data = await res.json();
          
          if (data.is_scanning === false) {
            setIsScanning(false);
            setScanStats({ current: 0, total: 0, message: "" });
            fetchLabeledFaces(); 
            setRefreshKey(prev => prev + 1); 
          } else {
            setScanStats({
              current: data.current || 0,
              total: data.total || 0,
              message: data.message || "Scanning..."
            });
          }
        } catch (e) {
          console.error("Failed to fetch scan status", e);
        }
      }, 1000); 
    }
    return () => clearInterval(interval);
  }, [isScanning]);

  const handleScan = async () => {
    if (!folderPath) return;
    setIsScanning(true); 
    setScanStats({ current: 0, total: 0, message: "Initializing scan..." });
    
    try {
      const response = await fetch('/api/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folder_path: folderPath })
      });
      if (!response.ok) {
        setIsScanning(false);
        throw new Error("Scan failed to start");
      }
      setFolderPath(""); 
    } catch (error) {
      console.error(error);
      alert("Error starting the scan. Please check the folder path.");
      setIsScanning(false);
    }
  };

  const handleCancel = async () => {
    try {
      await fetch('/api/scan/cancel', { method: 'POST' });
      setScanStats(prev => ({ ...prev, message: "Cancelling scan..." }));
    } catch (error) {
      console.error("Failed to cancel", error);
    }
  };

  const progressPercent = scanStats.total > 0 
    ? Math.round((scanStats.current / scanStats.total) * 100) 
    : 0;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-8 text-slate-900 dark:text-slate-50">
      <Card className="bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-800 overflow-hidden">
        <CardContent className="p-6 flex flex-col gap-4">
          <div className="flex flex-col sm:flex-row items-end gap-4 w-full">
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
                disabled={isScanning}
              />
            </div>
            
            {isScanning ? (
              <Button 
                onClick={handleCancel} 
                variant="destructive"
                className="w-full sm:w-auto min-w-[140px]"
              >
                <XCircle className="w-4 h-4 mr-2" /> Cancel Scan
              </Button>
            ) : (
              <Button 
                onClick={handleScan} 
                disabled={!folderPath}
                className="w-full sm:w-auto min-w-[140px]"
              >
                <FolderSearch className="w-4 h-4 mr-2" /> Start Scan
              </Button>
            )}
          </div>

          {isScanning && (
            <div className="mt-4 space-y-3 animate-in fade-in slide-in-from-top-4 duration-500">
              <div className="flex justify-between items-end text-sm font-medium">
                <span className="text-slate-600 dark:text-slate-400 truncate pr-4">
                  {scanStats.message}
                </span>
                {scanStats.total > 0 && (
                  <span className="text-blue-600 dark:text-blue-400 whitespace-nowrap">
                    {scanStats.current} / {scanStats.total} ({progressPercent}%)
                  </span>
                )}
              </div>
              <Progress value={progressPercent} className="w-full h-2 bg-slate-200 dark:bg-slate-800" />
            </div>
          )}
        </CardContent>
      </Card>

      <Tabs defaultValue="unidentified" className="w-full">
        <TabsList className="grid w-full sm:w-[400px] grid-cols-2">
          <TabsTrigger value="unidentified">Unidentified Faces</TabsTrigger>
          <TabsTrigger value="named" onClick={fetchLabeledFaces}>
            Named People
          </TabsTrigger>
        </TabsList>

        <TabsContent value="unidentified" className="mt-6">
          <UnidentifiedPhotos refreshTrigger={refreshKey} />
        </TabsContent>

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
                  <div className="w-24 h-24 rounded-full overflow-hidden bg-slate-100 border-2 border-slate-200 dark:border-slate-700 flex-shrink-0">
                    <img 
                      src={face.image} 
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
};

export default FaceTraining;