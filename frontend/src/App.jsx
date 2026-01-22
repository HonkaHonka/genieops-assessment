import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Terminal, Cpu, Rocket, LayoutDashboard, PlusCircle, CreditCard, User, Zap, CheckCircle2, Code2, ChevronRight, ShieldCheck, Lock, History } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = "http://localhost:8000/api/v1";

// --- COMPONENT: HIGH-CONTRAST NEON MATRIX ---
const MatrixBackground = () => {
  const canvasRef = useRef(null);
  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    const characters = "010101018472950184"; 
    const fontSize = 14;
    const columns = canvas.width / fontSize;
    const drops = Array(Math.floor(columns)).fill(1);

    const draw = () => {
      ctx.fillStyle = "rgba(0, 0, 0, 0.15)"; 
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = "#00ff41"; 
      ctx.font = fontSize + "px monospace";
      for (let i = 0; i < drops.length; i++) {
        const text = characters.charAt(Math.floor(Math.random() * characters.length));
        ctx.fillText(text, i * fontSize, drops[i] * fontSize);
        if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) drops[i] = 0;
        drops[i]++;
      }
    };
    const interval = setInterval(draw, 40);
    return () => clearInterval(interval);
  }, []);
  return <canvas ref={canvasRef} className="fixed inset-0 pointer-events-none z-0 bg-black" />;
};

