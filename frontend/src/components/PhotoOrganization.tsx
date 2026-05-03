import React, { useState, useEffect } from 'react';
import { Input } from "./ui/input";
import { Button } from "./ui/button";
import { Search, Users, MapPin, Tag, Image as ImageIcon, Loader2 } from "lucide-react";

interface Photo {
  id: number;
  path: string;
  size_kb: number;
  taken_at: string;
  event: string | null;
  location: string | null;
}

export const PhotoOrganization = () => {
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("All");
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    const fetchPhotos = async () => {
      try {
        const response = await fetch('/api/photos');
        const data = await response.json();
        if (data.status === 'success') {
          setPhotos(data.photos);
        }
      } catch (error) {
        console.error("Error fetching photos:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchPhotos();
  }, []);

  // Filter photos based on the active tab and search query
  const filteredPhotos = photos.filter(photo => {
    // 1. Apply Tab Filters
    if (activeTab === "Location" && !photo.location) return false;
    if (activeTab === "Untagged" && (photo.event || photo.location)) return false;
    // (Note: The "People" tab is a placeholder until we link the faces database table to this view!)

    // 2. Apply Search Query
    if (searchQuery) {
      const queryLower = searchQuery.toLowerCase();
      
      // Check if the search text matches the folder path, event name, or location name
      const matchesPath = photo.path.toLowerCase().includes(queryLower);
      const matchesEvent = photo.event ? photo.event.toLowerCase().includes(queryLower) : false;
      const matchesLoc = photo.location ? photo.location.toLowerCase().includes(queryLower) : false;

      if (!matchesPath && !matchesEvent && !matchesLoc) {
        return false;
      }
    }
    
    return true;
  });

  return (
    <div className="p-6 max-w-[1600px] mx-auto space-y-6 animate-in fade-in duration-500">
      
      {/* Header */}
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Photo Organization</h1>
        <p className="text-sm text-slate-500">
          {filteredPhotos.length} photos • 0 selected
        </p>
      </div>

      {/* Controls Bar */}
      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
        
        {/* Search Bar */}
        <div className="relative w-full sm:max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input 
            placeholder="Search by folder path, location, or event..." 
            className="pl-9 bg-white border-slate-200 text-slate-900 w-full shadow-sm" 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center gap-2 overflow-x-auto w-full sm:w-auto pb-2 sm:pb-0">
          <Button 
            variant={activeTab === "All" ? "secondary" : "ghost"} 
            size="sm" 
            className={`text-sm rounded-full px-4 ${activeTab === "All" ? "bg-slate-100 text-slate-900" : "text-slate-600 hover:text-slate-900"}`}
            onClick={() => setActiveTab("All")}
          >
            All
          </Button>
          <Button 
            variant={activeTab === "People" ? "secondary" : "ghost"} 
            size="sm" 
            className={`text-sm rounded-full px-4 ${activeTab === "People" ? "bg-slate-100 text-slate-900" : "text-slate-600 hover:text-slate-900"}`}
            onClick={() => setActiveTab("People")}
          >
            <Users className="w-4 h-4 mr-2" /> People
          </Button>
          <Button 
            variant={activeTab === "Location" ? "secondary" : "ghost"} 
            size="sm" 
            className={`text-sm rounded-full px-4 ${activeTab === "Location" ? "bg-slate-100 text-slate-900" : "text-slate-600 hover:text-slate-900"}`}
            onClick={() => setActiveTab("Location")}
          >
            <MapPin className="w-4 h-4 mr-2" /> Location
          </Button>
          <Button 
            variant={activeTab === "Untagged" ? "secondary" : "ghost"} 
            size="sm" 
            className={`text-sm rounded-full px-4 ${activeTab === "Untagged" ? "bg-slate-100 text-slate-900" : "text-slate-600 hover:text-slate-900"}`}
            onClick={() => setActiveTab("Untagged")}
          >
            <Tag className="w-4 h-4 mr-2" /> Untagged
          </Button>
        </div>
      </div>

      {/* Photo Grid */}
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-slate-400" />
        </div>
      ) : filteredPhotos.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-slate-500 bg-slate-50 rounded-xl border border-slate-200 border-dashed">
          <ImageIcon className="w-12 h-12 mb-4 text-slate-300" />
          <p>No photos found matching your search.</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {filteredPhotos.map((photo) => (
            <div 
              key={photo.id} 
              className="group relative aspect-square bg-slate-100 rounded-xl overflow-hidden border border-slate-200 hover:ring-2 hover:ring-blue-500 transition-all cursor-pointer shadow-sm"
            >
              <img 
                src={`/api/image?path=${encodeURIComponent(photo.path)}`} 
                alt="Scanned photo" 
                className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                loading="lazy"
              />
              <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors" />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};