'use client';

import { useEffect, useState } from 'react';
import { motion } from 'motion/react';
import { 
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid
} from 'recharts';
import { RefreshCcw, Search, User, Calendar, ExternalLink, Timer, CheckCircle, Flame, Activity, Bot } from 'lucide-react';

interface CallMetrics {
  total: number;
  successful: number;
  failed: number;
  rate: number;
  recent: Array<{ id: string; status: string; time: string }>;
  unique_callers: number;
  chart_data: Array<{ name: string; calls: number; success: number }>;
  distribution: Array<{ name: string; val: number; count: number }>;
  error?: string;
}

export function DashboardView() {
  const [metrics, setMetrics] = useState<CallMetrics>({
    total: 0, successful: 0, failed: 0, rate: 0, recent: [], unique_callers: 0, chart_data: [], distribution: []
  });

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const res = await fetch('http://localhost:8080/api/metrics');
        if (res.ok) {
          const data = await res.json();
          setMetrics(data);
        }
      } catch (err) {
        console.error("Dashboard fetch error:", err);
      }
    };
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 3000);
    return () => clearInterval(interval);
  }, []);

  const chartData = metrics.chart_data && metrics.chart_data.length > 0 
    ? metrics.chart_data 
    : [
        { name: 'Mon', calls: 0, success: 0 },
        { name: 'Tue', calls: 0, success: 0 },
        { name: 'Wed', calls: 0, success: 0 },
        { name: 'Thu', calls: 0, success: 0 },
      ];

  return (
    <div className="flex-1 w-full bg-background text-foreground font-sans flex flex-col lg:flex-row">
      {/* Main Content Area */}
      <div className="flex-1 p-8 lg:p-12 lg:pr-8 flex flex-col">
          
          {/* Header */}
          <header className="flex justify-between items-center mb-10">
            <div className="flex items-center gap-4">
              <img src="/logo.png" alt="NDRF Logo" className="w-12 h-12 object-contain" />
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-foreground">Live Dashboard</h1>
                <p className="text-muted-foreground text-sm font-medium flex items-center gap-2">
                  Rakshika AI Command Center
                  <span className="opacity-30">|</span>
                  <span className="text-[10px] font-mono uppercase tracking-widest opacity-80">
                    Powered by <span className="text-red-400">Murf Falcon</span> & LiveKit
                  </span>
                </p>
              </div>
            </div>
            <div className="flex gap-4">
              <div className="relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input 
                  type="text" 
                  placeholder="Search emergencies" 
                  className="pl-10 pr-4 py-2.5 bg-muted/50 border border-border rounded-full text-sm outline-none w-64 text-foreground focus:ring-1 focus:ring-red-500 transition-all font-mono"
                />
              </div>
              <button className="w-10 h-10 rounded-full bg-muted/50 border border-border flex items-center justify-center text-muted-foreground hover:bg-muted transition">
                <User className="w-4 h-4" />
              </button>
            </div>
          </header>

          {/* Top Cards Section */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            
            {/* Profile Card */}
            <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className="bg-card rounded-[32px] p-6 shadow-lg border border-border flex flex-col items-center relative">
              <button className="absolute right-6 top-6 text-muted-foreground hover:text-foreground">
                <RefreshCcw className="w-4 h-4" />
              </button>
              <div className="w-24 h-24 rounded-full bg-muted/20 border border-border mb-4 mt-2 flex items-center justify-center overflow-hidden">
                <img src="/r-logo.png" alt="Rakshika AI" className="w-full h-full object-cover" />
              </div>
              <h2 className="text-xl font-bold tracking-tight text-foreground">Rakshika AI</h2>
              <p className="text-muted-foreground text-xs uppercase tracking-widest font-mono mb-6">Agent Status: Active</p>
              <div className="flex gap-4 w-full justify-center">
                <div className="flex items-center gap-1.5 px-3 py-1.5 bg-muted/50 rounded-full text-sm font-medium text-foreground border border-border">
                  <User className="w-3.5 h-3.5 text-blue-400" /> {metrics.unique_callers}
                </div>
                <div className="flex items-center gap-1.5 px-3 py-1.5 bg-muted/50 rounded-full text-sm font-medium text-foreground border border-border">
                  <CheckCircle className="w-3.5 h-3.5 text-red-500" /> {metrics.successful}
                </div>
              </div>
            </motion.div>

            {/* Gradient Stats Cards */}
            <div className="col-span-2 grid grid-cols-2 gap-6">
              {/* Success Rate Card */}
              <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.1 }} className="rounded-[32px] p-8 flex flex-col justify-between relative overflow-hidden bg-gradient-to-br from-red-950/80 to-red-900/40 border border-red-500/20 shadow-[0_0_30px_rgba(239,68,68,0.1)]">
                <div className="flex justify-between items-start z-10">
                  <h3 className="text-red-100 font-medium text-sm tracking-widest uppercase">Resolution Rate</h3>
                  <div className="w-10 h-10 rounded-full bg-red-500/20 backdrop-blur-sm flex items-center justify-center border border-red-500/30">
                    <CheckCircle className="w-5 h-5 text-red-400" />
                  </div>
                </div>
                <div className="z-10 mt-12">
                  <div className="text-5xl font-bold text-red-50 mb-1 tracking-tighter">{metrics.rate}%</div>
                  <div className="text-red-300 font-mono text-xs uppercase tracking-wider">Avg. Completed</div>
                </div>
              </motion.div>

              {/* Total Calls Card */}
              <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.2 }} className="rounded-[32px] p-8 flex flex-col justify-between relative overflow-hidden bg-gradient-to-br from-slate-900 to-slate-800 border border-border shadow-lg">
                <div className="flex justify-between items-start z-10">
                  <h3 className="text-muted-foreground font-medium text-sm tracking-widest uppercase">Emergency Calls</h3>
                  <div className="w-10 h-10 rounded-full bg-muted/80 backdrop-blur-sm flex items-center justify-center border border-border">
                    <Activity className="w-5 h-5 text-foreground" />
                  </div>
                </div>
                <div className="z-10 mt-12">
                  <div className="text-5xl font-bold text-foreground mb-1 tracking-tighter">{metrics.total}</div>
                  <div className="text-muted-foreground font-mono text-xs uppercase tracking-wider">Total Handled</div>
                </div>
              </motion.div>
            </div>
          </div>

          {/* Chart Section */}
          <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.3 }}>
            <div className="flex justify-between items-end mb-8">
              <div>
                <h2 className="text-xl font-bold text-foreground tracking-tight mb-1">Session Analytics</h2>
                <p className="text-muted-foreground font-mono text-xs uppercase tracking-wider">Volume & Resolution Trend</p>
              </div>
              <select 
                className="flex items-center gap-2 px-4 py-2 bg-muted/50 border border-border rounded-full text-xs font-mono text-foreground cursor-pointer hover:bg-muted transition outline-none appearance-none"
              >
                <option value="7">RANGE: LAST 7 DAYS</option>
                <option value="30">RANGE: LAST MONTH</option>
              </select>
            </div>

            <div className="h-[350px] w-full relative mt-4">
              {metrics.total === 0 && (
                <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-background/50 backdrop-blur-[2px]">
                  <Activity className="w-8 h-8 text-muted-foreground mb-4 opacity-50 animate-pulse" />
                  <p className="text-muted-foreground font-mono text-sm uppercase tracking-widest">Waiting for live calls...</p>
                </div>
              )}
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 20, right: 30, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                  <XAxis 
                    dataKey="name" 
                    axisLine={false} 
                    tickLine={false} 
                    tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12, fontFamily: 'monospace' }}
                    dy={10}
                  />
                  <YAxis 
                    axisLine={false} 
                    tickLine={false} 
                    tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12, fontFamily: 'monospace' }}
                    dx={-10}
                    allowDecimals={false}
                  />
                  <Tooltip 
                    contentStyle={{ borderRadius: '12px', border: '1px solid hsl(var(--border))', backgroundColor: 'hsl(var(--card))', color: 'hsl(var(--foreground))' }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="calls" 
                    stroke="hsl(var(--muted-foreground))" 
                    strokeWidth={2} 
                    dot={false}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="success" 
                    stroke="#ef4444" 
                    strokeWidth={3} 
                    dot={{ r: 4, fill: "hsl(var(--background))", stroke: "#ef4444", strokeWidth: 2 }}
                    activeDot={{ r: 6, fill: "#ef4444", stroke: "hsl(var(--background))", strokeWidth: 3 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            
            <div className="flex justify-between items-center mt-6 px-10">
              <div className="flex gap-6">
                <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-muted-foreground">
                  <div className="w-3 h-3 rounded-sm bg-muted-foreground"></div> Inbound
                </div>
                <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-muted-foreground">
                  <div className="w-3 h-3 rounded-sm bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.5)]"></div> Resolved
                </div>
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold tracking-tighter text-foreground">{metrics.rate}%</div>
                <div className="text-[10px] font-mono uppercase tracking-widest text-red-500">Avg. Conversion</div>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Right Sidebar */}
        <div className="w-full lg:w-[400px] bg-muted/20 border-l border-border p-8 lg:p-12">
          
          {/* Recent Calls List */}
          <div className="flex justify-between items-center mb-8">
            <h2 className="text-lg font-bold tracking-tight text-foreground">Live Feed</h2>
            <button className="w-10 h-10 bg-background border border-border rounded-full flex items-center justify-center text-muted-foreground hover:bg-muted transition shadow-sm">
              <Calendar className="w-4 h-4" />
            </button>
          </div>

          <div className="space-y-6 mb-12">
            {metrics.recent.length === 0 ? (
              <p className="text-sm font-mono text-muted-foreground text-center py-4">No recent activity</p>
            ) : (
              metrics.recent.slice(0, 4).map((call, i) => (
                <div key={i} className="flex gap-6 pb-6 border-b border-border/50 last:border-0 last:pb-0 group cursor-pointer">
                  <div className="w-20 pt-1">
                    <p className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground mb-1">
                      {new Date(call.time + 'Z').toLocaleDateString('en-US', { weekday: 'short', day: 'numeric', month: 'short' })}
                    </p>
                    <p className="text-sm font-bold font-mono text-foreground">
                      {new Date(call.time + 'Z').toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                    </p>
                  </div>
                  <div className="flex-1">
                    <div className="flex justify-between items-start">
                      <p className="font-semibold text-foreground text-sm mb-1 group-hover:text-red-400 transition-colors">Session {call.id.substring(0, 6)}</p>
                      <ExternalLink className="w-3.5 h-3.5 text-muted-foreground group-hover:text-red-400 transition-colors" />
                    </div>
                    <div className="flex items-center gap-1.5 text-xs font-mono font-medium">
                      {call.status === 'success' ? (
                        <><span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"></span><span className="text-muted-foreground">Resolved</span></>
                      ) : (
                        <><span className="w-2 h-2 rounded-full bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.5)]"></span><span className="text-muted-foreground">Escalated/Failed</span></>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
            
            {metrics.recent.length > 0 && (
              <button className="text-xs font-mono uppercase tracking-widest text-muted-foreground hover:text-foreground w-full text-center flex items-center justify-center gap-2 mt-4 transition-colors">
                View all logs <span>›</span>
              </button>
            )}
          </div>

          {/* Breakdown Section */}
          <h2 className="text-lg font-bold tracking-tight text-foreground mb-2">Developed areas</h2>
          <p className="text-muted-foreground font-mono text-xs uppercase tracking-wider mb-8">Incident distribution</p>
          
          <div className="space-y-6">
            {metrics.distribution && metrics.distribution.length > 0 ? (
              metrics.distribution.map((item, i) => {
                const colorMap: Record<string, string> = {
                  'Weather Alerts': 'bg-red-500',
                  'Hospital Search': 'bg-blue-500',
                  'Rescue Esc.': 'bg-amber-500',
                  'General Safety': 'bg-emerald-500'
                };
                const color = colorMap[item.name] || 'bg-slate-500';
                return (
                  <div key={i} className="flex items-center gap-4">
                    <span className="w-32 text-sm font-medium text-foreground">{item.name}</span>
                    <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                      <div className={`h-full ${color} rounded-full`} style={{ width: `${item.val}%` }}></div>
                    </div>
                    <span className="text-xs font-mono font-medium text-muted-foreground w-8 text-right">{item.val}%</span>
                  </div>
                );
              })
            ) : (
              <p className="text-sm font-mono text-muted-foreground">No data available yet</p>
            )}
          </div>

        </div>
      </div>
  );
}
