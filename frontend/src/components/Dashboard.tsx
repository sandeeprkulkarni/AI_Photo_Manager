// src/components/Dashboard.tsx
import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { motion } from "motion/react";
import { Image, Users, MapPin, Sparkles } from "lucide-react";

// Named export to match routes.tsx
export function Dashboard() {
  const [stats, setStats] = useState({ photos: 0, faces: 0, locations: 0, events: 0 });

  useEffect(() => {
    fetch("http://localhost:8000/api/stats")
      .then(res => res.json())
      .then(data => setStats({
        photos: data.photos || 0,
        faces: data.faces || 0,
        locations: data.locations || 0,
        events: data.events || 0
      }))
      .catch(err => console.error("Stats Error:", err));
  }, []);

  const cards = [
    { label: "Photos", val: stats.photos, icon: <Image size={20}/>, color: "var(--primary)" },
    { label: "Faces", val: stats.faces, icon: <Users size={20}/>, color: "#10b981" },
    { label: "Places", val: stats.locations, icon: <MapPin size={20}/>, color: "#f59e0b" },
    { label: "Events", val: stats.events, icon: <Sparkles size={20}/>, color: "#8b5cf6" }
  ];

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-10">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {cards.map((card, i) => (
          <div key={i} className="p-6 bg-card border border-border rounded-2xl shadow-sm">
            <div className="flex items-center gap-3 text-muted-foreground mb-4">
              <span style={{ color: card.color }}>{card.icon}</span>
              <span className="text-xs font-bold uppercase tracking-widest">{card.label}</span>
            </div>
            <p className="text-4xl font-black">{(card.val || 0).toLocaleString()}</p>
          </div>
        ))}
      </div>

      <div className="p-10 bg-card border border-border rounded-3xl shadow-sm h-96">
        <h3 className="text-lg font-medium mb-8 text-foreground">Library Insights</h3>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={[
            { n: "Photos", v: stats.photos },
            { n: "Faces", v: stats.faces },
            { n: "Places", v: stats.locations }
          ]}>
            <XAxis dataKey="n" axisLine={false} tickLine={false} tick={{fill: 'var(--muted-foreground)'}} />
            <Tooltip 
              cursor={{fill: 'var(--accent)'}} 
              contentStyle={{backgroundColor: 'var(--card)', borderRadius: '12px', border: '1px solid var(--border)'}} 
            />
            <Bar dataKey="v" radius={[10, 10, 10, 10]} barSize={50}>
              <Cell fill="var(--primary)" />
              <Cell fill="var(--secondary-foreground)" />
              <Cell fill="var(--muted-foreground)" />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}