import Head from 'next/head';
import Link from 'next/link';
import { useState, useEffect } from 'react';
import { useAuth } from '../components/AuthContext';
import { FileText, Upload, MessageSquare, Search, Brain, Zap, Shield, GitCompare, Mic, ArrowRight, Sparkles, ChevronRight, CheckCircle } from 'lucide-react';

export default function LandingPage() {
    const [isVisible, setIsVisible] = useState(false);
    const { user, logout } = useAuth();

    useEffect(() => {
        setIsVisible(true);
    }, []);

    return (
        <>
            <Head>
                <title>DocIntel AI — AI Document Intelligence Platform</title>
                <meta name="description" content="Upload documents and interact with them using AI. OCR, classification, semantic search, RAG Q&A, and more." />
            </Head>

            <div className="landing-page">
                {/* ── Navbar ──────────────────────────────────── */}
                <nav className="landing-nav">
                    <div className="landing-nav-inner">
                        <div className="landing-logo">
                            <div className="landing-logo-icon">🧠</div>
                            <span>DocIntel AI</span>
                        </div>
                        <div className="landing-nav-links">
                            <a href="#features">Features</a>
                            <a href="#how-it-works">How It Works</a>
                            <a href="#tech">Tech Stack</a>
                        </div>
                        {user ? (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                <Link href="/app" className="btn btn-primary btn-sm">
                                    Dashboard <ArrowRight size={14} />
                                </Link>
                                <button className="btn btn-secondary btn-sm" onClick={logout}>
                                    Log Out
                                </button>
                            </div>
                        ) : (
                            <Link href="/login" className="btn btn-primary btn-sm">
                                Sign In <ArrowRight size={14} />
                            </Link>
                        )}
                    </div>
                </nav>

                {/* ── Hero ────────────────────────────────────── */}
                <section className={`hero-section ${isVisible ? 'visible' : ''}`}>
                    <div className="hero-glow hero-glow-1" />
                    <div className="hero-glow hero-glow-2" />
                    <div className="hero-glow hero-glow-3" />

                    <div className="hero-badge">
                        <Sparkles size={14} />
                        <span>Powered by Groq LLM + FAISS Vector Search</span>
                    </div>

                    <h1 className="hero-title">
                        Your Documents,<br />
                        <span className="hero-gradient-text">Supercharged with AI</span>
                    </h1>

                    <p className="hero-subtitle">
                        Upload any document — PDFs, scanned pages, images — and let AI extract insights,
                        answer questions, classify content, and generate comprehensive reports in seconds.
                    </p>

                    <div className="hero-actions">
                        <Link href={user ? "/app" : "/login"} className="btn btn-hero-primary">
                            Get Started <ArrowRight size={18} />
                        </Link>
                        <Link href={user ? "/app/upload" : "/login"} className="btn btn-hero-secondary">
                            <Upload size={18} /> Upload a Document
                        </Link>
                    </div>

                    {/* Floating feature cards */}
                    <div className="hero-floating-cards">
                        <div className="floating-card fc-1">
                            <MessageSquare size={20} />
                            <div>
                                <strong>Ask Anything</strong>
                                <span>RAG-powered Q&A</span>
                            </div>
                        </div>
                        <div className="floating-card fc-2">
                            <Search size={20} />
                            <div>
                                <strong>Semantic Search</strong>
                                <span>Find by meaning</span>
                            </div>
                        </div>
                        <div className="floating-card fc-3">
                            <Mic size={20} />
                            <div>
                                <strong>Voice Query</strong>
                                <span>Speak your questions</span>
                            </div>
                        </div>
                    </div>
                </section>

                {/* ── Stats bar ──────────────────────────────── */}
                <section className="stats-bar">
                    <div className="stats-bar-inner">
                        <div className="stat-item">
                            <span className="stat-number">6</span>
                            <span className="stat-text">AI Services</span>
                        </div>
                        <div className="stat-divider" />
                        <div className="stat-item">
                            <span className="stat-number">5</span>
                            <span className="stat-text">AI Agents</span>
                        </div>
                        <div className="stat-divider" />
                        <div className="stat-item">
                            <span className="stat-number">9</span>
                            <span className="stat-text">API Endpoints</span>
                        </div>
                        <div className="stat-divider" />
                        <div className="stat-item">
                            <span className="stat-number">∞</span>
                            <span className="stat-text">Documents</span>
                        </div>
                    </div>
                </section>

                {/* ── Features ───────────────────────────────── */}
                <section className="features-section" id="features">
                    <div className="section-header">
                        <span className="section-badge">Features</span>
                        <h2>Everything You Need for<br /><span className="gradient-text">Intelligent Document Processing</span></h2>
                        <p>A complete AI-powered pipeline from upload to insights</p>
                    </div>

                    <div className="features-grid">
                        <div className="feature-card feature-highlight">
                            <div className="feature-icon fi-blue"><Brain size={24} /></div>
                            <h3>RAG Question Answering</h3>
                            <p>Ask questions about your documents and get accurate, sourced answers powered by retrieval-augmented generation.</p>
                            <div className="feature-tag">Core Feature</div>
                        </div>
                        <div className="feature-card">
                            <div className="feature-icon fi-purple"><FileText size={24} /></div>
                            <h3>OCR Extraction</h3>
                            <p>Extract text from PDFs, scanned documents, and images using PyMuPDF + Tesseract OCR.</p>
                        </div>
                        <div className="feature-card">
                            <div className="feature-icon fi-emerald"><Zap size={24} /></div>
                            <h3>Auto Classification</h3>
                            <p>Automatically categorize documents — invoices, contracts, resumes, reports, and more.</p>
                        </div>
                        <div className="feature-card">
                            <div className="feature-icon fi-cyan"><Search size={24} /></div>
                            <h3>Semantic Search</h3>
                            <p>Search by meaning, not keywords. FAISS-powered vector search across all documents.</p>
                        </div>
                        <div className="feature-card">
                            <div className="feature-icon fi-orange"><Sparkles size={24} /></div>
                            <h3>AI Summarization</h3>
                            <p>Generate concise, structured summaries of any document with key points highlighted.</p>
                        </div>
                        <div className="feature-card">
                            <div className="feature-icon fi-rose"><GitCompare size={24} /></div>
                            <h3>Document Comparison</h3>
                            <p>Compare two documents side-by-side with AI-powered similarity and difference analysis.</p>
                            <div className="feature-tag new">New</div>
                        </div>
                        <div className="feature-card">
                            <div className="feature-icon fi-pink"><Mic size={24} /></div>
                            <h3>Voice Query</h3>
                            <p>Ask questions by speaking — built-in Web Speech API for hands-free interaction.</p>
                            <div className="feature-tag new">New</div>
                        </div>
                        <div className="feature-card">
                            <div className="feature-icon fi-indigo"><Shield size={24} /></div>
                            <h3>Structured Extraction</h3>
                            <p>Extract structured data fields — dates, amounts, names — with type-specific schemas.</p>
                        </div>
                    </div>
                </section>

                {/* ── How it works ───────────────────────────── */}
                <section className="how-section" id="how-it-works">
                    <div className="section-header">
                        <span className="section-badge">How It Works</span>
                        <h2>From Upload to<br /><span className="gradient-text">Actionable Insights</span></h2>
                        <p>Our multi-agent AI pipeline processes your documents in seconds</p>
                    </div>

                    <div className="steps-container">
                        <div className="step-card">
                            <div className="step-number">01</div>
                            <div className="step-icon">📤</div>
                            <h3>Upload</h3>
                            <p>Drop any PDF, image, or scanned document</p>
                        </div>
                        <div className="step-connector"><ChevronRight size={24} /></div>
                        <div className="step-card">
                            <div className="step-number">02</div>
                            <div className="step-icon">🔍</div>
                            <h3>Extract & Analyze</h3>
                            <p>OCR, chunking, embedding, and classification</p>
                        </div>
                        <div className="step-connector"><ChevronRight size={24} /></div>
                        <div className="step-card">
                            <div className="step-number">03</div>
                            <div className="step-icon">🧠</div>
                            <h3>AI Processing</h3>
                            <p>Vector indexing and LLM-powered analysis</p>
                        </div>
                        <div className="step-connector"><ChevronRight size={24} /></div>
                        <div className="step-card">
                            <div className="step-number">04</div>
                            <div className="step-icon">✨</div>
                            <h3>Get Insights</h3>
                            <p>Q&A, search, summaries, and reports</p>
                        </div>
                    </div>
                </section>

                {/* ── Tech stack ─────────────────────────────── */}
                <section className="tech-section" id="tech">
                    <div className="section-header">
                        <span className="section-badge">Tech Stack</span>
                        <h2>Built with<br /><span className="gradient-text">Modern AI Infrastructure</span></h2>
                    </div>

                    <div className="tech-grid">
                        {[
                            { name: 'FastAPI', desc: 'Async Python backend', color: '#009688' },
                            { name: 'Next.js', desc: 'React frontend', color: '#000' },
                            { name: 'MongoDB', desc: 'Document storage', color: '#47A248' },
                            { name: 'FAISS', desc: 'Vector search', color: '#3b82f6' },
                            { name: 'Groq', desc: 'LLM inference', color: '#f55036' },
                            { name: 'Tesseract', desc: 'OCR engine', color: '#8b5cf6' },
                        ].map((tech) => (
                            <div key={tech.name} className="tech-card">
                                <div className="tech-dot" style={{ background: tech.color }} />
                                <strong>{tech.name}</strong>
                                <span>{tech.desc}</span>
                            </div>
                        ))}
                    </div>
                </section>

                {/* ── CTA ────────────────────────────────────── */}
                <section className="cta-section">
                    <div className="cta-inner">
                        <h2>Ready to make your documents<br /><span className="gradient-text">intelligent?</span></h2>
                        <p>Start uploading documents and experience the power of AI-driven analysis.</p>
                        <Link href="/app" className="btn btn-hero-primary" style={{ fontSize: '18px', padding: '16px 40px' }}>
                            Launch Platform <ArrowRight size={20} />
                        </Link>
                    </div>
                </section>

                {/* ── Footer ─────────────────────────────────── */}
                <footer className="landing-footer">
                    <div className="landing-footer-inner">
                        <div className="landing-logo">
                            <div className="landing-logo-icon" style={{ width: 32, height: 32, fontSize: 16 }}>🧠</div>
                            <span>DocIntel AI</span>
                        </div>
                        <span style={{ color: 'var(--text-muted)', fontSize: '13px' }}>AI Document Intelligence Platform • Built with ❤️</span>
                    </div>
                </footer>
            </div>
        </>
    );
}
