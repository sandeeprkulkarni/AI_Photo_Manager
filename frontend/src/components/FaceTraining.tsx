// src/components/FaceTraining.tsx
import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Upload, UserCheck, AlertCircle } from 'lucide-react';

const FaceTraining = () => {
  const [name, setName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);

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
        body: formData, // No headers needed, browser sets multipart/form-data
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
    <div className="p-6 max-w-2xl mx-auto">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <UserCheck className="w-6 h-6 text-blue-500" />
            Face Identity Training
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="name">Person's Full Name</Label>
              <Input 
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. John Doe"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="photo">Training Photo (Clear Face Only)</Label>
              <div className="flex items-center justify-center w-full">
                <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100">
                  <div className="flex flex-col items-center justify-center pt-5 pb-6">
                    <Upload className="w-8 h-8 mb-3 text-gray-400" />
                    <p className="text-sm text-gray-500">
                      {file ? file.name : "Click to upload face sample"}
                    </p>
                  </div>
                  <input 
                    id="photo" 
                    type="file" 
                    className="hidden" 
                    accept="image/*"
                    onChange={handleFileChange}
                    required
                  />
                </label>
              </div>
            </div>

            {message && (
              <div className={`p-3 rounded-md flex items-center gap-2 ${
                message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
              }`}>
                {message.type === 'error' && <AlertCircle className="w-4 h-4" />}
                {message.text}
              </div>
            )}

            <Button 
              type="submit" 
              className="w-full" 
              disabled={loading || !file || !name}
            >
              {loading ? "Analyzing Face..." : "Train Identity"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default FaceTraining;