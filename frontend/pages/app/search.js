import Head from 'next/head';
import { useState } from 'react';
import { Sidebar, API } from './index';
import { useAuth } from '../../components/AuthContext';
import { Search as SearchIcon, FileText, Loader } from 'lucide-react';

export default function SearchPage() {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [searched, setSearched] = useState(false);
    const { authFetch } = useAuth();

    async function handleSearch(e) {
        e.preventDefault();
        if (!query.trim()) return;
        setLoading(true); setSearched(true);
        try {
            const res = await authFetch(`${API}/search`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query: query.trim(), top_k: 10 }) });
            if (res.ok) {
                const data = await res.json();
                setResults(data.results || []);
            }
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    }

    const scoreColor = (s) => s >= 0.7 ? 'var(--accent-emerald)' : s >= 0.4 ? 'var(--accent-orange)' : 'var(--accent-rose)';

    return (
        <>
            <Head><title>Search — DocIntel AI</title></Head>
            <div className="app-layout">
                <Sidebar currentPath="/app/search" />
                <main className="main-content">
                    <div className="page-header">
                        <h2>🔍 Semantic Search</h2>
                        <p>Search by meaning across all your documents</p>
                    </div>
                    <form onSubmit={handleSearch}>
                        <div className="search-wrapper">
                            <div className="search-icon"><SearchIcon size={20} /></div>
                            <input className="input" placeholder="Describe what you're looking for..." value={query} onChange={e => setQuery(e.target.value)} />
                        </div>
                    </form>
                    {loading && <div className="loading-bar" />}
                    {!loading && searched && !results.length && (
                        <div className="empty-state"><div className="empty-state-icon">🔍</div><h3>No results found</h3><p>Try a different search query</p></div>
                    )}
                    <div className="search-results">
                        {results.map((r, i) => (
                            <div key={i} className="search-result-card">
                                <div className="search-result-header">
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                        <FileText size={18} style={{ color: 'var(--accent-blue)' }} />
                                        <span style={{ fontWeight: 600, fontSize: 14 }}>{r.filename || 'Document'}</span>
                                        <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Chunk {r.chunk_index}</span>
                                    </div>
                                    <div className="search-result-score" style={{ background: `${scoreColor(r.score)}18`, color: scoreColor(r.score) }}>{(r.score * 100).toFixed(0)}% match</div>
                                </div>
                                <div className="search-result-text">{r.chunk_text}</div>
                            </div>
                        ))}
                    </div>
                </main>
            </div>
        </>
    );
}
