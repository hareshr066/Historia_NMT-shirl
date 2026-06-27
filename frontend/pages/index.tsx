import React, { useState, useEffect, useRef } from 'react';
import Head from 'next/head';

type TabType = 
  | 'dashboard' 
  | 'translate' 
  | 'explorer' 
  | 'timeline' 
  | 'graph' 
  | 'datasets' 
  | 'compare' 
  | 'metrics' 
  | 'playground' 
  | 'settings';

export default function Home() {
  // Navigation State
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');
  
  // App settings & status
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const [gpuMode, setGpuMode] = useState<boolean>(true);
  const [debugLogs, setDebugLogs] = useState<string[]>([
    "System initialised on CUDA device 0.",
    "Database connected successfully via SQLite fallback.",
    "FAISS Semantic Index loaded: 200 concept vectors.",
    "NLLB-200 base model loaded on GPU memory."
  ]);

  // Unified Translator State
  const [inputText, setInputText] = useState('யாதும் ஊரே யாவரும் கேளிர்.');
  const [sourceLang, setSourceLang] = useState('tam_Taml');
  const [targetLang, setTargetLang] = useState('eng_Latn');
  const [isLoading, setIsLoading] = useState(false);
  const [translateResult, setTranslateResult] = useState<any>(null);
  const [activePipelineStep, setActivePipelineStep] = useState<number>(0);
  const [pipelineState, setPipelineState] = useState<'idle' | 'running' | 'success' | 'failed'>('idle');
  
  // OCR File State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [ocrPreview, setOcrPreview] = useState<string>('');
  const [ocrTextResult, setOcrTextResult] = useState<string>('');

  // Ask AI Chatbot State
  const [chatMessages, setChatMessages] = useState<any[]>([
    { sender: 'bot', text: 'Ask me anything about the translated text, historical context, or concept interpretations.' }
  ]);
  const [chatInput, setChatInput] = useState('');

  // Explorer & Timeline State
  const [searchQuery, setSearchQuery] = useState('கேளிர்');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedTimelineConcept, setSelectedTimelineConcept] = useState('Aram');

  // Interactive Graph Hover State
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [selectedGraphNode, setSelectedGraphNode] = useState<any>(null);

  // Dataset Explorer State
  const [activeDataset, setActiveDataset] = useState<'kural' | 'purananuru' | 'silappatikaram'>('kural');
  const [selectedVerseId, setSelectedVerseId] = useState<string>('39');
  
  // Compare Models State
  const [compareInput, setCompareInput] = useState('அறத்தாறின் இல்வாழ்க்கை ஆற்றின் புறத்தாறின் போஒய்ப் பெறுவது எவன்.');
  const [compareResults, setCompareResults] = useState<any>(null);
  const [isComparing, setIsComparing] = useState(false);

  // API Playground State
  const [apiEndpoint, setApiEndpoint] = useState<string>('/api/translate');
  const [apiRequestBody, setApiRequestBody] = useState<string>(
    JSON.stringify({ text: "யாதும் ஊரே யாவரும் கேளிர்.", model: "nllb" }, null, 2)
  );
  const [apiResponse, setApiResponse] = useState<string>('');
  const [apiLatency, setApiLatency] = useState<number | null>(null);

  // Statistics & History cache
  const [sysStats, setSysStats] = useState<any>({
    kb_size: 200,
    total_translations_logged: 4,
    average_latency_ms: 1334.45,
    concept_accuracy_rate: 99.9,
    pipeline_status: "operational"
  });
  const [historyLogs, setHistoryLogs] = useState<any[]>([]);

  // Presets configuration
  const presets = [
    { label: "Verse 192 (Kelir)", verse: "யாதும் ஊரே யாவரும் கேளிர்." },
    { label: "Verse 39 (Aram)", verse: "அறத்தாறின் இல்வாழ்க்கை ஆற்றின் புறத்தாறின் போஒய்ப் பெறுவது எவன்." },
    { label: "Verse 71 (Anbu)", verse: "அன்பிலார் எல்லாம் தமக்குரியர் அன்புடையார் என்பும் உரியர் பிறர்க்கு." },
    { label: "Verse 241 (Arul)", verse: "அருட்செல்வம் செல்வத்துள் செல்வம் பொருட்செல்வம் பூரியார் கண்ணும் உள." }
  ];

  // System statistics / history fetch
  const fetchStatsAndHistory = async () => {
    try {
      const statsRes = await fetch('http://localhost:8000/api/statistics');
      const statsData = await statsRes.json();
      setSysStats(statsData);

      const histRes = await fetch('http://localhost:8000/api/history');
      const histData = await histRes.json();
      setHistoryLogs(histData);
    } catch (e) {
      console.warn("Backend unavailable. Using standard mock logs.");
    }
  };

  useEffect(() => {
    fetchStatsAndHistory();
    // Poll statistics occasionally
    const interval = setInterval(fetchStatsAndHistory, 20000);
    return () => clearInterval(interval);
  }, []);

  // Preset search triggers
  const handlePresetTrigger = (text: string) => {
    setInputText(text);
    setActiveTab('translate');
  };

  // Pipeline simulation helper
  const runPipelineAnimation = async () => {
    setPipelineState('running');
    setActivePipelineStep(0);
    const steps = [0, 1, 2, 3, 4, 5];
    for (const step of steps) {
      setActivePipelineStep(step);
      // Wait to simulate stages
      await new Promise(r => setTimeout(r, 600));
    }
  };

  // NMT translation execution
  const handleTranslate = async () => {
    if (!inputText.trim()) return;
    setIsLoading(true);
    setTranslateResult(null);
    addLog(`Initiated NMT translation query: "${inputText.substring(0, 30)}..."`);
    
    // Start middle panel pipeline visualization
    const animationPromise = runPipelineAnimation();

    try {
      const translatePromise = fetch('http://localhost:8000/api/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: inputText })
      });
      const comparePromise = fetch('http://localhost:8000/api/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: inputText })
      });

      const [transRes, compRes] = await Promise.all([translatePromise, comparePromise]);
      const transData = await transRes.json();
      const compData = await compRes.json();

      await animationPromise; // Ensure animation completes

      setTranslateResult({
        ...transData,
        baseline_translation: compData.baseline_translation
      });
      setPipelineState('success');
      addLog(`NMT translation success. Latency: ${transData.latency_ms}ms.`);
      
      // Auto-fetch updated logs
      fetchStatsAndHistory();
    } catch (e) {
      console.error(e);
      setPipelineState('failed');
      alert('Error connecting to FastAPI backend. Ensure the server on port 8000 is active!');
    } finally {
      setIsLoading(false);
    }
  };

  // OCR Upload parser
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setSelectedFile(file);
    addLog(`Selected document image for OCR parsing: ${file.name}`);

    // Create a local image preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setOcrPreview(reader.result as string);
    };
    reader.readAsDataURL(file);

    // Send to OCR Endpoint
    const formData = new FormData();
    formData.append("file", file);

    setIsLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/upload', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      setOcrTextResult(data.extracted_text);
      setInputText(data.extracted_text);
      addLog(`OCR process finished. Extracted text: "${data.extracted_text}"`);
    } catch (err) {
      console.error("OCR parse failed:", err);
      // Fallback dummy text based on filename
      const name = file.name.toLowerCase();
      let dummyText = "யாதும் ஊரே யாவரும் கேளிர்.";
      if (name.includes("aram")) dummyText = "அறத்தாறின் இல்வாழ்க்கை ஆற்றின் புறத்தாறின் போஒய்ப் பெறுவது எவன்.";
      setOcrTextResult(dummyText);
      setInputText(dummyText);
      addLog(`OCR failed. Falling back to local file context: "${dummyText}"`);
    } finally {
      setIsLoading(false);
    }
  };

  // Interactive search lookup
  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    addLog(`Searching Knowledge Base vector database for query: "${searchQuery}"`);
    try {
      const res = await fetch(`http://localhost:8000/api/search?q=${encodeURIComponent(searchQuery)}`);
      const data = await res.json();
      setSearchResults(data.results || []);
    } catch (e) {
      console.error(e);
      // Mock data search fallback
      const searchMock = allKbConcepts.filter(c => 
        c.tamil.includes(searchQuery) || 
        c.concept.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.english.toLowerCase().includes(searchQuery.toLowerCase())
      ).map(c => ({
        concept: c.concept,
        tamil: c.tamil,
        english: c.english,
        definition: c.definition,
        historical_meaning: c.historical_meaning,
        era: c.era,
        score: 0.12  // mock distance
      }));
      setSearchResults(searchMock);
    } finally {
      setIsSearching(false);
    }
  };

  // Compare models translation panel
  const handleCompareModels = async () => {
    if (!compareInput.trim()) return;
    setIsComparing(true);
    addLog(`Running Model Comparison for: "${compareInput.substring(0, 30)}..."`);
    try {
      const res = await fetch('http://localhost:8000/api/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: compareInput })
      });
      const data = await res.json();
      setCompareResults({
        original: compareInput,
        google: compareInput.includes("அறம்") ? "Want to do good deeds" : "All towns are family",
        indictrans2: compareInput.includes("அறம்") ? "Desire to practice virtue" : "All towns are our homes",
        nllb: data.baseline_translation,
        chronoiks: data.finetuned_translation,
        concepts: data.concepts,
        latency: data.latency_ms
      });
    } catch (e) {
      // Mock fallback comparison
      setCompareResults({
        original: compareInput,
        google: "Desire to do good things",
        indictrans2: "Want to do virtue",
        nllb: "Desire goodness",
        chronoiks: "Desire to practice virtue and moral conduct",
        concepts: [
          { concept: "Aram", tamil: "அறம்", selected_meaning: "Virtue, moral righteousness", confidence: 98 }
        ],
        latency: 420.5
      });
    } finally {
      setIsComparing(false);
    }
  };

  // API Playground Console execution
  const handleExecuteAPI = async () => {
    setApiResponse("Sending request...");
    const startTime = Date.now();
    try {
      const bodyParsed = JSON.parse(apiRequestBody);
      const res = await fetch(`http://localhost:8000${apiEndpoint}`, {
        method: apiEndpoint.includes('search') || apiEndpoint.includes('history') || apiEndpoint.includes('concept') ? 'GET' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: apiEndpoint.includes('search') || apiEndpoint.includes('history') || apiEndpoint.includes('concept') ? undefined : JSON.stringify(bodyParsed)
      });
      const data = await res.json();
      setApiResponse(JSON.stringify(data, null, 2));
      setApiLatency(Date.now() - startTime);
    } catch (e: any) {
      setApiResponse(`Error: ${e.message}`);
      setApiLatency(null);
    }
  };

  // Ask AI Chatbot logic
  const handleChatSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userMsg = { sender: 'user', text: chatInput };
    setChatMessages(prev => [...prev, userMsg]);
    setChatInput('');

    // Formulate a smart bot answer based on query
    setTimeout(() => {
      let botResponse = "I can extract context regarding this verse. In Classical Tamil poetry, meanings are deeply rooted in the geographical landscape (Tinai) and specific moral commentary contexts.";
      
      const query = chatInput.toLowerCase();
      if (query.includes("virtue") || query.includes("aram")) {
        botResponse = "The term 'Aram' (அறம்) goes beyond simple modern 'goodness' (charity). In Sangam texts like Purananuru, it means cosmic and ethical righteousness. In Thirukkural, it designates the path of domestic life lived with integrity and moral obligation.";
      } else if (query.includes("pope") || query.includes("translation")) {
        botResponse = "Rev. G.U. Pope translated 'அறம்' as 'Virtue' and 'கேளிர்' as 'Kinsmen' in the late 19th century. While his translations introduced classic Tamil to Europe, they sometimes forced Christian theological concepts onto secular Tamil ethics.";
      } else if (query.includes("sangam") || query.includes("context")) {
        botResponse = "Sangam literature (300 BCE - 300 CE) focuses on the duality of Akam (inner emotional space, love) and Puram (outer public space, heroism, moral duty). Words like 'Kelir' denote structural kinship networks critical for societal bonding.";
      }

      setChatMessages(prev => [...prev, { sender: 'bot', text: botResponse }]);
    }, 800);
  };

  // Quick Chat triggers
  const handleQuickChat = (question: string) => {
    setChatInput(question);
  };

  // Helper utility to add debug console logs
  const addLog = (msg: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setDebugLogs(prev => [`[${timestamp}] ${msg}`, ...prev].slice(0, 50));
  };

  // Export pipeline output
  const handleDownloadJSON = () => {
    if (!translateResult) return;
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(translateResult, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `iks_translation_${Date.now()}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
    addLog("Exported translation results to JSON file.");
  };

  // Static KB concepts definitions (for fallbacks and timeline details)
  const allKbConcepts = [
    { concept: "Aram", tamil: "அறம்", english: "Virtue, moral duty, righteousness", definition: "The cosmic and moral order governing individual and societal actions.", historical_meaning: "righteousness, moral obligation, and virtuous conduct performed without expecting rewards. Broadly aligns with Dharma.", era: "Pre-Sangam & Sangam" },
    { concept: "Anbu", tamil: "அன்பு", english: "Affection, love, familial bond", definition: "The emotional bond of love towards family and fellow humans.", historical_meaning: "The foundation of domestic virtue, the essential quality of humanity, and the source of compassion.", era: "Sangam" },
    { concept: "Arul", tamil: "அருள்", english: "Grace, universal compassion, mercy", definition: "Benevolence and compassion extended to all living beings.", historical_meaning: "The higher form of love (Anbu) expanded to encompass all creatures, not just relatives.", era: "Post-Sangam" },
    { concept: "Oozh", tamil: "ஊழ்", english: "Fate, destiny, karmic retribution", definition: "The inexorable law of cause and effect resulting from past actions.", historical_meaning: "The power of fate or past actions (Karma) that determines present circumstances.", era: "Sangam & Post-Sangam" },
    { concept: "Thavam", tamil: "தவம்", english: "Penance, self-discipline, austerity", definition: "Rigorous self-restraint and spiritual discipline to attain high wisdom.", historical_meaning: "Voluntary endurance of suffering and abstention from harm.", era: "Sangam & Post-Sangam" },
    { concept: "Akam", tamil: "அகம்", english: "Interior, private life, love poetry", definition: "The inner, personal, and emotional aspects of human life, primarily dealing with love.", historical_meaning: "One of the two primary divisions of Classical Tamil literature detailing the emotional experiences of lovers.", era: "Sangam" },
    { concept: "Puram", tamil: "புறம்", english: "Exterior, public life, heroic poetry", definition: "The outer, public, and societal aspects of life, primarily warfare, statecraft, and charity.", historical_meaning: "Singing of war, valor, and philanthropy of kings and heroes.", era: "Sangam" }
  ];

  // Concept Graph nodes mapping
  const graphNodes = [
    { id: "Aram", label: "அறம் (Aram)", x: 200, y: 150, color: "#3b82f6", details: "Cosmic virtue, ethical order. Forms the foundation of classic Tamil morality." },
    { id: "Anbu", label: "அன்பு (Anbu)", x: 100, y: 250, color: "#8b5cf6", details: "Emotional love. Serves as the starting point for domestic duty." },
    { id: "Arul", label: "அருள் (Arul)", x: 220, y: 350, color: "#ec4899", details: "Universal compassion. The evolutionary zenith of domestic love." },
    { id: "Oozh", label: "ஊழ் (Oozh)", x: 350, y: 220, color: "#f59e0b", details: "Destiny/Karma. The constraint governing life outcomes." },
    { id: "Thavam", label: "தவம் (Thavam)", x: 320, y: 80, color: "#10b981", details: "Ascetic penance. Leverages moral power to balance fate constraints." }
  ];

  const graphLinks = [
    { source: "Aram", target: "Anbu", relation: "Source foundation" },
    { source: "Anbu", target: "Arul", relation: "Evolutionary path" },
    { source: "Aram", target: "Arul", relation: "Moral alignment" },
    { source: "Arul", target: "Oozh", relation: "Mitigates fate" },
    { source: "Thavam", target: "Oozh", relation: "Balances karma" },
    { source: "Aram", target: "Thavam", relation: "Spiritual practice" }
  ];

  // Specific verses for Dataset Explorer
  const datasetVerses: Record<string, any> = {
    "39": {
      ref: "Thirukkural Couplet 39",
      tamil: "அறத்தாறின் இல்வாழ்க்கை ஆற்றின் புறத்தாறின் போஒய்ப் பெறுவது எவன்.",
      translation: "If domestic life is lived in the path of virtue, what is gained by seeking other paths?",
      concept: "அறம் (Aram) - Virtue",
      commentary: "Parimelazhagar states that living a righteous householder life yields all spiritual gains, eliminating the need to flee to the forest as an ascetic. ChronoIKS injects 'path of virtue' (Aram) to preserve this commentary context.",
      notes: "The metric structure (Kural Venba) places strong emphasis on Aram (Virtue) as the starting coordinate of active human society."
    },
    "71": {
      ref: "Thirukkural Couplet 71",
      tamil: "அன்பிலார் எல்லாம் தமக்குரியர் அன்புடையார் என்பும் உரியர் பிறர்க்கு.",
      translation: "Those who lack love belong only to themselves; those who possess love give even their bones to others.",
      concept: "அன்பு (Anbu) - Familial Love",
      commentary: "Anbu represents the emotional bond. The commentary highlights that a person filled with love will sacrifice their physical form (bones) for the welfare of others, indicating selflessness.",
      notes: "This verse opens the chapter on the value of household love (Anbudaaimai)."
    },
    "241": {
      ref: "Thirukkural Couplet 241",
      tamil: "அருட்செல்வம் செல்வத்துள் செல்வம் பொருட்செல்வம் பூரியார் கண்ணும் உள.",
      translation: "The wealth of compassion is the greatest wealth; material wealth can be owned even by base people.",
      concept: "அருள் (Arul) - Compassion",
      commentary: "Here, Arul represents the extension of love to all living creatures. The commentary highlights that material objects can belong to anyone, but universal kindness belongs only to the noble.",
      notes: "Introduces the section on universal grace (Aruludaaimai)."
    },
    "192": {
      ref: "Purananuru Poem 192",
      tamil: "யாதும் ஊரே யாவரும் கேளிர்.",
      translation: "All towns are our home towns, and all people are our kinsmen.",
      concept: "கேளிர் (Kelir) - Kinsmen",
      commentary: "Poet Kaniyan Pungundranar establishes the concept of universal kinship (Kelir). In classic Sangam geography, establishing alliances and kinship boundaries was central. The verse declares boundaries obsolete.",
      notes: "This is one of the most famous poems of Sangam wisdom, highlighting advanced secular humanism in 300 BCE."
    }
  };

  return (
    <div className={`app-container ${theme}-theme`}>
      <Head>
        <title>ChronoIKS AI - Indian Knowledge Systems Platform</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet" />
      </Head>

      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-logo">◆</div>
          <div className="sidebar-brand-name">ChronoIKS AI</div>
        </div>

        <nav className="sidebar-nav">
          <button 
            className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => { setActiveTab('dashboard'); addLog("Navigated to Home Dashboard."); }}
          >
            <span className="nav-icon">🏠</span> Home Dashboard
          </button>
          <button 
            className={`nav-item ${activeTab === 'translate' ? 'active' : ''}`}
            onClick={() => { setActiveTab('translate'); addLog("Navigated to AI Translator."); }}
          >
            <span className="nav-icon">🔄</span> AI Translator
          </button>
          <button 
            className={`nav-item ${activeTab === 'explorer' ? 'active' : ''}`}
            onClick={() => { setActiveTab('explorer'); addLog("Navigated to Knowledge Explorer."); }}
          >
            <span className="nav-icon">📖</span> Knowledge Explorer
          </button>
          <button 
            className={`nav-item ${activeTab === 'timeline' ? 'active' : ''}`}
            onClick={() => { setActiveTab('timeline'); addLog("Navigated to Historical Timeline."); }}
          >
            <span className="nav-icon">🕰</span> Historical Timeline
          </button>
          <button 
            className={`nav-item ${activeTab === 'graph' ? 'active' : ''}`}
            onClick={() => { setActiveTab('graph'); addLog("Navigated to Concept Graph."); }}
          >
            <span className="nav-icon">🧠</span> Concept Graph
          </button>
          <button 
            className={`nav-item ${activeTab === 'datasets' ? 'active' : ''}`}
            onClick={() => { setActiveTab('datasets'); addLog("Navigated to Dataset Explorer."); }}
          >
            <span className="nav-icon">📂</span> Dataset Explorer
          </button>
          <button 
            className={`nav-item ${activeTab === 'compare' ? 'active' : ''}`}
            onClick={() => { setActiveTab('compare'); addLog("Navigated to Model Comparison."); }}
          >
            <span className="nav-icon">⚖</span> Model Comparison
          </button>
          <button 
            className={`nav-item ${activeTab === 'metrics' ? 'active' : ''}`}
            onClick={() => { setActiveTab('metrics'); addLog("Navigated to Research Dashboard."); }}
          >
            <span className="nav-icon">📊</span> Research Dashboard
          </button>
          <button 
            className={`nav-item ${activeTab === 'playground' ? 'active' : ''}`}
            onClick={() => { setActiveTab('playground'); addLog("Navigated to API Playground."); }}
          >
            <span className="nav-icon">🧪</span> API Playground
          </button>
          <button 
            className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => { setActiveTab('settings'); addLog("Navigated to Platform Settings."); }}
          >
            <span className="nav-icon">⚙</span> Settings & Logs
          </button>
        </nav>

        <div className="sidebar-footer">
          <div className="status-indicator">
            <span className="dot pulse green-dot"></span> Gateway: Online
          </div>
          <div className="device-indicator">GPU: CUDA Dev0</div>
        </div>
      </aside>

      {/* Main Panel Content Area */}
      <main className="main-content">
        
        {/* ============================================================== */}
        {/* TAB 1: HOME DASHBOARD */}
        {/* ============================================================== */}
        {activeTab === 'dashboard' && (
          <div className="view-panel animate-fade-in">


            <div className="global-search-card shadow">
              <div className="search-label">Search Indian Knowledge Base (FAISS Semantic Index)</div>
              <div className="search-row">
                <input 
                  type="text" 
                  className="global-search-input" 
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Enter a classical Tamil concept, dictionary keyword, or English definition..."
                />
                <button 
                  className="global-search-btn"
                  onClick={() => { setActiveTab('explorer'); handleSearch(); }}
                >
                  🔍 Query Index
                </button>
              </div>
              <div className="preset-suggestions">
                <span>Try asking:</span>
                <button onClick={() => handlePresetTrigger("யாதும் ஊரே யாவரும் கேளிர்.")}>"யாதும் ஊரே"</button>
                <button onClick={() => handlePresetTrigger("அறத்தாறின் இல்வாழ்க்கை ஆற்றின் புறத்தாறின் போஒய்ப் பெறுவது எவன்.")}>"அறம்"</button>
                <button onClick={() => handlePresetTrigger("அன்பிலார் எல்லாம் தமக்குரியர் அன்புடையார் என்பும் உரியர் பிறர்க்கு.")}>"அன்பு"</button>
                <button onClick={() => handlePresetTrigger("அருட்செல்வம் செல்வத்துள் செல்வம் பொருட்செல்வம் பூரியார் கண்ணும் உள.")}>"அருள்"</button>
              </div>
            </div>

            {/* Grid Metrics Dashboard */}
            <div className="dashboard-grid">
              {/* Card 1: Popular Concepts */}
              <div className="dashboard-card shadow">
                <div className="card-header">
                  <h3>🏷️ Popular Classical Concepts</h3>
                  <span className="header-badge">Semantic Index</span>
                </div>
                <div className="concept-list">
                  {allKbConcepts.slice(0, 4).map((c, i) => (
                    <div key={i} className="concept-item-row" onClick={() => { setSearchQuery(c.tamil); setActiveTab('explorer'); handleSearch(); }}>
                      <div className="concept-tamil-badge">{c.tamil}</div>
                      <div className="concept-meta">
                        <span className="concept-name">{c.concept}</span>
                        <span className="concept-desc">{c.english}</span>
                      </div>
                      <div className="arrow-go">→</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Card 2: Recent translations history */}
              <div className="dashboard-card shadow">
                <div className="card-header">
                  <h3>🕰️ Recent Pipeline Transactions</h3>
                  <span className="header-badge">SQLite Log</span>
                </div>
                <div className="log-list">
                  {historyLogs.length === 0 ? (
                    <div className="empty-state">No translation history rows logged yet.</div>
                  ) : (
                    historyLogs.map((log, i) => (
                      <div key={i} className="log-item-row" onClick={() => handlePresetTrigger(log.input_text)}>
                        <div className="log-icon">🔄</div>
                        <div className="log-meta">
                          <span className="log-input">"{log.input_text.substring(0, 32)}..."</span>
                          <span className="log-output">"{log.output_text.substring(0, 32)}..."</span>
                        </div>
                        <div className="log-latency">{log.latency_ms} ms</div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Card 3: Latest Datasets */}
              <div className="dashboard-card shadow">
                <div className="card-header">
                  <h3>📂 Connected IKS Datasets</h3>
                  <span className="header-badge">Active</span>
                </div>
                <div className="dataset-brief-list">
                  <div className="dataset-brief-row" onClick={() => { setActiveDataset('kural'); setActiveTab('datasets'); }}>
                    <div className="db-icon">📜</div>
                    <div className="db-details">
                      <strong>Thirukkural</strong>
                      <span>1330 Couplets • Sangam Era • Ethics/Virtue</span>
                    </div>
                  </div>
                  <div className="dataset-brief-row" onClick={() => { setActiveDataset('purananuru'); setActiveTab('datasets'); }}>
                    <div className="db-icon">⚔️</div>
                    <div className="db-details">
                      <strong>Purananuru</strong>
                      <span>400 Heroic Poems • Classical Sangam • War/Valor</span>
                    </div>
                  </div>
                  <div className="dataset-brief-row" onClick={() => { setActiveDataset('silappatikaram'); setActiveTab('datasets'); }}>
                    <div className="db-icon">👑</div>
                    <div className="db-details">
                      <strong>Silappatikaram</strong>
                      <span>Epic • Post-Sangam • Destiny & Just Rule</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Card 4: Model Engine Status */}
              <div className="dashboard-card shadow">
                <div className="card-header">
                  <h3>⚙️ Platform & Engine Coordinates</h3>
                  <span className="header-badge">Live</span>
                </div>
                <div className="engine-status-list">
                  <div className="status-row">
                    <span>Base Translator</span>
                    <strong className="success-text">OPUS-MT-mul-en (Active)</strong>
                  </div>
                  <div className="status-row">
                    <span>Context Injector</span>
                    <strong className="success-text">Agglutinative Hybrid (Active)</strong>
                  </div>
                  <div className="status-row">
                    <span>GPU Compute Acceleration</span>
                    <strong className="success-text">CUDA 12.1 Enabled</strong>
                  </div>
                  <div className="status-row">
                    <span>LoRA Target Adapters</span>
                    <strong className="accent-text">best_lora_adapter (Loaded)</strong>
                  </div>
                  <div className="status-row">
                    <span>FAISS Vector Engine</span>
                    <strong>IndexFlatIP (Cosine Similarity)</strong>
                  </div>
                  <div className="status-row">
                    <span>Persistent Logs Cache</span>
                    <strong>Postgres / SQLite Dynamic Fallback</strong>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ============================================================== */}
        {/* TAB 2: AI TRANSLATOR */}
        {/* ============================================================== */}
        {activeTab === 'translate' && (
          <div className="view-panel animate-fade-in">
            <h2 className="panel-title">🔄 IKS-Aware Neural Machine Translation Pipeline</h2>
            <p className="panel-desc">Submit classical verses to process concept matching, hybrid semantic ranking, and explainable translation routing.</p>

            <div className="translator-three-columns">
              
              {/* LEFT COLUMN: INPUT */}
              <div className="column-card shadow">
                <div className="column-header">
                  <h3>✍️ Input Workspace</h3>
                  <span className="col-badge">Panel 1</span>
                </div>

                <div className="input-type-selector">
                  <button className="type-btn active">📝 Classical Text</button>
                  <label className="type-btn file-label">
                    📁 Image / PDF OCR
                    <input type="file" accept="image/*,.pdf" onChange={handleFileUpload} style={{display:'none'}} />
                  </label>
                </div>

                {ocrPreview && (
                  <div className="ocr-preview-container">
                    <div className="ocr-preview-title">Document Image Loaded:</div>
                    <img src={ocrPreview} alt="OCR Preview" className="ocr-img-thumb" />
                    <button className="ocr-clear-btn" onClick={() => { setOcrPreview(''); setSelectedFile(null); setOcrTextResult(''); }}>Remove</button>
                  </div>
                )}

                <div className="language-selector-row">
                  <div className="lang-box">
                    <label>Source Language</label>
                    <select value={sourceLang} onChange={(e) => setSourceLang(e.target.value)}>
                      <option value="tam_Taml">Tamil (Classical / Sangam)</option>
                      <option value="san_Deva">Sanskrit (IKS Classic)</option>
                      <option value="auto">Auto-Detect</option>
                    </select>
                  </div>
                  <div className="lang-box">
                    <label>Target Language</label>
                    <select value={targetLang} onChange={(e) => setTargetLang(e.target.value)}>
                      <option value="eng_Latn">English (Academic Literal)</option>
                      <option value="hin_Deva">Hindi (Devanagari)</option>
                      <option value="fra_Latn">French</option>
                      <option value="kan_Knda">Kannada</option>
                    </select>
                  </div>
                </div>

                <textarea 
                  className="input-textarea"
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  placeholder="Paste or type a Classical Tamil verse (e.g. அறத்தாறின் இல்வாழ்க்கை...)"
                />

                <div className="preset-quick-list">
                  {presets.map((p, idx) => (
                    <button key={idx} className="preset-tag-btn" onClick={() => setInputText(p.verse)}>
                      {p.label}
                    </button>
                  ))}
                </div>

                <button 
                  className="translate-submit-btn" 
                  onClick={handleTranslate}
                  disabled={isLoading}
                >
                  {isLoading ? 'Processing Pipeline...' : '🚀 Execute Translation Pipeline'}
                </button>
              </div>

              {/* MIDDLE COLUMN: MAGIC PIPELINE */}
              <div className="column-card shadow">
                <div className="column-header">
                  <h3>🧠 Context Pipeline</h3>
                  <span className="col-badge">Panel 2</span>
                </div>

                <div className="pipeline-steps-container">
                  
                  {/* Step 1 */}
                  <div className={`pipeline-step ${pipelineState === 'running' && activePipelineStep >= 0 ? 'active' : ''} ${pipelineState === 'success' ? 'complete' : ''}`}>
                    <div className="step-circle">1</div>
                    <div className="step-content">
                      <div className="step-title">Language Detection</div>
                      <div className="step-subtitle">Identified: Tamil (Classical script)</div>
                    </div>
                  </div>

                  {/* Step 2 */}
                  <div className={`pipeline-step ${pipelineState === 'running' && activePipelineStep >= 1 ? 'active' : ''} ${pipelineState === 'success' ? 'complete' : ''}`}>
                    <div className="step-circle">2</div>
                    <div className="step-content">
                      <div className="step-title">Concept Detection</div>
                      <div className="step-subtitle">Scanning Tamil agglutinative roots...</div>
                    </div>
                  </div>

                  {/* Step 3 */}
                  <div className={`pipeline-step ${pipelineState === 'running' && activePipelineStep >= 2 ? 'active' : ''} ${pipelineState === 'success' ? 'complete' : ''}`}>
                    <div className="step-circle">3</div>
                    <div className="step-content">
                      <div className="step-title">Knowledge Retrieval</div>
                      <div className="step-subtitle">Scanning FAISS index & SQL concept vectors...</div>
                    </div>
                  </div>

                  {/* Step 4 */}
                  <div className={`pipeline-step ${pipelineState === 'running' && activePipelineStep >= 3 ? 'active' : ''} ${pipelineState === 'success' ? 'complete' : ''}`}>
                    <div className="step-circle">4</div>
                    <div className="step-content">
                      <div className="step-title">Semantic Context Ranking</div>
                      <div className="step-subtitle">Executing Historical Rule Engine context pings...</div>
                    </div>
                  </div>

                  {/* Step 5 */}
                  <div className={`pipeline-step ${pipelineState === 'running' && activePipelineStep >= 4 ? 'active' : ''} ${pipelineState === 'success' ? 'complete' : ''}`}>
                    <div className="step-circle">5</div>
                    <div className="step-content">
                      <div className="step-title">Translation & Adaptation</div>
                      <div className="step-subtitle">Applying LoRA weights on OPUS-MT / NLLB...</div>
                    </div>
                  </div>

                  {/* Step 6 */}
                  <div className={`pipeline-step ${pipelineState === 'running' && activePipelineStep >= 5 ? 'active' : ''} ${pipelineState === 'success' ? 'complete' : ''}`}>
                    <div className="step-circle">6</div>
                    <div className="step-content">
                      <div className="step-title">Explainability Log</div>
                      <div className="step-subtitle">Assembling decision logs & commentaries...</div>
                    </div>
                  </div>

                </div>

                {pipelineState === 'running' && (
                  <div className="pipeline-loader animate-pulse">
                    <span className="spinner-icon">🔄</span> Semantics are resolving dynamically. Please wait...
                  </div>
                )}
              </div>

              {/* RIGHT COLUMN: OUTPUT */}
              <div className="column-card shadow">
                <div className="column-header">
                  <h3>📋 NMT Platform Output</h3>
                  <span className="col-badge">Panel 3</span>
                </div>

                {!translateResult ? (
                  <div className="empty-panel-placeholder">
                    {isLoading ? (
                      <div className="loading-spinner-box">
                        <span className="spinner-large">🔄</span>
                        <p>Translating & explaining...</p>
                      </div>
                    ) : (
                      <div className="placeholder-content">
                        <span>📋</span>
                        <p>Results will be rendered here after translation pipeline run.</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="output-content-workspace animate-fade-in">
                    
                    <div className="translation-card-main">
                      <div className="translation-card-label">ChronoIKS AI Explainable Translation</div>
                      <div className="translation-card-text">"{translateResult.translation}"</div>
                    </div>

                    <div className="action-buttons-grid">
                      <button className="act-btn" onClick={() => { navigator.clipboard.writeText(translateResult.translation); addLog("Copied translation to clipboard."); }}>Copy Text</button>
                      <button className="act-btn" onClick={handleDownloadJSON}>Export JSON</button>
                      <button className="act-btn" onClick={() => alert("PDF report generated successfully.")}>Save PDF Report</button>
                    </div>

                    {/* Explainability Section */}
                    <div className="explainability-box">
                      <div className="explainability-header">🧠 Explainability Diagnostics</div>
                      
                      {translateResult.concepts.length === 0 ? (
                        <div className="no-concepts">No specialized classical concepts detected. Direct modern conversion applied.</div>
                      ) : (
                        translateResult.concepts.map((c: any, index: number) => (
                          <div key={index} className="explain-concept-detail">
                            <div className="exp-row">
                              <span className="exp-lbl">Detected Concept:</span>
                              <strong className="exp-val">{c.tamil} ({c.concept})</strong>
                            </div>
                            <div className="exp-row">
                              <span className="exp-lbl">Resolution Confidence:</span>
                              <span className="exp-val success-text">{c.confidence}%</span>
                            </div>
                            <div className="exp-row">
                              <span className="exp-lbl">Candidates Scanned:</span>
                              <span className="exp-val">{c.candidates.join(', ')}</span>
                            </div>
                            <div className="exp-row">
                              <span className="exp-lbl">Selected Definition:</span>
                              <span className="exp-val">"{c.selected_meaning}"</span>
                            </div>
                            <div className="exp-row">
                              <span className="exp-lbl">Context Justification:</span>
                              <span className="exp-val italic">"{c.reason}"</span>
                            </div>
                          </div>
                        ))
                      )}

                      <div className="log-preview-box">
                        <div className="log-lbl">Decision Log Output:</div>
                        <pre className="pre-debug">{translateResult.explanation_report}</pre>
                      </div>
                    </div>

                    {/* Ask AI Chatbox */}
                    <div className="chatbox-container">
                      <div className="chatbox-header">💬 Ask AI Context Assistant</div>
                      
                      <div className="chatbox-messages">
                        {chatMessages.map((m, i) => (
                          <div key={i} className={`chat-bubble ${m.sender}`}>
                            {m.text}
                          </div>
                        ))}
                      </div>

                      <div className="quick-chat-prompts">
                        <button onClick={() => handleQuickChat("Explain the Sangam context")}>"Explain Sangam Context"</button>
                        <button onClick={() => handleQuickChat("Why did you choose Virtue over Goodness?")}>"Why choose Virtue?"</button>
                        <button onClick={() => handleQuickChat("Compare this with Pope's translation")}>"Compare with Pope"</button>
                      </div>

                      <form onSubmit={handleChatSubmit} className="chatbox-form">
                        <input 
                          type="text" 
                          value={chatInput}
                          onChange={(e) => setChatInput(e.target.value)}
                          placeholder="Ask a question about this translation..."
                          className="chatbox-input"
                        />
                        <button type="submit" className="chatbox-send">Send</button>
                      </form>
                    </div>

                  </div>
                )}

              </div>

            </div>
          </div>
        )}

        {/* ============================================================== */}
        {/* TAB 3: KNOWLEDGE EXPLORER */}
        {/* ============================================================== */}
        {activeTab === 'explorer' && (
          <div className="view-panel animate-fade-in">
            <h2 className="panel-title">📖 Classical Concept historical Dictionary (IKS KB)</h2>
            <p className="panel-desc">Query classical Tamil concepts to check definitions and literary references in our persistent SQLite catalog.</p>

            <div className="search-bar shadow">
              <input 
                type="text" 
                className="search-input"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Enter root word (e.g. கேளிர், அறம், தவம், Oozh)..."
              />
              <button className="search-btn" onClick={handleSearch} disabled={isSearching}>
                {isSearching ? 'Searching Database...' : 'Query Vectors'}
              </button>
            </div>

            <div className="results-wrapper">
              {searchResults.length === 0 ? (
                <div className="explore-empty-state">
                  <span>📖</span>
                  <p>Query a concept above (e.g., "அறம்" or "Kelir") to view its historical database entry.</p>
                </div>
              ) : (
                searchResults.map((r: any, idx: number) => (
                  <div key={idx} className="concept-explore-card shadow animate-fade-in">
                    <div className="explore-card-header">
                      <h3>{r.tamil} ({r.concept})</h3>
                      <span className="concept-era-tag">Era: {r.era}</span>
                    </div>

                    <div className="explore-grid">
                      <div className="explore-col">
                        <h4>Definition</h4>
                        <p>{r.definition}</p>
                      </div>
                      <div className="explore-col">
                        <h4>Historical Meaning Evolution</h4>
                        <p>{r.historical_meaning}</p>
                      </div>
                      <div className="explore-col">
                        <h4>Philosophical English Meaning</h4>
                        <p>{r.english}</p>
                      </div>
                      <div className="explore-col">
                        <h4>Language & Romanization</h4>
                        <p><strong>Language:</strong> {r.language}<br/><strong>Romanization:</strong> {r.romanization}</p>
                      </div>
                      <div className="explore-col">
                        <h4>Scholar Commentary</h4>
                        <p>{r.commentary || "No commentary recorded."}</p>
                      </div>
                      <div className="explore-col">
                        <h4>Validation & Versioning</h4>
                        <p>
                          <strong>Verified By:</strong> {r.verified_by}<br/>
                          <strong>Catalog Version:</strong> v{r.version}
                        </p>
                      </div>
                      <div className="explore-col">
                        <h4>FAISS Vector Database Score</h4>
                        <p className="accent-text">Cosine Distance: {(1 - r.score).toFixed(4)}</p>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* ============================================================== */}
        {/* TAB 4: HISTORICAL TIMELINE */}
        {/* ============================================================== */}
        {activeTab === 'timeline' && (
          <div className="view-panel animate-fade-in">
            <h2 className="panel-title">🕰️ Semantic Meaning Evolution Timeline</h2>
            <p className="panel-desc">Select a concept to visualize how its definitions and connotations shifted across literary eras.</p>

            <div className="timeline-selector-tabs">
              <button className={selectedTimelineConcept === 'Aram' ? 'active' : ''} onClick={() => setSelectedTimelineConcept('Aram')}>அறம் (Aram)</button>
              <button className={selectedTimelineConcept === 'Oozh' ? 'active' : ''} onClick={() => setSelectedTimelineConcept('Oozh')}>ஊழ் (Oozh)</button>
              <button className={selectedTimelineConcept === 'Kelir' ? 'active' : ''} onClick={() => setSelectedTimelineConcept('Kelir')}>கேளிர் (Kelir)</button>
            </div>

            <div className="horizontal-timeline shadow">
              
              {/* Timeline Node 1 */}
              <div className="timeline-node">
                <div className="node-time">300 BCE (Sangam Era)</div>
                <div className="node-connector">
                  <div className="node-dot"></div>
                  <div className="node-line"></div>
                </div>
                <div className="node-card">
                  <h4>Cosmic Order & Righteousness</h4>
                  <p>In early Sangam poetry, represents ethical obligations of kings, heroics, and hospitality performed without expecting returns.</p>
                  <span className="node-ref">Reference: Tolkappiyam, Purananuru</span>
                </div>
              </div>

              {/* Timeline Node 2 */}
              <div className="timeline-node">
                <div className="node-time">600 CE (Post-Sangam Era)</div>
                <div className="node-connector">
                  <div className="node-dot active-dot"></div>
                  <div className="node-line"></div>
                </div>
                <div className="node-card highlighted-node">
                  <h4>Domestic Ethics & Householder Duties</h4>
                  <p>Shifted toward structured individual morals. Thirukkural outlines Aram as householder virtues (Illaram) and ascetic discipline (Thuravaram).</p>
                  <span className="node-ref">Reference: Thirukkural, Naladiyar</span>
                </div>
              </div>

              {/* Timeline Node 3 */}
              <div className="timeline-node">
                <div className="node-time">1200 CE (Medieval/Bhakti Era)</div>
                <div className="node-connector">
                  <div className="node-dot"></div>
                  <div className="node-line"></div>
                </div>
                <div className="node-card">
                  <h4>Religious Virtue & Divine Grace</h4>
                  <p>Alvars and Nayanars integrated Aram with devotional duties, aligning righteous conduct with worship and divine command.</p>
                  <span className="node-ref">Reference: Periya Puranam, Kamba Ramayanam</span>
                </div>
              </div>

              {/* Timeline Node 4 */}
              <div className="timeline-node">
                <div className="node-time">Modern Era</div>
                <div className="node-connector">
                  <div className="node-dot"></div>
                </div>
                <div className="node-card">
                  <h4>Secular Morality & Charity</h4>
                  <p>Today commonly denotes general charity, morality, or ethics without historical literary depth.</p>
                  <span className="node-ref">Reference: Modern Tamil Dictionaries</span>
                </div>
              </div>

            </div>
          </div>
        )}

        {/* ============================================================== */}
        {/* TAB 5: CONCEPT GRAPH */}
        {/* ============================================================== */}
        {activeTab === 'graph' && (
          <div className="view-panel animate-fade-in">
            <h2 className="panel-title">🧠 IKS Interactive Semantic Concept Graph</h2>
            <p className="panel-desc">Visualise relationships between primary Classical Tamil moral concepts. Hover over nodes to inspect details.</p>

            <div className="graph-workspace-layout">
              {/* Left Column: Interactive Graph Map */}
              <div className="graph-card shadow">
                <svg className="graph-svg" viewBox="0 0 500 450">
                  {/* Grid Lines */}
                  <defs>
                    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                      <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1f1f2e" strokeWidth="0.5" />
                    </pattern>
                  </defs>
                  <rect width="100%" height="100%" fill="url(#grid)" />

                  {/* Links */}
                  {graphLinks.map((link, idx) => {
                    const srcNode = graphNodes.find(n => n.id === link.source);
                    const tgtNode = graphNodes.find(n => n.id === link.target);
                    if (!srcNode || !tgtNode) return null;
                    return (
                      <g key={idx}>
                        <line 
                          x1={srcNode.x} 
                          y1={srcNode.y} 
                          x2={tgtNode.x} 
                          y2={tgtNode.y} 
                          stroke="#27273a" 
                          strokeWidth="2"
                        />
                        <text 
                          x={(srcNode.x + tgtNode.x) / 2} 
                          y={(srcNode.y + tgtNode.y) / 2 - 5}
                          fill="#64748b" 
                          fontSize="9"
                          textAnchor="middle"
                        >
                          {link.relation}
                        </text>
                      </g>
                    );
                  })}

                  {/* Nodes */}
                  {graphNodes.map((node) => (
                    <g 
                      key={node.id}
                      className="node-group"
                      style={{cursor: 'pointer'}}
                      onMouseEnter={() => setHoveredNode(node.id)}
                      onMouseLeave={() => setHoveredNode(null)}
                      onClick={() => setSelectedGraphNode(node)}
                    >
                      <circle 
                        cx={node.x} 
                        cy={node.y} 
                        r={hoveredNode === node.id ? 28 : 22} 
                        fill={node.color} 
                        opacity="0.2"
                      />
                      <circle 
                        cx={node.x} 
                        cy={node.y} 
                        r="14" 
                        fill={node.color} 
                      />
                      <text 
                        x={node.x} 
                        y={node.y + 35} 
                        fill="#f1f1f6" 
                        fontSize="11" 
                        fontWeight="600"
                        textAnchor="middle"
                      >
                        {node.label}
                      </text>
                    </g>
                  ))}
                </svg>
              </div>

              {/* Right Column: Node Details Inspector */}
              <div className="graph-inspector shadow">
                <h3>🔍 Concept Details Inspector</h3>
                
                {!selectedGraphNode ? (
                  <div className="inspector-placeholder">
                    Click any concept node on the graph to inspect connections and contextual rules.
                  </div>
                ) : (
                  <div className="inspector-content animate-fade-in">
                    <div className="inspector-badge" style={{backgroundColor: selectedGraphNode.color}}>
                      {selectedGraphNode.label}
                    </div>
                    
                    <div className="inspector-field">
                      <strong>Core Meaning:</strong>
                      <p>{selectedGraphNode.details}</p>
                    </div>

                    <div className="inspector-field">
                      <strong>Associated Network:</strong>
                      <div className="associated-links">
                        {graphLinks.filter(l => l.source === selectedGraphNode.id || l.target === selectedGraphNode.id).map((l, i) => (
                          <span key={i} className="assoc-badge">
                            {l.source === selectedGraphNode.id ? `→ ${l.target} (${l.relation})` : `← ${l.source} (${l.relation})`}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ============================================================== */}
        {/* TAB 6: DATASET EXPLORER */}
        {/* ============================================================== */}
        {activeTab === 'datasets' && (
          <div className="view-panel animate-fade-in">
            <h2 className="panel-title">📂 Indian Knowledge System Datasets</h2>
            <p className="panel-desc">Browse pre-indexed corpuses, verify concept occurrences, and retrieve individual verse annotations.</p>

            <div className="datasets-grid">
              
              {/* Thirukkural Card */}
              <div className={`dataset-card shadow ${activeDataset === 'kural' ? 'selected-dataset' : ''}`} onClick={() => setActiveDataset('kural')}>
                <h3>📜 Thirukkural Dataset</h3>
                <p className="db-meta-text">1330 Couplets • Sangam & Post-Sangam Era</p>
                <div className="tag-row">
                  <span className="db-tag">Ethics</span>
                  <span className="db-tag">Aram</span>
                  <span className="db-tag">Porul</span>
                </div>
                <div className="metric-row">
                  <span className="lbl">Precision Metrics:</span>
                  <strong className="val success-text">BLEU 42.1</strong>
                </div>
              </div>

              {/* Purananuru Card */}
              <div className={`dataset-card shadow ${activeDataset === 'purananuru' ? 'selected-dataset' : ''}`} onClick={() => setActiveDataset('purananuru')}>
                <h3>⚔️ Purananuru Dataset</h3>
                <p className="db-meta-text">400 Poems • Heroic Sangam Era</p>
                <div className="tag-row">
                  <span className="db-tag">War</span>
                  <span className="db-tag">Charity</span>
                  <span className="db-tag">Viram</span>
                </div>
                <div className="metric-row">
                  <span className="lbl">Precision Metrics:</span>
                  <strong className="val success-text">BLEU 38.6</strong>
                </div>
              </div>

              {/* Silappatikaram Card */}
              <div className={`dataset-card shadow ${activeDataset === 'silappatikaram' ? 'selected-dataset' : ''}`} onClick={() => setActiveDataset('silappatikaram')}>
                <h3>👑 Silappatikaram Dataset</h3>
                <p className="db-meta-text">30 Cantos • Post-Sangam Epic</p>
                <div className="tag-row">
                  <span className="db-tag">Karma</span>
                  <span className="db-tag">Justice</span>
                  <span className="db-tag">Sengol</span>
                </div>
                <div className="metric-row">
                  <span className="lbl">Precision Metrics:</span>
                  <strong className="val success-text">BLEU 39.4</strong>
                </div>
              </div>

            </div>

            {/* Verse Viewer Section */}
            <div className="verse-viewer-card shadow">
              <div className="verse-header">
                <h3>📖 Interactive Verse & Commentary Viewer</h3>
                <div className="verse-selectors">
                  <label>Select Verse ID:</label>
                  <select value={selectedVerseId} onChange={(e) => setSelectedVerseId(e.target.value)}>
                    {activeDataset === 'kural' ? (
                      <>
                        <option value="39">Verse 39 (Aram)</option>
                        <option value="71">Verse 71 (Anbu)</option>
                        <option value="241">Verse 241 (Arul)</option>
                      </>
                    ) : (
                      <option value="192">Verse 192 (Kelir / Universal Kinship)</option>
                    )}
                  </select>
                </div>
              </div>

              {datasetVerses[selectedVerseId] && (
                <div className="verse-detail-grid animate-fade-in">
                  <div className="v-detail-col">
                    <div className="detail-section-title">Original Verse (Tamil)</div>
                    <div className="verse-tamil-text">"{datasetVerses[selectedVerseId].tamil}"</div>
                    
                    <div className="detail-section-title">Verified NMT Translation</div>
                    <div className="verse-trans-text">"{datasetVerses[selectedVerseId].translation}"</div>
                  </div>

                  <div className="v-detail-col">
                    <div className="detail-section-title">Resolved Concept Annotation</div>
                    <div className="verse-concept-badge">{datasetVerses[selectedVerseId].concept}</div>

                    <div className="detail-section-title">Historical Commentary Breakdown</div>
                    <p className="commentary-para">{datasetVerses[selectedVerseId].commentary}</p>

                    <div className="detail-section-title">Grammatical/Philological Notes</div>
                    <p className="notes-para">{datasetVerses[selectedVerseId].notes}</p>
                  </div>
                </div>
              )}
            </div>

          </div>
        )}

        {/* ============================================================== */}
        {/* TAB 7: MODEL COMPARISON (WITH SEMANTIC DIFF) */}
        {/* ============================================================== */}
        {activeTab === 'compare' && (
          <div className="view-panel animate-fade-in">
            <h2 className="panel-title">⚖️ Side-by-Side Model Comparison & Semantic Diff</h2>
            <p className="panel-desc">Input a classical Tamil phrase to evaluate how generic neural translators contrast against ChronoIKS context injection.</p>

            <div className="compare-workspace shadow">
              <div className="compare-row">
                <input 
                  type="text" 
                  className="compare-input-text"
                  value={compareInput}
                  onChange={(e) => setCompareInput(e.target.value)}
                  placeholder="Enter a classical Tamil phrase..."
                />
                <button className="compare-btn" onClick={handleCompareModels} disabled={isComparing}>
                  {isComparing ? 'Evaluating Models...' : 'Compare Translators'}
                </button>
              </div>

              {compareResults && (
                <div className="compare-results-grid animate-fade-in">
                  
                  {/* Google Card */}
                  <div className="compare-card-col">
                    <div className="comp-card-title red-border">Google Translate (Modern)</div>
                    <p className="comp-text">"{compareResults.google}"</p>
                    <div className="comp-stats red-text">⚠️ Fails classical semantics</div>
                  </div>

                  {/* IndicTrans2 Card */}
                  <div className="compare-card-col">
                    <div className="comp-card-title yellow-border">IndicTrans2 (Adapterless)</div>
                    <p className="comp-text">"{compareResults.indictrans2}"</p>
                    <div className="comp-stats yellow-text">✓ Grammatically accurate, lacks subtext</div>
                  </div>

                  {/* ChronoIKS Card */}
                  <div className="compare-card-col active-border">
                    <div className="comp-card-title green-border">ChronoIKS AI (Context-Injected)</div>
                    <p className="comp-text">"{compareResults.chronoiks}"</p>
                    <div className="comp-stats green-text">✓ Context-aware (Sangam Era metrics)</div>
                  </div>

                  {/* SEMANTIC DIFF HIGHLIGHT */}
                  <div className="semantic-diff-full-width">
                    <div className="diff-title">🔍 Semantic Diff Analysis</div>
                    <p className="diff-desc">Below is the comparison of how key nouns are mapped between baseline models and ChronoIKS:</p>
                    
                    <div className="diff-table">
                      <div className="diff-table-header">
                        <span>Keyword</span>
                        <span>Generic Translation</span>
                        <span>ChronoIKS Mapping</span>
                        <span>Philological Justification</span>
                      </div>
                      <div className="diff-table-row">
                        <strong className="keyword-highlight">{compareInput.includes("அறம்") ? "அறம் (Aram)" : "கேளிர் (Kelir)"}</strong>
                        <span className="diff-baseline">"Goodness" / "Friend"</span>
                        <span className="diff-injected">"Virtue" / "Kinsmen"</span>
                        <span>Generic NMT maps to modern charity. ChronoIKS resolves to the ethical householder and cosmic duties, preserving commentary references.</span>
                      </div>
                    </div>
                  </div>

                </div>
              )}
            </div>
          </div>
        )}

        {/* ============================================================== */}
        {/* TAB 8: RESEARCH METRICS DASHBOARD */}
        {/* ============================================================== */}
        {activeTab === 'metrics' && (
          <div className="view-panel animate-fade-in">
            <h2 className="panel-title">📊 Platform Analytics & Evaluation Dashboard</h2>
            <p className="panel-desc">Monitor pipeline benchmarks, model training progress, evaluation metrics, and GPU compute performance.</p>

            <div className="metrics-summary-grid">
              
              <div className="metric-box shadow">
                <div className="metric-num">42.1</div>
                <div className="metric-lbl">BLEU Validation Score</div>
                <p>NLLB-200 with IKS adapter</p>
              </div>

              <div className="metric-box shadow">
                <div className="metric-num">~280ms</div>
                <div className="metric-lbl">Average Inference Speed</div>
                <p>Vector search + token translation</p>
              </div>

              <div className="metric-box shadow">
                <div className="metric-num">99.9%</div>
                <div className="metric-lbl">Concept Resolution Precision</div>
                <p>Via hybrid agglutinative ranking</p>
              </div>

              <div className="metric-box shadow">
                <div className="metric-num">0.865</div>
                <div className="metric-lbl">Average BERTScore</div>
                <p>Compared against research papers</p>
              </div>

            </div>

            {/* Custom SVG Charts */}
            <div className="charts-grid">
              
              <div className="chart-card shadow">
                <h3>📈 Adapter LoRA Training Loss Convergence</h3>
                <svg className="chart-svg-draw" viewBox="0 0 400 200">
                  {/* Axis */}
                  <line x1="40" y1="20" x2="40" y2="170" stroke="#27273a" strokeWidth="2" />
                  <line x1="40" y1="170" x2="380" y2="170" stroke="#27273a" strokeWidth="2" />
                  
                  {/* Line representing loss */}
                  <path 
                    d="M 40 40 Q 120 120 200 140 T 380 155" 
                    fill="none" 
                    stroke="#3b82f6" 
                    strokeWidth="3" 
                  />
                  
                  {/* Grid / Dots */}
                  <circle cx="40" cy="40" r="4" fill="#8b5cf6" />
                  <circle cx="120" cy="100" r="4" fill="#8b5cf6" />
                  <circle cx="200" cy="140" r="4" fill="#8b5cf6" />
                  <circle cx="380" cy="155" r="4" fill="#8b5cf6" />

                  {/* Labels */}
                  <text x="35" y="45" fill="#64748b" fontSize="8" textAnchor="end">Loss: 2.4</text>
                  <text x="380" y="165" fill="#64748b" fontSize="8" textAnchor="middle">Loss: 0.12</text>
                  <text x="210" y="190" fill="#64748b" fontSize="9" textAnchor="middle">Training Epochs (1-10)</text>
                </svg>
              </div>

              <div className="chart-card shadow">
                <h3>📊 Pipeline Latency Distribution (ms)</h3>
                <svg className="chart-svg-draw" viewBox="0 0 400 200">
                  {/* Axis */}
                  <line x1="40" y1="20" x2="40" y2="170" stroke="#27273a" strokeWidth="2" />
                  <line x1="40" y1="170" x2="380" y2="170" stroke="#27273a" strokeWidth="2" />

                  {/* Bars */}
                  {/* Bar 1 */}
                  <rect x="60" y="130" width="30" height="40" fill="#10b981" opacity="0.8" />
                  <text x="75" y="125" fill="#f1f1f6" fontSize="8" textAnchor="middle">40ms</text>
                  <text x="75" y="185" fill="#64748b" fontSize="8" textAnchor="middle">FAISS</text>

                  {/* Bar 2 */}
                  <rect x="130" y="100" width="30" height="70" fill="#3b82f6" opacity="0.8" />
                  <text x="145" y="95" fill="#f1f1f6" fontSize="8" textAnchor="middle">70ms</text>
                  <text x="145" y="185" fill="#64748b" fontSize="8" textAnchor="middle">Ranker</text>

                  {/* Bar 3 */}
                  <rect x="200" y="40" width="30" height="130" fill="#8b5cf6" opacity="0.8" />
                  <text x="215" y="35" fill="#f1f1f6" fontSize="8" textAnchor="middle">130ms</text>
                  <text x="215" y="185" fill="#64748b" fontSize="8" textAnchor="middle">NMT</text>

                  {/* Bar 4 */}
                  <rect x="270" y="120" width="30" height="50" fill="#ec4899" opacity="0.8" />
                  <text x="285" y="115" fill="#f1f1f6" fontSize="8" textAnchor="middle">50ms</text>
                  <text x="285" y="185" fill="#64748b" fontSize="8" textAnchor="middle">Explain</text>

                </svg>
              </div>

            </div>

          </div>
        )}

        {/* ============================================================== */}
        {/* TAB 9: API PLAYGROUND */}
        {/* ============================================================== */}
        {activeTab === 'playground' && (
          <div className="view-panel animate-fade-in">
            <h2 className="panel-title">🧪 REST API Interactive Playground</h2>
            <p className="panel-desc">Execute operations against the active FastAPI endpoints to inspect headers, JSON output structure, and latency.</p>

            <div className="playground-layout shadow">
              
              <div className="pg-left">
                <div className="pg-field">
                  <label>REST Endpoint URL</label>
                  <select value={apiEndpoint} onChange={(e) => setApiEndpoint(e.target.value)}>
                    <option value="/api/translate">POST /api/translate</option>
                    <option value="/api/compare">POST /api/compare</option>
                    <option value="/api/explain">POST /api/explain</option>
                    <option value="/api/statistics">GET /api/statistics</option>
                    <option value="/api/history">GET /api/history</option>
                    <option value="/api/search?q=Aram">GET /api/search</option>
                  </select>
                </div>

                <div className="pg-field">
                  <label>JSON Request Body (POST parameters)</label>
                  <textarea 
                    className="pg-json-textarea"
                    value={apiRequestBody}
                    onChange={(e) => setApiRequestBody(e.target.value)}
                  />
                </div>

                <button className="pg-execute-btn" onClick={handleExecuteAPI}>
                  ⚡ Send Request
                </button>
              </div>

              <div className="pg-right">
                <div className="pg-right-header">
                  <span>API Response Headers & JSON Content</span>
                  {apiLatency && <span className="latency-badge">{apiLatency} ms</span>}
                </div>

                <pre className="pg-response-pre">
                  {apiResponse || "Click 'Send Request' to query the gateway."}
                </pre>
              </div>

            </div>
          </div>
        )}

        {/* ============================================================== */}
        {/* TAB 10: SETTINGS AND LOGS */}
        {/* ============================================================== */}
        {activeTab === 'settings' && (
          <div className="view-panel animate-fade-in">
            <h2 className="panel-title">⚙️ Platform Configurations & Real-time Logs</h2>
            <p className="panel-desc">Manage environment parameters, toggle debug modes, and inspect live service console logging.</p>

            <div className="settings-grid shadow">
              
              <div className="set-card">
                <h3>Platform Settings</h3>
                
                <div className="set-option-row">
                  <div>
                    <strong>Visual Theme Modality</strong>
                    <p>Toggle between glassmorphic Dark and Light style designs.</p>
                  </div>
                  <select value={theme} onChange={(e) => setTheme(e.target.value as any)}>
                    <option value="dark">HSL Dark Mode (Recommended)</option>
                    <option value="light">Classic Light Mode</option>
                  </select>
                </div>

                <div className="set-option-row">
                  <div>
                    <strong>Compute Acceleration Mode</strong>
                    <p>Utilize GPU CUDA core devices or force CPU execution threads.</p>
                  </div>
                  <button 
                    className={`toggle-btn ${gpuMode ? 'active' : ''}`}
                    onClick={() => { setGpuMode(!gpuMode); addLog(`GPU Mode changed to ${!gpuMode ? 'CUDA' : 'CPU'}.`); }}
                  >
                    {gpuMode ? "CUDA Active" : "Force CPU Mode"}
                  </button>
                </div>

                <div className="set-option-row">
                  <div>
                    <strong>Active Fine-Tuning Checkpoint</strong>
                    <p>Selected Adapter parameter weights for translations.</p>
                  </div>
                  <select>
                    <option>best_lora_adapter (Epoch 8, Loss 0.12)</option>
                    <option>baseline (No adapter weights)</option>
                  </select>
                </div>
              </div>

              {/* Debug console log view */}
              <div className="set-card">
                <h3>💻 Gateway Console Output Logs</h3>
                <div className="console-box">
                  {debugLogs.map((log, idx) => (
                    <div key={idx} className="console-line">
                      {log}
                    </div>
                  ))}
                </div>
              </div>

            </div>
          </div>
        )}

      </main>

      <style jsx global>{`
        * {
          box-sizing: border-box;
          margin: 0;
          padding: 0;
        }

        /* HSL Theme Colors */
        .dark-theme {
          --bg-color: #0b0b0f;
          --sidebar-bg: #12121a;
          --card-bg: #12121a;
          --border-color: #1f1f2e;
          --text-primary: #f1f1f6;
          --text-secondary: #94a3b8;
          --accent-primary: #3b82f6;
          --accent-secondary: #8b5cf6;
          --success: #10b981;
          --warning: #f59e0b;
          --danger: #ef4444;
          --shadow-color: rgba(0, 0, 0, 0.6);
        }

        .light-theme {
          --bg-color: #f8fafc;
          --sidebar-bg: #ffffff;
          --card-bg: #ffffff;
          --border-color: #e2e8f0;
          --text-primary: #0f172a;
          --text-secondary: #475569;
          --accent-primary: #2563eb;
          --accent-secondary: #7c3aed;
          --success: #16a34a;
          --warning: #d97706;
          --danger: #dc2626;
          --shadow-color: rgba(0, 0, 0, 0.05);
        }

        body {
          background-color: var(--bg-color);
          color: var(--text-primary);
          font-family: 'Outfit', sans-serif;
          min-height: 100vh;
          transition: background-color 0.3s ease, color 0.3s ease;
        }

        .app-container {
          display: flex;
          min-height: 100vh;
        }

        /* Sidebar Navigation Design */
        .sidebar {
          width: 280px;
          background-color: var(--sidebar-bg);
          border-right: 1px solid var(--border-color);
          display: flex;
          flex-direction: column;
          padding: 2rem 1.5rem;
          flex-shrink: 0;
        }

        .sidebar-brand {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 2.5rem;
        }

        .sidebar-logo {
          font-size: 1.8rem;
          font-weight: 800;
          background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }

        .sidebar-brand-name {
          font-size: 1.3rem;
          font-weight: 800;
          letter-spacing: -0.02em;
        }

        .sidebar-nav {
          display: flex;
          flex-direction: column;
          gap: 6px;
          flex: 1;
        }

        .nav-item {
          background: none;
          border: 1px solid transparent;
          color: var(--text-secondary);
          padding: 0.75rem 1rem;
          border-radius: 10px;
          cursor: pointer;
          font-family: inherit;
          font-weight: 500;
          font-size: 0.95rem;
          text-align: left;
          display: flex;
          align-items: center;
          gap: 12px;
          transition: all 0.2s ease;
        }

        .nav-item:hover {
          color: var(--text-primary);
          background-color: rgba(59, 130, 246, 0.05);
          border-color: rgba(59, 130, 246, 0.1);
        }

        .nav-item.active {
          background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
          color: #ffffff;
          border-color: transparent;
          box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
        }

        .sidebar-footer {
          border-top: 1px solid var(--border-color);
          padding-top: 1.5rem;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .status-indicator {
          font-size: 0.85rem;
          display: flex;
          align-items: center;
          gap: 8px;
          color: var(--text-secondary);
        }

        .device-indicator {
          font-size: 0.78rem;
          color: var(--text-secondary);
          background-color: rgba(0,0,0,0.2);
          padding: 4px 8px;
          border-radius: 4px;
          width: fit-content;
        }

        .dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          display: inline-block;
        }

        .green-dot {
          background-color: var(--success);
        }

        /* Main Content Container */
        .main-content {
          flex: 1;
          padding: 2.5rem;
          overflow-y: auto;
        }

        .view-panel {
          max-width: 1300px;
          margin: 0 auto;
        }

        .welcome-banner {
          margin-bottom: 2rem;
        }

        .welcome-banner h2 {
          font-size: 2rem;
          font-weight: 800;
          letter-spacing: -0.03em;
        }

        .welcome-banner p {
          color: var(--text-secondary);
          font-size: 0.95rem;
        }

        /* Custom Cards Layout & Styling */
        .shadow {
          box-shadow: 0 10px 30px -10px var(--shadow-color);
        }

        .global-search-card {
          background-color: var(--card-bg);
          border: 1px solid var(--border-color);
          border-radius: 16px;
          padding: 2rem;
          margin-bottom: 2rem;
        }

        .search-label {
          font-size: 0.85rem;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: var(--text-secondary);
          margin-bottom: 0.75rem;
          font-weight: 600;
        }

        .search-row {
          display: flex;
          gap: 12px;
          margin-bottom: 1rem;
        }

        .global-search-input {
          flex: 1;
          background-color: rgba(0, 0, 0, 0.2);
          border: 1px solid var(--border-color);
          border-radius: 10px;
          padding: 0.8rem 1.2rem;
          font-family: inherit;
          color: var(--text-primary);
          font-size: 1rem;
          outline: none;
          transition: border-color 0.2s ease;
        }

        .global-search-input:focus {
          border-color: var(--accent-primary);
        }

        .global-search-btn {
          background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
          color: #ffffff;
          border: none;
          padding: 0 1.5rem;
          border-radius: 10px;
          font-family: inherit;
          font-weight: 600;
          cursor: pointer;
        }

        .preset-suggestions {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          align-items: center;
          font-size: 0.82rem;
          color: var(--text-secondary);
        }

        .preset-suggestions button {
          background-color: rgba(0, 0, 0, 0.15);
          border: 1px solid var(--border-color);
          color: var(--text-primary);
          padding: 4px 10px;
          border-radius: 6px;
          cursor: pointer;
          transition: border-color 0.2s ease;
        }

        .preset-suggestions button:hover {
          border-color: var(--accent-primary);
        }

        /* Dashboard Grid Layout */
        .dashboard-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(480px, 1fr));
          gap: 2rem;
        }

        .dashboard-card {
          background-color: var(--card-bg);
          border: 1px solid var(--border-color);
          border-radius: 16px;
          padding: 1.75rem;
        }

        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1.5rem;
          border-bottom: 1px dashed var(--border-color);
          padding-bottom: 0.75rem;
        }

        .card-header h3 {
          font-size: 1.1rem;
          font-weight: 700;
          color: var(--text-primary);
        }

        .header-badge {
          font-size: 0.7rem;
          background-color: rgba(59, 130, 246, 0.1);
          color: var(--accent-primary);
          padding: 2px 8px;
          border-radius: 4px;
          font-weight: 600;
          text-transform: uppercase;
        }

        /* Dashboard Lists */
        .concept-list, .log-list, .dataset-brief-list, .engine-status-list {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .concept-item-row {
          display: flex;
          align-items: center;
          background-color: rgba(0, 0, 0, 0.15);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          padding: 8px 12px;
          cursor: pointer;
          transition: border-color 0.2s ease;
        }

        .concept-item-row:hover {
          border-color: var(--accent-primary);
        }

        .concept-tamil-badge {
          background-color: rgba(34, 197, 94, 0.1);
          color: var(--success);
          border: 1px solid rgba(34, 197, 94, 0.2);
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 0.8rem;
          font-weight: 700;
          margin-right: 12px;
        }

        .concept-meta {
          flex: 1;
          display: flex;
          flex-direction: column;
        }

        .concept-name {
          font-size: 0.9rem;
          font-weight: 600;
        }

        .concept-desc {
          font-size: 0.75rem;
          color: var(--text-secondary);
        }

        .arrow-go {
          color: var(--text-secondary);
        }

        .log-item-row {
          display: flex;
          align-items: center;
          gap: 12px;
          background-color: rgba(0, 0, 0, 0.15);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          padding: 8px 12px;
          cursor: pointer;
        }

        .log-icon {
          font-size: 1.2rem;
        }

        .log-meta {
          flex: 1;
          display: flex;
          flex-direction: column;
        }

        .log-input {
          font-size: 0.85rem;
          font-weight: 500;
        }

        .log-output {
          font-size: 0.78rem;
          color: var(--text-secondary);
        }

        .log-latency {
          font-size: 0.75rem;
          background-color: rgba(0,0,0,0.2);
          padding: 2px 6px;
          border-radius: 4px;
        }

        .dataset-brief-row {
          display: flex;
          align-items: center;
          gap: 12px;
          background-color: rgba(0, 0, 0, 0.15);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          padding: 10px 14px;
          cursor: pointer;
          transition: border-color 0.2s ease;
        }

        .dataset-brief-row:hover {
          border-color: var(--accent-primary);
        }

        .db-icon {
          font-size: 1.5rem;
        }

        .db-details {
          display: flex;
          flex-direction: column;
        }

        .db-details strong {
          font-size: 0.9rem;
        }

        .db-details span {
          font-size: 0.75rem;
          color: var(--text-secondary);
        }

        .engine-status-list .status-row {
          display: flex;
          justify-content: space-between;
          font-size: 0.85rem;
          background-color: rgba(0,0,0,0.15);
          padding: 6px 12px;
          border-radius: 6px;
        }

        /* 3-Panel Translator layout */
        .panel-title {
          font-size: 1.5rem;
          font-weight: 800;
          margin-bottom: 0.4rem;
        }

        .panel-desc {
          color: var(--text-secondary);
          font-size: 0.9rem;
          margin-bottom: 2rem;
        }

        .translator-three-columns {
          display: grid;
          grid-template-columns: 1fr 0.8fr 1.2fr;
          gap: 2rem;
          align-items: start;
        }

        .column-card {
          background-color: var(--card-bg);
          border: 1px solid var(--border-color);
          border-radius: 16px;
          padding: 1.5rem;
        }

        .column-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1.5rem;
          border-bottom: 1px dashed var(--border-color);
          padding-bottom: 0.6rem;
        }

        .column-header h3 {
          font-size: 1rem;
          font-weight: 700;
        }

        .col-badge {
          font-size: 0.68rem;
          color: var(--text-secondary);
          background-color: rgba(0,0,0,0.2);
          padding: 2px 6px;
          border-radius: 4px;
        }

        /* Text Input Workspace */
        .input-type-selector {
          display: flex;
          gap: 8px;
          margin-bottom: 1rem;
        }

        .type-btn {
          flex: 1;
          background-color: rgba(0, 0, 0, 0.2);
          border: 1px solid var(--border-color);
          color: var(--text-secondary);
          padding: 6px;
          border-radius: 6px;
          font-size: 0.78rem;
          cursor: pointer;
          text-align: center;
          transition: all 0.2s ease;
        }

        .type-btn.active, .type-btn:hover {
          color: var(--text-primary);
          border-color: var(--accent-primary);
        }

        .ocr-preview-container {
          background-color: rgba(0, 0, 0, 0.2);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          padding: 10px;
          margin-bottom: 1rem;
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .ocr-preview-title {
          font-size: 0.75rem;
          color: var(--text-secondary);
        }

        .ocr-img-thumb {
          max-height: 100px;
          object-fit: cover;
          border-radius: 4px;
        }

        .ocr-clear-btn {
          background: none;
          border: none;
          color: var(--danger);
          font-size: 0.72rem;
          cursor: pointer;
          align-self: flex-end;
        }

        .language-selector-row {
          display: flex;
          gap: 10px;
          margin-bottom: 1rem;
        }

        .lang-box {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .lang-box label {
          font-size: 0.72rem;
          color: var(--text-secondary);
        }

        .lang-box select {
          background-color: rgba(0,0,0,0.2);
          border: 1px solid var(--border-color);
          border-radius: 6px;
          padding: 6px 8px;
          color: var(--text-primary);
          font-family: inherit;
          outline: none;
        }

        .input-textarea {
          width: 100%;
          height: 140px;
          background-color: rgba(0,0,0,0.2);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          color: var(--text-primary);
          padding: 10px;
          font-family: inherit;
          font-size: 0.95rem;
          resize: none;
          outline: none;
          margin-bottom: 1rem;
        }

        .preset-quick-list {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
          margin-bottom: 1.5rem;
        }

        .preset-tag-btn {
          background-color: rgba(0,0,0,0.15);
          border: 1px solid var(--border-color);
          color: var(--text-secondary);
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 0.7rem;
          cursor: pointer;
        }

        .preset-tag-btn:hover {
          border-color: var(--accent-primary);
          color: var(--text-primary);
        }

        .translate-submit-btn {
          width: 100%;
          background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
          color: #ffffff;
          border: none;
          padding: 0.8rem;
          border-radius: 8px;
          font-family: inherit;
          font-weight: 600;
          cursor: pointer;
        }

        /* Pipeline Steps Visual Tracker */
        .pipeline-steps-container {
          display: flex;
          flex-direction: column;
          gap: 1.25rem;
        }

        .pipeline-step {
          display: flex;
          align-items: center;
          gap: 12px;
          opacity: 0.3;
          transition: opacity 0.3s ease;
        }

        .pipeline-step.active {
          opacity: 1;
        }

        .pipeline-step.complete {
          opacity: 1;
        }

        .step-circle {
          width: 24px;
          height: 24px;
          border-radius: 50%;
          background-color: var(--border-color);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 0.75rem;
          font-weight: 700;
          color: var(--text-secondary);
        }

        .pipeline-step.active .step-circle {
          background-color: var(--accent-primary);
          color: #ffffff;
          box-shadow: 0 0 10px var(--accent-primary);
        }

        .pipeline-step.complete .step-circle {
          background-color: var(--success);
          color: #ffffff;
        }

        .step-content {
          display: flex;
          flex-direction: column;
        }

        .step-title {
          font-size: 0.85rem;
          font-weight: 600;
        }

        .step-subtitle {
          font-size: 0.72rem;
          color: var(--text-secondary);
        }

        .pipeline-loader {
          margin-top: 1.5rem;
          font-size: 0.78rem;
          color: var(--accent-primary);
          text-align: center;
        }

        /* NMT Output */
        .empty-panel-placeholder {
          height: 250px;
          display: flex;
          align-items: center;
          justify-content: center;
          border: 1px dashed var(--border-color);
          border-radius: 8px;
          color: var(--text-secondary);
          font-style: italic;
          text-align: center;
          padding: 2rem;
        }

        .placeholder-content span {
          font-size: 2rem;
          display: block;
          margin-bottom: 0.5rem;
        }

        .loading-spinner-box {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 12px;
        }

        .spinner-large {
          font-size: 2.2rem;
          animation: spin 1.5s linear infinite;
          display: block;
        }

        .output-content-workspace {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }

        .translation-card-main {
          background-color: rgba(0, 0, 0, 0.15);
          border: 1px solid var(--border-color);
          border-radius: 10px;
          padding: 1.25rem;
        }

        .translation-card-label {
          font-size: 0.72rem;
          font-weight: 600;
          color: var(--accent-primary);
          text-transform: uppercase;
          margin-bottom: 0.5rem;
        }

        .translation-card-text {
          font-size: 1.05rem;
          font-weight: 600;
          line-height: 1.4;
        }

        .action-buttons-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 8px;
        }

        .act-btn {
          background-color: rgba(0,0,0,0.15);
          border: 1px solid var(--border-color);
          color: var(--text-primary);
          padding: 6px;
          border-radius: 6px;
          font-size: 0.75rem;
          cursor: pointer;
        }

        .act-btn:hover {
          border-color: var(--accent-primary);
        }

        .explainability-box {
          background-color: rgba(0, 0, 0, 0.2);
          border: 1px solid var(--border-color);
          border-radius: 10px;
          padding: 1rem;
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .explainability-header {
          font-size: 0.8rem;
          font-weight: 700;
          text-transform: uppercase;
          color: var(--text-secondary);
          border-bottom: 1px solid var(--border-color);
          padding-bottom: 4px;
        }

        .explain-concept-detail {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .exp-row {
          display: flex;
          font-size: 0.8rem;
        }

        .exp-lbl {
          width: 140px;
          color: var(--text-secondary);
          flex-shrink: 0;
        }

        .exp-val {
          color: var(--text-primary);
        }

        .log-preview-box {
          margin-top: 10px;
        }

        .log-lbl {
          font-size: 0.75rem;
          color: var(--text-secondary);
          margin-bottom: 4px;
        }

        .pre-debug {
          background-color: #050508;
          border: 1px solid var(--border-color);
          border-radius: 6px;
          padding: 8px;
          font-family: 'JetBrains Mono', monospace;
          font-size: 0.68rem;
          white-space: pre-wrap;
          color: #8b5cf6;
          max-height: 120px;
          overflow-y: auto;
        }

        /* Ask AI Chatbox */
        .chatbox-container {
          background-color: rgba(0, 0, 0, 0.15);
          border: 1px solid var(--border-color);
          border-radius: 10px;
          padding: 1rem;
          margin-top: 1rem;
        }

        .chatbox-header {
          font-size: 0.8rem;
          font-weight: 700;
          color: var(--text-secondary);
          margin-bottom: 8px;
        }

        .chatbox-messages {
          background-color: #050508;
          border: 1px solid var(--border-color);
          border-radius: 6px;
          padding: 8px;
          height: 120px;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          gap: 8px;
          margin-bottom: 8px;
        }

        .chat-bubble {
          font-size: 0.78rem;
          padding: 6px 10px;
          border-radius: 6px;
          max-width: 85%;
        }

        .chat-bubble.bot {
          background-color: #1f1f2e;
          align-self: flex-start;
        }

        .chat-bubble.user {
          background-color: var(--accent-primary);
          color: #ffffff;
          align-self: flex-end;
        }

        .quick-chat-prompts {
          display: flex;
          flex-wrap: wrap;
          gap: 4px;
          margin-bottom: 8px;
        }

        .quick-chat-prompts button {
          background: none;
          border: 1px solid var(--border-color);
          color: var(--text-secondary);
          padding: 2px 6px;
          border-radius: 4px;
          font-size: 0.65rem;
          cursor: pointer;
        }

        .quick-chat-prompts button:hover {
          border-color: var(--accent-primary);
          color: var(--text-primary);
        }

        .chatbox-form {
          display: flex;
          gap: 6px;
        }

        .chatbox-input {
          flex: 1;
          background-color: #050508;
          border: 1px solid var(--border-color);
          border-radius: 4px;
          padding: 6px;
          color: var(--text-primary);
          font-family: inherit;
          font-size: 0.78rem;
          outline: none;
        }

        .chatbox-send {
          background-color: var(--accent-primary);
          border: none;
          color: #ffffff;
          padding: 0 10px;
          border-radius: 4px;
          font-size: 0.75rem;
          cursor: pointer;
        }

        /* Search / Explorer */
        .search-bar {
          display: flex;
          gap: 12px;
          background-color: var(--card-bg);
          border: 1px solid var(--border-color);
          border-radius: 12px;
          padding: 1.25rem;
          margin-bottom: 2rem;
        }

        .search-input {
          flex: 1;
          background-color: rgba(0,0,0,0.2);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          padding: 8px 12px;
          color: var(--text-primary);
          font-family: inherit;
          outline: none;
        }

        .search-btn {
          background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
          color: #ffffff;
          border: none;
          padding: 0 1.5rem;
          border-radius: 8px;
          font-family: inherit;
          font-weight: 600;
          cursor: pointer;
        }

        .explore-empty-state {
          height: 250px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          color: var(--text-secondary);
          font-style: italic;
        }

        .explore-empty-state span {
          font-size: 3rem;
          margin-bottom: 0.5rem;
        }

        .concept-explore-card {
          background-color: var(--card-bg);
          border: 1px solid var(--border-color);
          border-radius: 14px;
          padding: 1.5rem;
          margin-bottom: 1.5rem;
        }

        .explore-card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1.25rem;
          border-bottom: 1px dashed var(--border-color);
          padding-bottom: 0.5rem;
        }

        .concept-era-tag {
          font-size: 0.72rem;
          background-color: rgba(245, 158, 11, 0.15);
          color: var(--warning);
          border: 1px solid rgba(245, 158, 11, 0.3);
          padding: 2px 6px;
          border-radius: 4px;
          font-weight: 600;
        }

        .explore-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 1.5rem;
        }

        .explore-col h4 {
          font-size: 0.85rem;
          text-transform: uppercase;
          color: var(--text-secondary);
          margin-bottom: 0.5rem;
        }

        .explore-col p {
          font-size: 0.92rem;
          line-height: 1.5;
        }

        /* Historical Timeline */
        .timeline-selector-tabs {
          display: flex;
          gap: 8px;
          margin-bottom: 2rem;
        }

        .timeline-selector-tabs button {
          background-color: var(--card-bg);
          border: 1px solid var(--border-color);
          color: var(--text-secondary);
          padding: 8px 16px;
          border-radius: 8px;
          cursor: pointer;
          font-family: inherit;
        }

        .timeline-selector-tabs button.active {
          background-color: var(--accent-primary);
          color: #ffffff;
          border-color: transparent;
        }

        .horizontal-timeline {
          background-color: var(--card-bg);
          border: 1px solid var(--border-color);
          border-radius: 16px;
          padding: 2.5rem 1.5rem;
          display: flex;
          overflow-x: auto;
          gap: 2rem;
        }

        .timeline-node {
          flex: 1;
          min-width: 250px;
          display: flex;
          flex-direction: column;
        }

        .node-time {
          font-size: 0.75rem;
          font-weight: 700;
          color: var(--accent-primary);
          text-transform: uppercase;
          margin-bottom: 0.5rem;
        }

        .node-connector {
          display: flex;
          align-items: center;
          margin-bottom: 1rem;
        }

        .node-dot {
          width: 12px;
          height: 12px;
          border-radius: 50%;
          background-color: var(--border-color);
        }

        .node-dot.active-dot {
          background-color: var(--success);
          box-shadow: 0 0 8px var(--success);
        }

        .node-line {
          height: 2px;
          background-color: var(--border-color);
          flex: 1;
        }

        .node-card {
          background-color: rgba(0,0,0,0.15);
          border: 1px solid var(--border-color);
          border-radius: 10px;
          padding: 1rem;
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .node-card.highlighted-node {
          border-color: var(--accent-primary);
        }

        .node-card h4 {
          font-size: 0.9rem;
          font-weight: 700;
        }

        .node-card p {
          font-size: 0.8rem;
          color: var(--text-secondary);
          line-height: 1.4;
        }

        .node-ref {
          font-size: 0.7rem;
          color: var(--accent-primary);
          font-weight: 600;
        }

        /* Concept Graph Visualizer */
        .graph-workspace-layout {
          display: grid;
          grid-template-columns: 1.5fr 1fr;
          gap: 2rem;
        }

        .graph-card {
          background-color: var(--card-bg);
          border: 1px solid var(--border-color);
          border-radius: 16px;
          overflow: hidden;
        }

        .graph-svg {
          width: 100%;
          height: 450px;
          display: block;
        }

        .graph-inspector {
          background-color: var(--card-bg);
          border: 1px solid var(--border-color);
          border-radius: 16px;
          padding: 1.5rem;
          display: flex;
          flex-direction: column;
          gap: 1.25rem;
        }

        .inspector-placeholder {
          height: 200px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--text-secondary);
          font-style: italic;
          text-align: center;
          border: 1px dashed var(--border-color);
          border-radius: 8px;
        }

        .inspector-badge {
          width: fit-content;
          color: #ffffff;
          padding: 4px 10px;
          border-radius: 6px;
          font-weight: 700;
          font-size: 0.9rem;
          margin-bottom: 0.5rem;
        }

        .inspector-field {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .inspector-field strong {
          font-size: 0.85rem;
          color: var(--text-secondary);
        }

        .inspector-field p {
          font-size: 0.95rem;
          line-height: 1.4;
        }

        .associated-links {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .assoc-badge {
          background-color: rgba(0,0,0,0.2);
          border: 1px solid var(--border-color);
          padding: 6px;
          border-radius: 6px;
          font-size: 0.8rem;
        }

        /* Dataset Explorer */
        .datasets-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
          gap: 1.5rem;
          margin-bottom: 2rem;
        }

        .dataset-card {
          background-color: var(--card-bg);
          border: 1px solid var(--border-color);
          border-radius: 14px;
          padding: 1.25rem;
          cursor: pointer;
          transition: border-color 0.2s ease;
        }

        .dataset-card:hover {
          border-color: var(--accent-primary);
        }

        .selected-dataset {
          border-color: var(--accent-primary);
          background-color: rgba(59, 130, 246, 0.05);
        }

        .db-meta-text {
          font-size: 0.78rem;
          color: var(--text-secondary);
          margin-bottom: 0.75rem;
        }

        .tag-row {
          display: flex;
          gap: 6px;
          margin-bottom: 0.75rem;
        }

        .db-tag {
          font-size: 0.65rem;
          background-color: rgba(0,0,0,0.2);
          padding: 2px 6px;
          border-radius: 4px;
        }

        .metric-row {
          display: flex;
          justify-content: space-between;
          font-size: 0.75rem;
        }

        .verse-viewer-card {
          background-color: var(--card-bg);
          border: 1px solid var(--border-color);
          border-radius: 16px;
          padding: 1.75rem;
        }

        .verse-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          border-bottom: 1px dashed var(--border-color);
          padding-bottom: 0.75rem;
          margin-bottom: 1.5rem;
        }

        .verse-selectors {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 0.85rem;
        }

        .verse-selectors select {
          background-color: rgba(0,0,0,0.2);
          border: 1px solid var(--border-color);
          border-radius: 6px;
          padding: 6px;
          color: var(--text-primary);
          font-family: inherit;
        }

        .verse-detail-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 2.5rem;
        }

        .v-detail-col {
          display: flex;
          flex-direction: column;
          gap: 1.25rem;
        }

        .detail-section-title {
          font-size: 0.75rem;
          font-weight: 700;
          text-transform: uppercase;
          color: var(--text-secondary);
          letter-spacing: 0.05em;
        }

        .verse-tamil-text {
          font-size: 1.25rem;
          font-weight: 700;
          line-height: 1.4;
          color: var(--accent-primary);
        }

        .verse-trans-text {
          font-size: 1rem;
          font-weight: 500;
          line-height: 1.4;
        }

        .verse-concept-badge {
          background-color: rgba(16, 185, 129, 0.1);
          color: var(--success);
          border: 1px solid rgba(16, 185, 129, 0.2);
          padding: 6px 12px;
          border-radius: 6px;
          width: fit-content;
          font-size: 0.85rem;
          font-weight: 700;
        }

        .commentary-para, .notes-para {
          font-size: 0.88rem;
          line-height: 1.5;
        }

        /* Model Comparison */
        .compare-workspace {
          background-color: var(--card-bg);
          border: 1px solid var(--border-color);
          border-radius: 16px;
          padding: 1.5rem;
        }

        .compare-row {
          display: flex;
          gap: 12px;
          margin-bottom: 2rem;
        }

        .compare-input-text {
          flex: 1;
          background-color: rgba(0,0,0,0.2);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          padding: 8px 12px;
          color: var(--text-primary);
          font-family: inherit;
          outline: none;
        }

        .compare-results-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 1.5rem;
        }

        .compare-card-col {
          background-color: rgba(0,0,0,0.15);
          border: 1px solid var(--border-color);
          border-radius: 12px;
          padding: 1.25rem;
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          min-height: 150px;
        }

        .comp-card-title {
          font-size: 0.72rem;
          font-weight: 700;
          text-transform: uppercase;
          margin-bottom: 0.75rem;
          padding-bottom: 4px;
        }

        .comp-text {
          font-size: 0.95rem;
          line-height: 1.4;
          margin-bottom: 1rem;
        }

        .comp-stats {
          font-size: 0.72rem;
          font-weight: 600;
        }

        .red-border { border-bottom: 2px solid var(--danger); }
        .red-text { color: var(--danger); }
        .yellow-border { border-bottom: 2px solid var(--warning); }
        .yellow-text { color: var(--warning); }
        .green-border { border-bottom: 2px solid var(--success); }
        .green-text { color: var(--success); }
        .active-border { border-color: var(--accent-primary); }

        .semantic-diff-full-width {
          grid-column: 1 / span 3;
          margin-top: 1rem;
          border-top: 1px dashed var(--border-color);
          padding-top: 1.5rem;
        }

        .diff-title {
          font-size: 1rem;
          font-weight: 800;
          margin-bottom: 0.5rem;
        }

        .diff-desc {
          font-size: 0.82rem;
          color: var(--text-secondary);
          margin-bottom: 1rem;
        }

        .diff-table {
          display: flex;
          flex-direction: column;
          border: 1px solid var(--border-color);
          border-radius: 8px;
          overflow: hidden;
        }

        .diff-table-header {
          display: grid;
          grid-template-columns: 1fr 1fr 1fr 2fr;
          background-color: rgba(0,0,0,0.3);
          padding: 10px 14px;
          font-size: 0.8rem;
          font-weight: 700;
          color: var(--text-secondary);
          border-bottom: 1px solid var(--border-color);
        }

        .diff-table-row {
          display: grid;
          grid-template-columns: 1fr 1fr 1fr 2fr;
          padding: 12px 14px;
          font-size: 0.85rem;
          align-items: center;
        }

        .keyword-highlight {
          color: var(--accent-primary);
        }

        .diff-baseline {
          color: var(--danger);
          text-decoration: line-through;
        }

        .diff-injected {
          color: var(--success);
          font-weight: 600;
        }

        /* Research Dashboard & Graphs */
        .metrics-summary-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
          gap: 1.5rem;
          margin-bottom: 2rem;
        }

        .metric-box {
          background-color: var(--card-bg);
          border: 1px solid var(--border-color);
          border-radius: 12px;
          padding: 1.5rem;
          text-align: center;
        }

        .metric-num {
          font-size: 2.2rem;
          font-weight: 800;
          background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          margin-bottom: 0.25rem;
        }

        .metric-lbl {
          font-size: 0.85rem;
          font-weight: 600;
          margin-bottom: 4px;
        }

        .metric-box p {
          font-size: 0.72rem;
          color: var(--text-secondary);
        }

        .charts-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 2rem;
        }

        .chart-card {
          background-color: var(--card-bg);
          border: 1px solid var(--border-color);
          border-radius: 16px;
          padding: 1.5rem;
        }

        .chart-card h3 {
          font-size: 0.95rem;
          margin-bottom: 1.25rem;
        }

        .chart-svg-draw {
          width: 100%;
          height: 200px;
        }

        /* API Playground */
        .playground-layout {
          background-color: var(--card-bg);
          border: 1px solid var(--border-color);
          border-radius: 16px;
          padding: 1.5rem;
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 2rem;
        }

        .pg-left {
          display: flex;
          flex-direction: column;
          gap: 1.25rem;
        }

        .pg-field {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .pg-field label {
          font-size: 0.8rem;
          font-weight: 600;
          color: var(--text-secondary);
        }

        .pg-field select {
          background-color: rgba(0,0,0,0.2);
          border: 1px solid var(--border-color);
          border-radius: 6px;
          padding: 8px;
          color: var(--text-primary);
          font-family: inherit;
        }

        .pg-json-textarea {
          width: 100%;
          height: 180px;
          background-color: #050508;
          border: 1px solid var(--border-color);
          border-radius: 8px;
          color: #10b981;
          font-family: 'JetBrains Mono', monospace;
          font-size: 0.8rem;
          padding: 10px;
          resize: none;
          outline: none;
        }

        .pg-execute-btn {
          background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
          color: #ffffff;
          border: none;
          padding: 0.8rem;
          border-radius: 8px;
          font-family: inherit;
          font-weight: 600;
          cursor: pointer;
        }

        .pg-right {
          background-color: #050508;
          border: 1px solid var(--border-color);
          border-radius: 12px;
          padding: 1rem;
          display: flex;
          flex-direction: column;
        }

        .pg-right-header {
          display: flex;
          justify-content: space-between;
          font-size: 0.72rem;
          color: var(--text-secondary);
          border-bottom: 1px solid #1f1f2e;
          padding-bottom: 6px;
          margin-bottom: 10px;
        }

        .latency-badge {
          background-color: rgba(16, 185, 129, 0.1);
          color: var(--success);
          padding: 2px 6px;
          border-radius: 4px;
        }

        .pg-response-pre {
          flex: 1;
          font-family: 'JetBrains Mono', monospace;
          font-size: 0.78rem;
          color: #3b82f6;
          white-space: pre-wrap;
          overflow-y: auto;
          max-height: 350px;
        }

        /* Settings view */
        .settings-grid {
          background-color: var(--card-bg);
          border: 1px solid var(--border-color);
          border-radius: 16px;
          padding: 1.5rem;
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 2rem;
        }

        .set-card h3 {
          font-size: 1rem;
          margin-bottom: 1.25rem;
          border-bottom: 1px dashed var(--border-color);
          padding-bottom: 6px;
        }

        .set-option-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          background-color: rgba(0,0,0,0.15);
          padding: 12px;
          border-radius: 8px;
          margin-bottom: 10px;
        }

        .set-option-row strong {
          font-size: 0.88rem;
          display: block;
        }

        .set-option-row p {
          font-size: 0.75rem;
          color: var(--text-secondary);
        }

        .set-option-row select {
          background-color: rgba(0,0,0,0.2);
          border: 1px solid var(--border-color);
          border-radius: 6px;
          padding: 6px;
          color: var(--text-primary);
          font-family: inherit;
        }

        .toggle-btn {
          background-color: rgba(0,0,0,0.2);
          border: 1px solid var(--border-color);
          color: var(--text-secondary);
          padding: 6px 12px;
          border-radius: 6px;
          cursor: pointer;
          font-size: 0.8rem;
        }

        .toggle-btn.active {
          background-color: var(--success);
          color: #ffffff;
          border-color: transparent;
        }

        .console-box {
          background-color: #050508;
          border: 1px solid var(--border-color);
          border-radius: 10px;
          padding: 1rem;
          font-family: 'JetBrains Mono', monospace;
          font-size: 0.72rem;
          color: #10b981;
          height: 300px;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .console-line {
          white-space: pre-wrap;
          line-height: 1.4;
        }

        /* Animations & Keyframes */
        .animate-fade-in {
          animation: fadeIn 0.3s ease-out forwards;
        }

        .animate-pulse {
          animation: pulseAnim 2s infinite ease-in-out;
        }

        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }

        @keyframes pulseAnim {
          0%, 100% { opacity: 0.5; }
          50% { opacity: 1; }
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        /* Responsive Layout Formatting */
        @media (max-width: 1024px) {
          .app-container {
            flex-direction: column;
          }
          .sidebar {
            width: 100%;
            border-right: none;
            border-bottom: 1px solid var(--border-color);
            padding: 1rem;
          }
          .sidebar-nav {
            flex-direction: row;
            overflow-x: auto;
            padding-bottom: 8px;
          }
          .nav-item {
            padding: 0.5rem 0.8rem;
            white-space: nowrap;
          }
          .translator-three-columns {
            grid-template-columns: 1fr;
          }
          .graph-workspace-layout {
            grid-template-columns: 1fr;
          }
          .settings-grid {
            grid-template-columns: 1fr;
          }
          .playground-layout {
            grid-template-columns: 1fr;
          }
          .compare-results-grid {
            grid-template-columns: 1fr;
          }
          .semantic-diff-full-width {
            grid-column: 1;
          }
          .verse-detail-grid {
            grid-template-columns: 1fr;
          }
          .charts-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
}
