import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Upload, UserCheck, AlertCircle, Search } from 'lucide-react';
import { motion } from "motion/react";

const FaceTraining = () => {
  const [name, setName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);
  const [detectedFaces, setDetectedFaces] = useState([]);

  // Fetch detected faces from your Python backend
  useEffect(() => {
    fetch("http://localhost:8000/api/stats") // Replace with actual /api/faces/unlabeled endpoint when ready
      .then(res => res.json())
      .then(data => setDetectedFaces([])) // This will populate once you add the endpoint to server.py
      .catch(err => console.error("Error fetching faces:", err));
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !file) return;

    setLoading(true);
    setMessage(null);

    const formData = new FormData();
    formData.append("name", name);
    formData.append("file", file);

    try {
      const response = await fetch("/api/train", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      if (data.status === "success") {
        setMessage({ type: 'success', text: data.message });
        setName("");
        setFile(null);
      } else {
        setMessage({ type: 'error', text: data.message });
      }
    } catch (error) {
      setMessage({ type: 'error', text: "Failed to connect to backend server." });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <header>
        <h2 className="text-3xl font-bold tracking-tight">Face Detection Module</h2>
        <p className="text-muted-foreground mt-1">Manage and train identities for your 500GB library.</p>
      </header>

      <Tabs defaultValue="training" className="w-full">
        {/* MATCH FIGMA: Sub-tabs inside the module */}
        <TabsList className="grid w-full max-w-md grid-cols-2 mb-8">
          <TabsTrigger value="training">Training Model</TabsTrigger>
          <TabsTrigger value="detected">Detected Faces</TabsTrigger>
        </TabsList>

        <TabsContent value="training">
          <Card className="max-w-2xl mx-auto border-border shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-primary">
                <UserCheck className="w-5 h-5" />
                Train New Identity
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="name">Full Name</Label>
                  <Input id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. John Doe" required />
                </div>

                <div className="space-y-2">
                  <Label>Training Image</Label>
                  <label className="flex flex-col items-center justify-center w-full h-40 border-2 border-dashed rounded-2xl cursor-pointer bg-muted/30 hover:bg-muted/50 transition-all border-border">
                    <div className="flex flex-col items-center justify-center pt-5 pb-6">
                      <Upload className="w-10 h-10 mb-3 text-muted-foreground/60" />
                      <p className="text-sm text-muted-foreground">
                        {file ? file.name : "Upload a clear face photo"}
                      </p>
                    </div>
                    <input type="file" className="hidden" accept="image/*" onChange={handleFileChange} required />
                  </label>
                </div>

                {message && (
                  <div className={`p-4 rounded-xl flex items-center gap-3 ${
                    message.type === 'success' ? 'bg-green-500/10 text-green-600' : 'bg-red-500/10 text-red-600'
                  }`}>
                    {message.type === 'error' && <AlertCircle className="w-4 h-4" />}
                    <span className="text-sm font-medium">{message.text}</span>
                  </div>
                )}

                <Button type="submit" className="w-full h-12 rounded-xl text-md font-semibold" disabled={loading || !file || !name}>
                  {loading ? "Analyzing..." : "Train Model"}
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="detected">
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {detectedFaces.length > 0 ? (
              detectedFaces.map((face: any) => (
                <motion.div key={face.id} whileHover={{ y: -4 }} className="bg-card border rounded-2xl overflow-hidden shadow-sm">
                  <img src={`http://localhost:8000${face.url}`} alt="Face" className="w-full aspect-square object-cover" />
                  <div className="p-3 bg-muted/30 text-[10px] text-center font-mono text-muted-foreground">Cluster: {face.cluster}</div>
                </motion.div>
              ))
            ) : (
              <div className="col-span-full py-24 text-center">
                <Search className="w-16 h-16 mx-auto mb-4 text-muted-foreground/20" />
                <p className="text-muted-foreground font-medium">No detected faces yet. Start a library scan.</p>
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default FaceTraining;