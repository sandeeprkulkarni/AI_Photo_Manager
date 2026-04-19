// src/components/FaceTraining.tsx
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

  // Fetch detected faces for the second tab
  useEffect(() => {
    fetch("http://localhost:8000/api/faces/unlabeled")
      .then(res => res.json())
      .then(data => setDetectedFaces(data))
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
      const response = await fetch("/api/train", { method: "POST", body: formData });
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
        <h2 className="text-3xl font-bold">Face Identity Training</h2>
        <p className="text-muted-foreground mt-1">Manage and train the AI recognition model.</p>
      </header>

      <Tabs defaultValue="training" className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-2 mb-8">
          <TabsTrigger value="training">Training Model</TabsTrigger>
          <TabsTrigger value="detected">Detected Faces</TabsTrigger>
        </TabsList>

        {/* Tab 1: Original Training Form */}
        <TabsContent value="training">
          <Card className="max-w-2xl mx-auto">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <UserCheck className="w-6 h-6 text-primary" />
                Add New Identity
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="name">Person's Full Name</Label>
                  <Input id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. John Doe" required />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="photo">Training Photo</Label>
                  <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-lg cursor-pointer bg-muted/50 hover:bg-muted transition-colors">
                    <div className="flex flex-col items-center justify-center pt-5 pb-6">
                      <Upload className="w-8 h-8 mb-2 text-muted-foreground" />
                      <p className="text-sm text-muted-foreground">{file ? file.name : "Click to upload face sample"}</p>
                    </div>
                    <input id="photo" type="file" className="hidden" accept="image/*" onChange={handleFileChange} required />
                  </label>
                </div>
                {message && (
                  <div className={`p-3 rounded-md flex items-center gap-2 ${message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                    {message.type === 'error' && <AlertCircle className="w-4 h-4" />}
                    {message.text}
                  </div>
                )}
                <Button type="submit" className="w-full" disabled={loading || !file || !name}>
                  {loading ? "Analyzing..." : "Train Identity"}
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 2: The Face Gallery */}
        <TabsContent value="detected">
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {detectedFaces.length > 0 ? (
              detectedFaces.map((face: any) => (
                <motion.div key={face.id} whileHover={{ y: -5 }} className="bg-card border rounded-xl overflow-hidden shadow-sm">
                  <img src={`http://localhost:8000${face.url}`} alt="Detected" className="w-full aspect-square object-cover" />
                  <div className="p-2 bg-muted/30 text-[10px] text-center font-mono">Cluster: {face.cluster}</div>
                </motion.div>
              ))
            ) : (
              <div className="col-span-full py-20 text-center text-muted-foreground">
                <Search className="w-12 h-12 mx-auto mb-4 opacity-20" />
                <p>No unlabeled faces detected yet. Start a library scan to find faces.</p>
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default FaceTraining;