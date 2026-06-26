import Head from 'next/head';
import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useAuth } from '../../components/AuthContext';
import { FileText, Upload, MessageSquare, Search, BarChart3, Zap, Brain, Database, GitCompare, Sun, Moon, Menu, X, ChevronLeft, ChevronRight } from 'lucide-react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const NAV_ITEMS = [
    { href: '/app', label: 'Dashboard', icon: BarChart3 },
    { href: '/app/upload', label: 'Upload', icon: Upload },
    { href: '/app/chat', label: 'AI Chat', icon: MessageSquare },
    { href: '/app/search', label: 'Search', icon: Search },
    { href: '/app/compare', label: 'Compare', icon: GitCompare },
];

function Sidebar({ currentPath, mobileOpen = false, onToggle = null }) {
    const [theme, setTheme] = useState('dark');
    const { user, logout } = useAuth();
    useEffect(() => {
        const saved = localStorage.getItem('theme') || 'dark';
        setTheme(saved);
        document.documentElement.setAttribute('data-theme', saved);
    }, []);
    function toggleTheme() {
        const next = theme === 'dark' ? 'light' : 'dark';
        setTheme(next);
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('theme', next);
    }
    return (
        <>
            <div className={`sidebar-overlay ${mobileOpen ? 'open' : ''}`} onClick={onToggle} />
            <aside className={`sidebar ${mobileOpen ? 'open' : ''}`}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', marginBottom: '16px' }}>
                    <Link href="/" style={{ textDecoration: 'none' }}>
                        <div className="sidebar-brand">
                            <div className="sidebar-brand-icon">🧠</div>
                            <h1>DocIntel AI</h1>
                        </div>
                    </Link>
                    {onToggle && (
                        <button className="mobile-close-btn" onClick={onToggle} aria-label="Close menu">
                            <X size={18} />
                        </button>
                    )}
                </div>
                <nav className="sidebar-nav">
                    {NAV_ITEMS.map(({ href, label, icon: Icon }) => (
                        <Link key={href} href={href} className={`nav-link ${currentPath === href ? 'active' : ''}`} onClick={onToggle}>
                            <Icon />
                            <span>{label}</span>
                        </Link>
                    ))}
                </nav>
                {user && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '12px 8px', borderTop: '1px solid var(--border-color)', margin: '12px 0 12px' }}>
                        <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: 'var(--gradient-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: '14px', color: 'white' }}>
                            {user.name ? user.name[0].toUpperCase() : 'U'}
                        </div>
                        <div style={{ flex: 1, overflow: 'hidden' }}>
                            <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)', whiteSpace: 'nowrap', textOverflow: 'ellipsis' }}>{user.name}</div>
                            <div style={{ fontSize: '11px', color: 'var(--text-muted)', whiteSpace: 'nowrap', textOverflow: 'ellipsis' }}>{user.email}</div>
                        </div>
                        <button className="btn btn-icon btn-sm" onClick={logout} style={{ width: '28px', height: '28px', background: 'transparent', border: 'none' }} title="Log out">
                            <span style={{ fontSize: '16px' }}>🚪</span>
                        </button>
                    </div>
                )}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 8px', borderTop: '1px solid var(--border-color)', marginTop: 'auto' }}>
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 500 }}>Groq + FAISS</span>
                    <button className="theme-toggle" onClick={toggleTheme} aria-label="Toggle theme">
                        {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
                    </button>
                </div>
            </aside>
        </>
    );
}

export { Sidebar, NAV_ITEMS, API };

