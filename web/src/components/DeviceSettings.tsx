import { Camera, Monitor, Mic, RefreshCw } from "lucide-react";
import type React from "react";
import { useEffect, useState } from "react";
import { useBackend } from "../BackendContext";

interface HardwareData {
  monitors: any[];
  microphones: any[];
  cameras: string[];
}

const DeviceSettings: React.FC = () => {
  const { request } = useBackend();
  const [data, setData] = useState<HardwareData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchHardware = async () => {
    try {
      const resp = await request("/api/v1/hardware");
      setData(resp);
    } catch (err) {
      console.error("Hardware probe failed", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchHardware();
  }, [request]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchHardware();
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-2xl font-black text-white tracking-tight">Device Settings</h2>
          <p className="text-text-secondary mt-1">Configure your local hardware environment.</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 px-4 py-2 glass-card border-none hover:bg-white/10 transition-colors text-sm font-bold text-white disabled:opacity-50"
        >
          <RefreshCw size={14} className={refreshing ? "animate-spin" : ""} />
          Refresh
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center p-20">
          <div className="w-8 h-8 border-4 border-accent-purple border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Cameras */}
          <section className="glass-card p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-accent-purple/10 rounded-lg">
                <Camera size={20} className="text-accent-purple" />
              </div>
              <h3 className="font-bold text-white">Cameras</h3>
            </div>
            <div className="space-y-3">
              {data?.cameras.length === 0 ? (
                <p className="text-sm text-text-secondary italic">No cameras detected.</p>
              ) : (
                data?.cameras.map((cam, i) => (
                  <div key={i} className="flex items-center justify-between p-3 bg-white/[0.03] border border-white/5 rounded-xl">
                    <span className="text-sm font-medium text-white">{cam}</span>
                    {cam.toLowerCase().includes("c922") && (
                      <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-400 text-[10px] font-black uppercase rounded-full">Default</span>
                    )}
                  </div>
                ))
              )}
            </div>
          </section>

          {/* Microphones */}
          <section className="glass-card p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-blue-500/10 rounded-lg">
                <Mic size={20} className="text-blue-400" />
              </div>
              <h3 className="font-bold text-white">Microphones</h3>
            </div>
            <div className="space-y-3">
              {data?.microphones.length === 0 ? (
                <p className="text-sm text-text-secondary italic">No microphones detected.</p>
              ) : (
                data?.microphones.map((mic, i) => (
                  <div key={i} className="flex items-center justify-between p-3 bg-white/[0.03] border border-white/5 rounded-xl">
                    <div className="flex flex-col">
                      <span className="text-sm font-medium text-white truncate max-w-[200px]">{mic.name}</span>
                      <span className="text-[10px] text-text-secondary uppercase tracking-wider font-bold">{mic.rate}Hz • {mic.channels}ch</span>
                    </div>
                    {mic.name.toLowerCase().includes("c922") && (
                      <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-400 text-[10px] font-black uppercase rounded-full">Default</span>
                    )}
                  </div>
                ))
              )}
            </div>
          </section>

          {/* Monitors */}
          <section className="glass-card p-6 md:col-span-2">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-amber-500/10 rounded-lg">
                <Monitor size={20} className="text-amber-400" />
              </div>
              <h3 className="font-bold text-white">Display Layout</h3>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {data?.monitors.map((mon, i) => (
                <div key={i} className="relative p-6 bg-white/[0.03] border border-white/10 rounded-2xl flex flex-col items-center justify-center min-h-[160px] group transition-all hover:bg-white/[0.05]">
                  <div className="absolute top-3 left-3 w-6 h-6 rounded-lg bg-white/5 flex items-center justify-center text-[10px] font-black text-white">
                    {i + 1}
                  </div>
                  <Monitor size={32} className="text-text-secondary opacity-20 mb-4 group-hover:opacity-40 transition-opacity" />
                  <span className="text-base font-black text-white">{mon.width} × {mon.height}</span>
                  <span className="text-[10px] text-text-secondary mt-1 font-mono uppercase">Pos: {mon.left}, {mon.top}</span>
                  {i === 0 && (
                    <span className="mt-3 px-2 py-0.5 bg-accent-purple/20 text-accent-purple text-[10px] font-black uppercase rounded-full">Primary</span>
                  )}
                </div>
              ))}
            </div>
          </section>
        </div>
      )}
    </div>
  );
};

export default DeviceSettings;
