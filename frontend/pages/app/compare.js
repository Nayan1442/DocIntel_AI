import Head from 'next/head';
import { useState, useEffect } from 'react';
import { Sidebar, API } from './index';
import { useAuth } from '../../components/AuthContext';
import { GitCompare, FileText, Loader, CheckCircle, ArrowRight, Equal, AlertTriangle } from 'lucide-react';

export default function ComparePage() {
    const [documents, setDocuments] = useState([]);
    const [doc1, setDoc1] = useState('');
    const [doc2, setDoc2] = useState('');
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const { authFetch } = useAuth();

    useEffect(() => { authFetch(`${API}/documents`).then(r => r.json()).then(setDocuments).catch(() => { }); }, []);

    async function handleCompare() {
        if (!doc1 || !doc2 || doc1 === doc2) return;
        setLoading(true); setResult(null); setError(null);
        try {
            const res = await authFetch(`${API}/compare-documents`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ doc_id_1: doc1, doc_id_2: doc2 }) });
            if (res.ok) setResult(await res.json());
            else { const d = await res.json(); setError(d.detail || 'Comparison failed'); }
        } catch (err) { setError('Network error: ' + err.message); }
        finally { setLoading(false); }
    }

    return (
        <>
            <Head><title>Compare — DocIntel AI</title></Head>
            <div className="app-layout">
                <Sidebar currentPath="/app/compare" />
                <main className="main-content">
                    <div className="page-header"><h2>🔀 Document Comparison</h2><p>AI-powered side-by-side analysis</p></div>
                    {documents.length < 2 ? (
                        <div className="card"><div className="empty-state"><div className="empty-state-icon">📄</div><h3>Need at least 2 documents</h3><p>Upload more documents to use comparison</p></div></div>
                    ) : (
                        <>
                            <div className="comparison-grid">
                                <div className="card">
                                    <h3 className="card-title" style={{ marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
                                        <span style={{ background: 'var(--gradient-primary)', padding: '4px 10px', borderRadius: 'var(--radius-full)', color: 'white', fontSize: 12, fontWeight: 700 }}>A</span> Document 1
                                    </h3>
                                    <select className="input" value={doc1} onChange={e => setDoc1(e.target.value)}>
                                        <option value="">Select document...</option>
                                        {documents.filter(d => d.id !== doc2).map(d => <option key={d.id} value={d.id}>{d.original_name}</option>)}
                                    </select>
                                </div>
                                <div className="card">
                                    <h3 className="card-title" style={{ marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
                                        <span style={{ background: 'var(--gradient-cool)', padding: '4px 10px', borderRadius: 'var(--radius-full)', color: 'white', fontSize: 12, fontWeight: 700 }}>B</span> Document 2
                                    </h3>
                                    <select className="input" value={doc2} onChange={e => setDoc2(e.target.value)}>
                                        <option value="">Select document...</option>
                                        {documents.filter(d => d.id !== doc1).map(d => <option key={d.id} value={d.id}>{d.original_name}</option>)}
                                    </select>
                                </div>
                            </div>
                            <div style={{ textAlign: 'center', margin: '8px 0 28px' }}>
                                <button className="btn btn-gradient-cool" onClick={handleCompare} disabled={!doc1 || !doc2 || doc1 === doc2 || loading} style={{ padding: '12px 32px', fontSize: 15 }}>
                                    {loading ? <><Loader size={18} className="spinner" /> Analyzing...</> : <><GitCompare size={18} /> Compare Documents</>}
                                </button>
                            </div>
                            {error && <div style={{ padding: 20, background: 'rgba(244,63,94,0.06)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(244,63,94,0.15)', display: 'flex', alignItems: 'center', gap: 10, marginBottom: 24 }}><AlertTriangle size={22} style={{ color: 'var(--accent-rose)' }} /><strong style={{ color: 'var(--accent-rose)' }}>{error}</strong></div>}
                            {result && (
                                <div className="comparison-result">
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 28, padding: 16, background: 'var(--bg-glass)', borderRadius: 'var(--radius-md)' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><FileText size={18} style={{ color: 'var(--accent-blue)' }} /><span style={{ fontSize: 14, fontWeight: 600 }}>{result.doc_1?.name}</span></div>
                                        <ArrowRight size={16} style={{ color: 'var(--text-muted)' }} />
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><FileText size={18} style={{ color: 'var(--accent-indigo)' }} /><span style={{ fontSize: 14, fontWeight: 600 }}>{result.doc_2?.name}</span></div>
                                    </div>
                                    <div className="comparison-section"><h3><CheckCircle size={18} style={{ color: 'var(--accent-blue)' }} /> Overall Analysis</h3><p style={{ fontSize: 14, lineHeight: 1.8, color: 'var(--text-secondary)' }}>{result.comparison}</p></div>
                                    {result.similarities?.length > 0 && <div className="comparison-section"><h3><Equal size={18} style={{ color: 'var(--accent-emerald)' }} /> Similarities</h3>{result.similarities.map((s, i) => <div key={i} className="similarity-item">{s}</div>)}</div>}
                                    {result.differences?.length > 0 && <div className="comparison-section"><h3><GitCompare size={18} style={{ color: 'var(--accent-rose)' }} /> Key Differences</h3>{result.differences.map((d, i) => <div key={i} className="difference-item">{d}</div>)}</div>}
                                    {result.recommendation && <div style={{ padding: 16, background: 'rgba(99,102,241,0.06)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(99,102,241,0.15)' }}><h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 8 }}>💡 Recommendation</h3><p style={{ fontSize: 14, lineHeight: 1.7, color: 'var(--text-secondary)' }}>{result.recommendation}</p></div>}
                                </div>
                            )}
                        </>
                    )}
                </main>
            </div>
        </>
    );
}