function App() {
  const [view, setView] = useState("generate"); 
  const [prompt, setPrompt] = useState("");
  const [existingTopics, setExistingTopics] = useState(""); // NEW: For PDF requirement
  const [status, setStatus] = useState("idle"); 
  const [progress, setProgress] = useState(0);
  const [log, setLog] = useState("");
  const [history, setHistory] = useState([]);
  const [isPaying, setIsPaying] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('view') === 'pricing') setView('pricing');
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const res = await axios.get(`${API_BASE}/lead-magnets-all`);
      setHistory(res.data);
    } catch (err) { console.error("Vault link broken"); }
  };

  const handleStripePayment = () => {
    setIsPaying(true);
    setTimeout(() => {
      alert("STRIPE: Payment Successful! Deploying SaaS instance...");
      setIsPaying(false);
      setView("generate");
    }, 3000);
  };

  const startGeneration = async () => {
    if (!prompt) return;
    setStatus("generating");
    try {
      setProgress(10); setLog("Strategist Agent initiating market scan...");
      // Combining prompt and existing topics for a better brief
      const fullPrompt = `${prompt}. Existing Content to Avoid: ${existingTopics}`;
      
      const res = await axios.post(`${API_BASE}/generate-idea`, {
        icp_profile: fullPrompt, 
        pain_points: "Neural link established", 
        brand_voice: "Professional", 
        offer_type: "SaaS", 
        conversion_goal: "Direct Checkout"
      });
      
      setProgress(60); setLog("Engineer Agent architecting PAS copy & logic...");
      await axios.post(`${API_BASE}/generate-full-asset/${res.data.id}`);
      
      setProgress(100); setLog("Neural Funnel Deployed.");
      setTimeout(() => {
        window.open(`http://localhost:8000/api/v1/preview/${res.data.id}`, '_blank');
        setStatus("idle"); setView("dashboard"); fetchHistory();
        setPrompt(""); setExistingTopics("");
      }, 1500);
    } catch (err) { setStatus("idle"); setLog("Link error. Re-try requested."); }
  };

  return (
    <div className="min-h-screen bg-black text-white selection:bg-green-500/30 overflow-x-hidden font-sans">
      <MatrixBackground />
      
      {/* --- STRIPE OVERLAY --- */}
      <AnimatePresence>
        {isPaying && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-[100] bg-black/90 flex items-center justify-center p-6 backdrop-blur-sm">
            <div className="bg-white text-slate-900 w-full max-w-md rounded-3xl p-10 shadow-2xl overflow-hidden relative border-t-8 border-blue-600">
              <div className="flex items-center gap-2 mb-8 text-blue-600">
                <CreditCard size={28} />
                <span className="font-black text-2xl tracking-tighter uppercase italic">Stripe.Checkout</span>
              </div>
              <div className="space-y-4">
                <div className="h-12 w-full bg-slate-50 rounded-xl border-2 border-slate-200 flex items-center px-4 justify-between">
                   <span className="font-mono text-lg font-bold text-slate-600">**** **** **** 4242</span>
                   <span className="text-xs text-slate-400 font-bold uppercase">VISA</span>
                </div>
                <div className="flex gap-4">
                  <div className="h-12 flex-1 bg-slate-50 border-2 border-slate-200 rounded-xl"></div>
                  <div className="h-12 w-24 bg-slate-50 border-2 border-slate-200 rounded-xl"></div>
                </div>
              </div>
              <button disabled className="w-full py-5 mt-10 bg-blue-600 text-white font-black rounded-2xl flex items-center justify-center gap-3 shadow-xl">
                 <div className="w-5 h-5 border-t-2 border-white rounded-full animate-spin"></div>
                 PROCESSING_PAYMENT
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* --- NAVBAR --- */}
      <nav className="sticky top-0 px-8 py-4 border-b border-white/5 flex justify-between items-center bg-black/90 backdrop-blur-md z-50">
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => setView('generate')}>
          <div className="flex items-center gap-2 text-[#00ff41]">
            <Code2 size={24} strokeWidth={3} />
            <span className="text-xl font-black tracking-tighter uppercase font-orbitron text-white">GENIE<span className="text-[#00ff41]">OPS</span></span>
          </div>
        </div>
        
        <div className="flex gap-8 items-center font-orbitron text-[10px] tracking-[0.2em] font-medium uppercase text-slate-400">
            {[{id: 'generate', label: 'home'}, {id: 'pricing', label: 'offer'}, {id: 'dashboard', label: 'vault'}, {id: 'account', label: 'login'}].map((v) => (
                <button key={v.id} onClick={() => setView(v.id)} className={`hover:text-[#00ff41] transition-all hover:scale-105 ${view === v.id ? 'text-[#00ff41] font-black' : ''}`}>{v.label}</button>
            ))}
        </div>
      </nav>

      <main className="relative z-10 max-w-6xl mx-auto pt-24 px-6 pb-40">
        <AnimatePresence mode="wait">
          
          {/* VIEW: HOME / GENERATOR */}
          {view === "generate" && (
            <motion.div key="gen" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="text-center">
              {status === "idle" ? (
                <>
                  <div className="inline-block px-3 py-1 rounded-full bg-green-500/10 border border-green-500/20 text-[#00ff41] text-[9px] font-black uppercase tracking-[0.3em] mb-12 animate-pulse">● Neural Orchestrator Online</div>
                  <h2 className="text-5xl md:text-7xl font-black tracking-tight leading-[1.1] mb-12 font-orbitron uppercase text-white">REBUILD YOUR <span className="text-[#00ff41]">MVP</span><br />INTO A <span className="text-white italic underline decoration-green-500/30 underline-offset-8">REAL SAAS</span></h2>
                  
                  <div className="max-w-3xl mx-auto space-y-4">
                    <div className="bg-[#0a0a0a] border border-white/10 rounded-3xl p-3 shadow-2xl focus-within:border-[#00ff41]/50 transition-all">
                      <div className="flex items-center gap-4">
                        <input value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="Describe your SaaS vision and audience..." className="flex-1 bg-transparent border-none outline-none p-5 text-xl text-white placeholder:text-slate-800 font-mono" />
                        <button onClick={startGeneration} className="bg-[#00ff41] hover:bg-green-400 text-black px-8 py-5 rounded-2xl font-black transition-all active:scale-95 shadow-xl shadow-green-500/20"><Rocket size={24} /></button>
                      </div>
                    </div>
                    {/* NEW: Existing Topics Field */}
                    <div className="flex items-center gap-4 bg-white/5 border border-white/5 px-6 py-3 rounded-2xl text-left">
                       <History size={16} className="text-slate-600"/>
                       <input value={existingTopics} onChange={(e) => setExistingTopics(e.target.value)} placeholder="Avoid repeating existing assets (e.g. Sourdough Secret Guide)..." className="flex-1 bg-transparent border-none outline-none text-xs text-slate-500 font-mono" />
                    </div>
                  </div>

                  <div className="flex justify-center gap-6 mt-12 font-orbitron">
                    <button onClick={() => setView('pricing')} className="bg-[#00ff41] text-black px-6 py-3 rounded-sm font-black text-[10px] uppercase tracking-widest hover:brightness-110 flex items-center gap-2 transition-all">CHECK PRODUCT FIT <ChevronRight size={14}/></button>
                    <button onClick={() => setView('dashboard')} className="border border-[#00ff41] text-[#00ff41] px-6 py-3 rounded-sm font-black text-[10px] uppercase tracking-widest hover:bg-[#00ff41]/10">VIEW ACTIVE NODES</button>
                  </div>
                </>
              ) : (
                <div className="max-w-md mx-auto bg-black border border-green-500/20 rounded-2xl p-12 text-center shadow-[0_0_80px_rgba(0,255,65,0.05)]">
                    <Cpu className="text-[#00ff41] animate-spin mx-auto mb-8" size={64} />
                    <p className="text-5xl font-black text-white font-orbitron mb-8">{progress}%</p>
                    <div className="font-mono text-[9px] text-green-500 uppercase tracking-widest leading-loose italic">&gt; {log}</div>
                </div>
              )}
            </motion.div>
          )}

          {/* VIEW: VAULT / DASHBOARD */}
          {view === "dashboard" && (
            <motion.div key="vault" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-12 pb-40">
              <div className="flex items-end justify-between border-l-4 border-[#00ff41] pl-6">
                <div>
                    <h2 className="text-4xl font-black font-orbitron uppercase text-white tracking-tighter">Neural <span className="text-[#00ff41]">Vault</span></h2>
                    <p className="text-slate-500 text-xs font-mono uppercase tracking-[0.2em] mt-2">Active Production Instances: {history.length}</p>
                </div>
              </div>
              
              <div className="grid gap-10">
                {history.map(f => (
                  <div key={f.id} className="bg-[#050505] border border-white/5 rounded-3xl p-10 flex flex-col lg:flex-row gap-12 hover:border-[#00ff41]/30 transition-all shadow-2xl relative group">
                    <div className="flex-1">
                      <div className="flex items-center gap-4 mb-6 uppercase tracking-widest font-black text-[9px]">
                        <span className="text-[#00ff41] bg-green-500/10 px-3 py-1 rounded-full border border-green-500/20">{f.idea_type}</span>
                        {/* NEURAL GAUGE / CONFIDENCE SCORE */}
                        <div className="flex items-center gap-3 bg-white/5 px-3 py-1 rounded-full border border-white/5">
                            <div className="w-16 h-1 bg-white/10 rounded-full overflow-hidden">
                                <div style={{ width: `${f.conversion_score || 92}%` }} className="h-full bg-[#00ff41] shadow-[0_0_8px_#00ff41]"></div>
                            </div>
                            <span className="text-[#00ff41]">{f.conversion_score || 92}% SUCCESS CONFIDENCE</span>
                        </div>
                      </div>
                      <h3 className="text-3xl font-black text-white font-orbitron uppercase mb-4 tracking-tighter leading-tight">{f.idea_title}</h3>
                      <p className="text-slate-400 text-sm italic font-serif leading-relaxed opacity-70 mb-10 max-w-xl">"{f.value_promise}"</p>
                      <button onClick={() => window.open(`http://localhost:8000/api/v1/preview/${f.id}`, '_blank')} className="bg-[#00ff41] text-black px-10 py-4 rounded-2xl font-black hover:brightness-110 transition uppercase text-xs tracking-widest shadow-xl active:scale-95 transform">EXECUTE FUNNEL PROTOCOL</button>
                    </div>

                    {/* IMPROVED LINKEDIN PREVIEW */}
                    <div className="lg:w-[450px] bg-black/60 rounded-[2.5rem] p-10 border border-white/10 flex flex-col justify-center shadow-inner">
                       <p className="text-[10px] font-black text-[#00ff41]/50 uppercase tracking-[0.3em] mb-6 flex items-center gap-2">
                          <Zap size={14}/> Ad Strategy: Social Story
                       </p>
                       <div className="rounded-2xl overflow-hidden mb-6 border border-white/10 h-44 group-hover:scale-105 transition-transform duration-700">
                         <img src={f.linkedin_img || 'https://images.pexels.com/photos/3184291/pexels-photo-3184291.jpeg'} className="w-full h-full object-cover grayscale hover:grayscale-0 transition-all opacity-60" alt="Ad" />
                       </div>
                       <p className="text-[13px] text-slate-200 font-sans leading-relaxed italic line-clamp-6 opacity-90">"{f.linkedin_post}"</p>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* VIEW: PRICING / OFFER */}
          {view === "pricing" && (
            <motion.div key="price" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="max-w-5xl mx-auto">
              <div className="text-center mb-24 font-orbitron uppercase">
                <h2 className="text-5xl font-black text-white mb-4">SELECT <span className="text-[#00ff41]">PROTOCOL</span></h2>
                <p className="text-slate-500 text-sm tracking-widest">Upgrade your neural link to production status</p>
              </div>
              <div className="grid md:grid-cols-2 gap-8">
                <div className="bg-[#050505] border border-white/5 p-12 rounded-2xl hover:border-[#00ff41]/30 transition-all">
                  <h3 className="text-xl font-bold font-orbitron mb-2 tracking-widest">MONTHLY NODE</h3>
                  <div className="text-6xl font-black text-white mb-8 font-orbitron">$49<span className="text-sm text-slate-600 font-normal">/mo</span></div>
                  <ul className="text-slate-400 space-y-4 mb-10 text-[10px] font-mono tracking-wider">
                    <li className="flex items-center gap-2 uppercase">✅ 10 Weekly Generations</li>
                    <li className="flex items-center gap-2 uppercase">✅ Standard Neural Processing</li>
                    <li className="flex items-center gap-2 uppercase">✅ SMTP Email Logic Active</li>
                  </ul>
                  <button onClick={handleStripePayment} className="w-full py-4 bg-white/5 hover:bg-white/10 text-white border border-white/10 rounded-lg font-black uppercase text-[10px] tracking-widest transition-colors">Initialize Link</button>
                </div>
                <div className="bg-[#00ff41] p-12 rounded-2xl text-black shadow-[0_0_80px_rgba(0,255,65,0.2)]">
                  <h3 className="text-xl font-bold font-orbitron mb-2 tracking-widest">ANNUAL PROTOCOL</h3>
                  <div className="text-6xl font-black mb-8 font-orbitron">$399<span className="text-sm opacity-60 font-normal">/yr</span></div>
                  <ul className="space-y-4 mb-10 text-[10px] font-black uppercase font-mono tracking-wider">
                    <li className="flex items-center gap-2">⚡ Unlimited Funnel Creation</li>
                    <li className="flex items-center gap-2">⚡ Priority VRAM Allocation</li>
                    <li className="flex items-center gap-2">⚡ Full Multi-Agent Suite</li>
                  </ul>
                  <button onClick={handleStripePayment} className="w-full py-4 bg-black text-white rounded-lg font-black uppercase text-[10px] tracking-widest shadow-2xl hover:scale-105 transition-transform">Deploy Annual Hub</button>
                </div>
              </div>
            </motion.div>
          )}

          {/* VIEW: ACCOUNT */}
          {view === "account" && (
            <motion.div key="acc" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-md mx-auto">
               <div className="bg-[#050505] border border-white/10 p-12 rounded-[2.5rem] shadow-2xl text-center">
                  <User className="text-[#00ff41] mx-auto mb-8 border border-[#00ff41]/20 p-4 rounded-3xl w-24 h-24" />
                  <h2 className="text-2xl font-black font-orbitron text-white mb-10 uppercase tracking-[0.2em]">Operator Login</h2>
                  <div className="space-y-4">
                    <input type="text" placeholder="ACCESS_ID" className="w-full p-4 bg-black rounded-xl border border-white/5 outline-none focus:border-[#00ff41] transition text-center text-[#00ff41] font-mono text-sm uppercase"/>
                    <input type="password" placeholder="PASS_KEY" className="w-full p-4 bg-black rounded-xl border border-white/5 outline-none focus:border-[#00ff41] transition text-center text-[#00ff41] font-mono text-sm uppercase"/>
                  </div>
                  <button className="w-full py-4 mt-10 bg-[#00ff41] text-black font-black rounded-xl uppercase text-[10px] tracking-widest hover:shadow-[0_0_20px_rgba(0,255,65,0.4)] transition-all">Establish Link</button>
               </div>
            </motion.div>
          )}

        </AnimatePresence>
      </main>

      <footer className="fixed bottom-0 left-0 right-0 p-8 flex justify-between items-center bg-gradient-to-t from-black via-black/80 to-transparent pointer-events-none z-50">
         <div className="text-[10px] font-black text-green-950 uppercase tracking-[0.5em] flex gap-10">
            <div className="flex items-center gap-2"><div className="w-1.5 h-1.5 bg-green-900 rounded-full animate-pulse shadow-[0_0_10px_#00ff41]"></div> P2P_NEURAL_LINK: ACTIVE</div>
            <div>VRAM_POOL: 6GB // GENIEOPS_PROTOCOL_V2.1</div>
         </div>
      </footer>
    </div>
  );
}

export default App;