export default function AppDashboard() {
    const router = useRouter();
    const { authFetch } = useAuth();
    const [documents, setDocuments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState(null);
    const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
    const [toasts, setToasts] = useState([]);
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 6;

    const showToast = (message, type = 'success') => {
        const id = Date.now();
        setToasts(prev => [...prev, { id, message, type }]);
        setTimeout(() => {
            setToasts(prev => prev.filter(t => t.id !== id));
        }, 3000);
    };

    useEffect(() => {
        fetchAll(false);
    }, []);

    useEffect(() => {
        const hasProcessing = documents.some(doc => doc.status === 'processing');
        let interval;
        if (hasProcessing) {
            interval = setInterval(() => {
                fetchAll(true);
            }, 4000);
        }
        return () => {
            if (interval) clearInterval(interval);
        };
    }, [documents]);

    async function fetchAll(silent = false) {
        try {
            const [docsRes, statsRes] = await Promise.all([
                authFetch(`${API}/documents`),
                authFetch(`${API}/stats`),
            ]);
            if (docsRes.ok) {
                setDocuments(await docsRes.json());
            } else if (!silent) {
                showToast('Failed to load documents list.', 'error');
            }
            if (statsRes.ok) {
                setStats(await statsRes.json());
            } else if (!silent) {
                showToast('Failed to load platform statistics.', 'error');
            }
            if (docsRes.ok && statsRes.ok && !silent) {
                showToast('Dashboard data updated successfully!', 'success');
            }
        } catch (err) {
            console.error(err);
            if (!silent) showToast('Network error while syncing data.', 'error');
        } finally {
            setLoading(false);
        }
    }

    function formatFileSize(bytes) {
        if (!bytes) return '—';
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / 1048576).toFixed(1) + ' MB';
    }

    function formatDate(dateStr) {
        if (!dateStr) return '—';
        return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    }

    const totalDocs = stats?.documents?.total || 0;
    const totalChunks = stats?.chunks?.total || 0;
    const recentWeek = stats?.documents?.recent_week || 0;
    const totalConversations = stats?.conversations?.total || 0;
    const totalMessages = stats?.conversations?.total_messages || 0;
    const typeDist = stats?.documents?.type_distribution || {};
    const popularDocs = stats?.popular_documents || [];
    const storageTotal = stats?.storage?.total_bytes || 0;

    const totalPages = Math.ceil(documents.length / itemsPerPage) || 1;
    const displayedDocs = documents.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

    return (
        <>
            <Head>
                <title>Dashboard — DocIntel AI</title>
                <meta name="description" content="AI Document Intelligence Platform Dashboard" />
            </Head>
            <div className="app-layout">
                <Sidebar currentPath="/app" mobileOpen={mobileSidebarOpen} onToggle={() => setMobileSidebarOpen(false)} />
                <main className="main-content">
                    <div className="page-header">
                        <button className="mobile-menu-toggle" onClick={() => setMobileSidebarOpen(true)} aria-label="Open menu">
                            <Menu size={20} />
                        </button>
                        <div style={{ flex: 1 }}>
                            <h2>📊 Dashboard</h2>
                            <p>Platform analytics powered by <code>/stats</code> API</p>
                        </div>
                    </div>

                    {/* Stats grid - from /stats API */}
                    <div className="stats-grid">
                        <div className="stat-card">
                            <div className="stat-icon"><FileText size={22} /></div>
                            <div className="stat-value">{totalDocs}</div>
                            <div className="stat-label">Total Documents</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-icon"><Database size={22} /></div>
                            <div className="stat-value">{totalChunks}</div>
                            <div className="stat-label">Indexed Chunks</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-icon"><MessageSquare size={22} /></div>
                            <div className="stat-value">{totalConversations}</div>
                            <div className="stat-label">Conversations ({totalMessages} msgs)</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-icon"><Zap size={22} /></div>
                            <div className="stat-value">{recentWeek}</div>
                            <div className="stat-label">Uploaded This Week</div>
                        </div>
                    </div>

                    {/* Type distribution + Popular docs row */}
                    <div className="dashboard-grid-two-col">
                        {/* Type distribution */}
                        <div className="card">
                            <h3 className="card-title" style={{ marginBottom: '16px' }}>📂 Document Types</h3>
                            {Object.keys(typeDist).length === 0 ? (
                                <p style={{ color: 'var(--text-muted)', fontSize: '14px' }}>No documents yet</p>
                            ) : (() => {
                                const totalTypesCount = Object.values(typeDist).reduce((a, b) => a + b, 0) || 1;
                                const colors = {
                                    invoice: '#34d399', // emerald
                                    contract: '#22d3ee', // cyan
                                    resume: '#a78bfa', // purple
                                    report: '#fbbf24', // amber
                                    other: '#818cf8', // indigo
                                };

                                let accumulatedPercentage = 0;
                                const donutSegments = Object.entries(typeDist).map(([type, count]) => {
                                    const percentage = (count / totalTypesCount) * 100;
                                    const offset = 251.2 - (251.2 * percentage) / 100;
                                    const rotation = (accumulatedPercentage * 3.6) - 90;
                                    accumulatedPercentage += percentage;
                                    return {
                                        type,
                                        count,
                                        percentage,
                                        offset,
                                        rotation,
                                        color: colors[type] || '#818cf8',
                                    };
                                });

                                return (
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '24px', flexWrap: 'wrap', minHeight: '120px' }}>
                                        {/* SVG Donut */}
                                        <div style={{ position: 'relative', width: '110px', height: '110px', flexShrink: 0 }}>
                                            <svg width="100%" height="100%" viewBox="0 0 100 100">
                                                {/* Background circle */}
                                                <circle cx="50" cy="50" r="40" fill="transparent" stroke="rgba(255,255,255,0.04)" strokeWidth="8" />
                                                {/* Segments */}
                                                {donutSegments.map((seg, idx) => (
                                                    <circle
                                                        key={idx}
                                                        cx="50"
                                                        cy="50"
                                                        r="40"
                                                        fill="transparent"
                                                        stroke={seg.color}
                                                        strokeWidth="8"
                                                        strokeDasharray="251.2"
                                                        strokeDashoffset={seg.offset}
                                                        transform={`rotate(${seg.rotation} 50 50)`}
                                                        strokeLinecap="round"
                                                        style={{ transition: 'stroke-dashoffset 0.8s ease-in-out' }}
                                                    />
                                                ))}
                                            </svg>
                                            <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', textAlign: 'center' }}>
                                                <div style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-primary)' }}>{totalDocs}</div>
                                                <div style={{ fontSize: '9px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700, letterSpacing: '0.05em' }}>Docs</div>
                                            </div>
                                        </div>

                                        {/* Legend and stats */}
                                        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px', minWidth: '120px' }}>
                                            {donutSegments.map((seg) => (
                                                <div key={seg.type} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                        <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: seg.color }} />
                                                        <span style={{ fontSize: '13px', fontWeight: 600, textTransform: 'capitalize', color: 'var(--text-secondary)' }}>{seg.type}</span>
                                                    </div>
                                                    <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)' }}>
                                                        {seg.count} <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 500 }}>({Math.round(seg.percentage)}%)</span>
                                                    </span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                );
                            })()}
                            <div style={{ marginTop: '16px', paddingTop: '12px', borderTop: '1px solid var(--border-color)', fontSize: '13px', color: 'var(--text-muted)' }}>
                                Storage: {formatFileSize(storageTotal)}
                            </div>
                        </div>

                        {/* Popular documents */}
                        <div className="card">
                            <h3 className="card-title" style={{ marginBottom: '16px' }}>🔥 Most Queried</h3>
                            {popularDocs.length === 0 ? (
                                <p style={{ color: 'var(--text-muted)', fontSize: '14px' }}>No queries yet — ask questions in AI Chat</p>
                            ) : (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                                    {popularDocs.map((d, i) => (
                                        <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', background: 'var(--bg-glass)', borderRadius: 'var(--radius-sm)' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                                <span style={{ fontSize: '16px', fontWeight: 800, color: 'var(--text-muted)' }}>#{i + 1}</span>
                                                <span style={{ fontSize: '14px', fontWeight: 500 }}>{d.name}</span>
                                            </div>
                                            <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--accent-blue)' }}>{d.query_count} queries</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Recent documents */}
                    <div className="card animate-fade-in">
                        <div className="card-header">
                            <h3 className="card-title">Recent Documents</h3>
                            <Link href="/app/upload" className="btn btn-primary btn-sm"><Upload size={14} /> Upload New</Link>
                        </div>
                        {loading ? (
                            <div className="skeleton-container">
                                <div className="skeleton-bar" style={{ width: '100%', height: '45px' }} />
                                <div className="skeleton-bar" style={{ width: '100%', height: '45px' }} />
                                <div className="skeleton-bar" style={{ width: '100%', height: '45px' }} />
                            </div>
                        ) : documents.length === 0 ? (
                            <div className="empty-state">
                                <div className="empty-state-icon">📁</div>
                                <h3>No documents yet</h3>
                                <p>Upload your first document to get started</p>
                                <Link href="/app/upload" className="btn btn-primary" style={{ marginTop: '20px' }}><Upload size={16} /> Upload Document</Link>
                            </div>
                        ) : (
                            <>
                                <div className="doc-grid">
                                    {displayedDocs.map((doc) => (
                                        <Link key={doc.id} href={`/app/document?id=${doc.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                                            <div className="doc-card">
                                                <div className="doc-card-header">
                                                    <div className={`doc-type-icon ${doc.file_type}`}><FileText size={18} /></div>
                                                    <div>
                                                        <div className="doc-card-title">{doc.original_name}</div>
                                                        <div className="doc-card-meta">{formatFileSize(doc.file_size)} • {formatDate(doc.created_at)} • {doc.chunk_count} chunks</div>
                                                    </div>
                                                </div>
                                                <div className="doc-tags" style={{ display: 'flex', gap: '8px', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
                                                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                                        {doc.status === 'processing' ? (
                                                            <span className="tag" style={{ background: 'rgba(59,130,246,0.08)', border: '1px solid var(--accent-blue)', color: 'var(--accent-blue)', textTransform: 'none' }}>⚙️ Processing...</span>
                                                        ) : doc.status === 'failed' ? (
                                                            <span className="tag" style={{ background: 'rgba(244,63,94,0.08)', border: '1px solid var(--accent-rose)', color: 'var(--accent-rose)', textTransform: 'none' }}>❌ Failed</span>
                                                        ) : (
                                                            <span className={`tag tag-${doc.classification || 'other'}`}>{doc.classification || 'other'}</span>
                                                        )}
                                                        {doc.detected_language && doc.status === 'completed' && (
                                                            <span className="tag" style={{ background: 'var(--bg-glass)', border: '1px solid var(--border-color)', color: 'var(--text-muted)', textTransform: 'none' }}>
                                                                🌐 {doc.detected_language}
                                                            </span>
                                                        )}
                                                    </div>
                                                    {doc.status === 'completed' && (
                                                        <button 
                                                            className="btn btn-secondary btn-sm" 
                                                            style={{ 
                                                                padding: '2px 8px', 
                                                                fontSize: '11px', 
                                                                borderRadius: 'var(--radius-sm)',
                                                                background: 'rgba(59,130,246,0.06)',
                                                                border: '1px solid rgba(59,130,246,0.15)',
                                                                color: 'var(--accent-blue)',
                                                                display: 'flex',
                                                                alignItems: 'center',
                                                                gap: '4px',
                                                                cursor: 'pointer',
                                                                zIndex: 10
                                                            }}
                                                            onClick={(e) => {
                                                                e.preventDefault();
                                                                e.stopPropagation();
                                                                router.push(`/app/chat?docId=${doc.id}`);
                                                            }}
                                                        >
                                                            <MessageSquare size={10} /> Chat
                                                        </button>
                                                    )}
                                                </div>
                                            </div>
                                        </Link>
                                    ))}
                                </div>
                                {totalPages > 1 && (
                                    <div className="pagination">
                                        <button
                                            className="btn btn-outline btn-sm"
                                            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                                            disabled={currentPage === 1}
                                        >
                                            <ChevronLeft size={16} /> Prev
                                        </button>
                                        <span className="pagination-info">Page {currentPage} of {totalPages}</span>
                                        <button
                                            className="btn btn-outline btn-sm"
                                            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                                            disabled={currentPage === totalPages}
                                        >
                                            Next <ChevronRight size={16} />
                                        </button>
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                </main>
            </div>

            {/* Toast Container */}
            <div className="toast-container">
                {toasts.map(t => (
                    <div key={t.id} className={`toast toast-${t.type}`}>
                        {t.message}
                    </div>
                ))}
            </div>
        </>
    );
}
