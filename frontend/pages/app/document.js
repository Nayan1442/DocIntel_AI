import Head from 'next/head';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { Sidebar, API } from './index';
import { useAuth } from '../../components/AuthContext';
import ReactMarkdown from 'react-markdown';
import { FileText, Brain, Sparkles, Download, Loader, Tags, Blocks, Heart, Hash, Users, MapPin, Mail, Calendar, DollarSign, Building } from 'lucide-react';

const PIPELINE_STEPS = [
    { id: 'upload', label: 'Upload', icon: '📤', threshold: 5 },
    { id: 'ocr', label: 'OCR', icon: '🔍', threshold: 20 },
    { id: 'chunk', label: 'Chunk', icon: '✂️', threshold: 40 },
    { id: 'embed', label: 'Embed', icon: '🧠', threshold: 60 },
    { id: 'classify', label: 'Classify', icon: '🏷️', threshold: 80 },
    { id: 'store', label: 'Store', icon: '💾', threshold: 95 },
];

export default function DocumentPage() {
    const router = useRouter();
    const { id } = router.query;
    const [doc, setDoc] = useState(null);
    const [report, setReport] = useState(null);
    const [tags, setTags] = useState(null);
    const [sentiment, setSentiment] = useState(null);
    const [loading, setLoading] = useState(true);
    const [reportLoading, setReportLoading] = useState(false);
    const [tagsLoading, setTagsLoading] = useState(false);
    const [sentimentLoading, setSentimentLoading] = useState(false);
    const [copied, setCopied] = useState(false);
    const { authFetch } = useAuth();

    useEffect(() => {
        if (!id) return;
        fetchDoc(doc === null);

        let interval;
        if (doc && doc.status === 'processing') {
            interval = setInterval(() => {
                fetchDoc(false);
            }, 2000);
        }

        return () => {
            if (interval) clearInterval(interval);
        };
    }, [id, doc?.status]);

    async function fetchDoc(showLoading = true) {
        if (showLoading) setLoading(true);
        try {
            const r = await authFetch(`${API}/documents/${id}`);
            if (r.ok) setDoc(await r.json());
        }
        catch (e) { console.error(e); }
        finally { if (showLoading) setLoading(false); }
    }

    async function generateReport() {
        setReportLoading(true);
        try { const r = await authFetch(`${API}/report/${id}`); if (r.ok) setReport(await r.json()); }
        catch (e) { console.error(e); } finally { setReportLoading(false); }
    }

    async function runAutoTag() {
        setTagsLoading(true);
        try {
            const r = await authFetch(`${API}/auto-tag/${id}`, { method: 'POST' });
            if (r.ok) setTags(await r.json());
        } catch (e) { console.error(e); } finally { setTagsLoading(false); }
    }

    async function runSentiment() {
        setSentimentLoading(true);
        try {
            const r = await authFetch(`${API}/sentiment/${id}`, { method: 'POST' });
            if (r.ok) setSentiment(await r.json());
        } catch (e) { console.error(e); } finally { setSentimentLoading(false); }
    }

    async function downloadReport() {
        try {
            const res = await authFetch(`${API}/export-report/${id}`);
            if (res.ok) { const b = await res.blob(); const u = URL.createObjectURL(b); const a = document.createElement('a'); a.href = u; a.download = `report_${doc?.original_name || 'doc'}.txt`; a.click(); URL.revokeObjectURL(u); }
        } catch (e) { console.error(e); }
    }

    function handleCopyText() {
        if (!doc?.text_content) return;
        navigator.clipboard.writeText(doc.text_content);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    }

    function getSentimentEmoji(s) {
        const map = { positive: '😊', negative: '😟', neutral: '😐', mixed: '🤔' };
        return map[s] || '❓';
    }

    function getSentimentColor(s) {
        const map = { positive: 'var(--accent-emerald)', negative: 'var(--accent-rose)', neutral: 'var(--accent-blue)', mixed: 'var(--accent-orange)' };
        return map[s] || 'var(--text-muted)';
    }

    function getStepStatus(step) {
        const progress = doc?.progress_pct || 0;
        if (progress >= step.threshold + 15) return 'completed';
        if (progress >= step.threshold) return 'active';
        return 'pending';
    }

    const entityIcons = {
        people: <Users size={14} />, organizations: <Building size={14} />,
        dates: <Calendar size={14} />, amounts: <DollarSign size={14} />,
        emails: <Mail size={14} />, locations: <MapPin size={14} />,
    };

    return (
        <>
            <Head><title>{doc?.original_name || 'Document'} — DocIntel AI</title></Head>
            <div className="app-layout">
                <Sidebar currentPath="" />
                <main className="main-content">
                    <div className="page-header"><h2>📄 Document Analysis</h2><p>AI-powered insights, tagging, and sentiment</p></div>
                    {loading ? <div className="loading-bar" /> : !doc ? (
                        <div className="card empty-state"><div className="empty-state-icon">📄</div><h3>Document not found</h3></div>
                    ) : doc.status === 'processing' ? (
                        <div className="card" style={{ maxWidth: '780px', margin: '20px auto', padding: '40px 32px' }}>
                            <div style={{ textAlign: 'center', marginBottom: '24px' }}>
                                <Loader size={36} className="spinner" style={{ color: 'var(--accent-blue)', margin: '0 auto 12px' }} />
                                <h3 style={{ fontSize: '20px', fontWeight: 800 }}>Analyzing: {doc.original_name}</h3>
                                <p style={{ color: 'var(--text-muted)', fontSize: '14px', marginTop: '4px' }}>
                                    AI is processing this document. Follow progress below.
                                </p>
                            </div>
                            
                            <div className="pipeline-container">
                                <div className="pipeline-steps">
                                    {PIPELINE_STEPS.map((step, i) => (
                                        <div key={step.id} style={{ display: 'contents' }}>
                                            <div className={`pipeline-step ${getStepStatus(step)}`}>
                                                <div className="pipeline-step-icon">{getStepStatus(step) === 'completed' ? '✅' : step.icon}</div>
                                                <div className="pipeline-step-label">{step.label}</div>
                                            </div>
                                            {i < PIPELINE_STEPS.length - 1 && <div className={`pipeline-connector ${doc.progress_pct > step.threshold + 10 ? 'active' : ''}`} />}
                                        </div>
                                    ))}
                                </div>
                                <div className="progress-bar" style={{ marginTop: '8px' }}>
                                    <div className="progress-fill" style={{ width: `${doc.progress_pct || 15}%` }} />
                                </div>
                                {doc.status_detail && (
                                    <p style={{ marginTop: '16px', fontSize: '13px', textAlign: 'center', color: 'var(--text-secondary)', fontWeight: 500 }}>
                                        ⚙️ {doc.status_detail}
                                    </p>
                                )}
                            </div>
                        </div>
                    ) : doc.status === 'failed' ? (
                        <div className="card empty-state" style={{ padding: '60px 20px', textAlign: 'center' }}>
                            <div style={{ fontSize: '48px', marginBottom: '24px' }}>❌</div>
                            <h3 style={{ fontSize: '20px', marginBottom: '8px', color: 'var(--accent-rose)' }}>Processing Failed</h3>
                            <p style={{ color: 'var(--text-muted)', maxWidth: '450px', margin: '0 auto' }}>
                                {doc.error_message || "An error occurred during AI analysis. Please try uploading the document again."}
                            </p>
                        </div>
                    ) : (
                        <>
                            {/* Document info + action buttons */}
                            <div className="card" style={{ marginBottom: 24 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20 }}>
                                    <div className={`doc-type-icon ${doc.file_type}`} style={{ width: 56, height: 56, fontSize: 22 }}><FileText size={24} /></div>
                                    <div>
                                        <h3 style={{ fontSize: 20, fontWeight: 800 }}>{doc.original_name}</h3>
                                        <div style={{ display: 'flex', gap: 12, marginTop: 6, fontSize: 13, color: 'var(--text-muted)', alignItems: 'center' }}>
                                            <span className={`tag tag-${doc.classification || 'other'}`}>{doc.classification || 'other'}</span>
                                            <span>{doc.chunk_count} chunks</span>
                                            {doc.detected_language && (
                                                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', background: 'var(--bg-glass)', padding: '2px 8px', borderRadius: 'var(--radius-sm)', fontSize: '11px', border: '1px solid var(--border-color)' }}>
                                                    🌐 {doc.detected_language}
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                </div>
                                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                                    <button className="btn btn-primary" onClick={generateReport} disabled={reportLoading}>
                                        {reportLoading ? <><Loader size={16} className="spinner" /> Generating...</> : <><Sparkles size={16} /> AI Report</>}
                                    </button>
                                    <button className="btn btn-gradient-cool" onClick={runAutoTag} disabled={tagsLoading}>
                                        {tagsLoading ? <><Loader size={16} className="spinner" /> Extracting...</> : <><Tags size={16} /> Auto-Tag</>}
                                    </button>
                                    <button className="btn btn-secondary" onClick={runSentiment} disabled={sentimentLoading} style={{ borderColor: 'rgba(236,72,153,0.3)' }}>
                                        {sentimentLoading ? <><Loader size={16} className="spinner" /> Analyzing...</> : <><Heart size={16} /> Sentiment</>}
                                    </button>
                                    <button className="btn btn-secondary" onClick={downloadReport}><Download size={16} /> Export</button>
                                </div>
                            </div>

                            {/* Auto-Tags & Entities */}
                            {tags && (
                                <div className="card" style={{ marginBottom: 24 }}>
                                    <h3 className="card-title" style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                                        <Tags size={18} style={{ color: 'var(--accent-indigo)' }} /> Auto-Generated Tags & Entities
                                    </h3>

                                    {/* Tags */}
                                    {tags.tags?.length > 0 && (
                                        <div style={{ marginBottom: 16 }}>
                                            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 8 }}>TAGS</div>
                                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                                                {tags.tags.map((t, i) => (
                                                    <span key={i} style={{ padding: '4px 14px', borderRadius: 'var(--radius-full)', background: 'rgba(99,102,241,0.1)', color: 'var(--accent-indigo)', fontSize: 12, fontWeight: 600 }}>
                                                        <Hash size={10} style={{ verticalAlign: 'middle', marginRight: 4 }} />{t}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Keywords */}
                                    {tags.keywords?.length > 0 && (
                                        <div style={{ marginBottom: 16 }}>
                                            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 8 }}>KEYWORDS</div>
                                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                                                {tags.keywords.map((k, i) => (
                                                    <span key={i} style={{ padding: '3px 10px', borderRadius: 'var(--radius-full)', background: 'var(--bg-glass)', border: '1px solid var(--border-color)', fontSize: 12, fontWeight: 500 }}>{k}</span>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Entities */}
                                    {tags.entities && Object.entries(tags.entities).filter(([_, v]) => v?.length > 0).length > 0 && (
                                        <div>
                                            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 8 }}>ENTITIES</div>
                                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 12 }}>
                                                {Object.entries(tags.entities).filter(([_, v]) => v?.length > 0).map(([type, values]) => (
                                                    <div key={type} style={{ padding: 12, background: 'var(--bg-glass)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                                                        <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6, textTransform: 'uppercase' }}>
                                                            {entityIcons[type] || <Hash size={14} />} {type}
                                                        </div>
                                                        {values.map((v, i) => (
                                                            <div key={i} style={{ fontSize: 13, marginBottom: 4 }}>• {v}</div>
                                                        ))}
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Sentiment Analysis */}
                            {sentiment && (
                                <div className="card" style={{ marginBottom: 24 }}>
                                    <h3 className="card-title" style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                                        <Heart size={18} style={{ color: 'var(--accent-pink)' }} /> Sentiment Analysis
                                    </h3>

                                    {/* Overall */}
                                    <div style={{ display: 'flex', gap: 20, marginBottom: 20, flexWrap: 'wrap' }}>
                                        <div style={{ padding: '16px 24px', background: 'var(--bg-glass)', borderRadius: 'var(--radius-md)', textAlign: 'center', minWidth: 140 }}>
                                            <div style={{ fontSize: 32 }}>{getSentimentEmoji(sentiment.overall_sentiment)}</div>
                                            <div style={{ fontSize: 16, fontWeight: 700, color: getSentimentColor(sentiment.overall_sentiment), textTransform: 'capitalize' }}>{sentiment.overall_sentiment}</div>
                                            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Overall Sentiment</div>
                                        </div>
                                        <div style={{ padding: '16px 24px', background: 'var(--bg-glass)', borderRadius: 'var(--radius-md)', textAlign: 'center', minWidth: 140 }}>
                                            <div style={{ fontSize: 32, fontWeight: 900 }}>{Math.round((sentiment.confidence || 0) * 100)}%</div>
                                            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Confidence</div>
                                        </div>
                                        <div style={{ padding: '16px 24px', background: 'var(--bg-glass)', borderRadius: 'var(--radius-md)', textAlign: 'center', minWidth: 140 }}>
                                            <div style={{ fontSize: 18, fontWeight: 700, textTransform: 'capitalize' }}>{sentiment.tone}</div>
                                            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Tone</div>
                                        </div>
                                    </div>

                                    {/* Emotions */}
                                    {sentiment.key_emotions?.length > 0 && (
                                        <div style={{ marginBottom: 16 }}>
                                            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 8 }}>KEY EMOTIONS</div>
                                            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                                                {sentiment.key_emotions.map((e, i) => (
                                                    <span key={i} style={{ padding: '4px 12px', borderRadius: 'var(--radius-full)', background: 'rgba(236,72,153,0.08)', color: 'var(--accent-pink)', fontSize: 12, fontWeight: 600 }}>{e}</span>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Section analysis */}
                                    {sentiment.section_analysis?.length > 0 && (
                                        <div style={{ marginBottom: 16 }}>
                                            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 8 }}>SECTION ANALYSIS</div>
                                            {sentiment.section_analysis.map((s, i) => (
                                                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '8px 12px', background: 'var(--bg-glass)', borderRadius: 'var(--radius-sm)', marginBottom: 6, borderLeft: `3px solid ${getSentimentColor(s.sentiment)}` }}>
                                                    <span style={{ fontSize: 16 }}>{getSentimentEmoji(s.sentiment)}</span>
                                                    <span style={{ fontWeight: 600, fontSize: 13, textTransform: 'capitalize', minWidth: 70 }}>{s.section}</span>
                                                    <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{s.note}</span>
                                                </div>
                                            ))}
                                        </div>
                                    )}

                                    {/* Summary */}
                                    {sentiment.summary && (
                                        <p style={{ fontSize: 14, lineHeight: 1.7, color: 'var(--text-secondary)', padding: 12, background: 'var(--bg-glass)', borderRadius: 'var(--radius-sm)' }}>{sentiment.summary}</p>
                                    )}
                                </div>
                            )}

                            {/* AI Report */}
                            {report && (
                                <div className="card" style={{ marginBottom: 24 }}>
                                    {report.summary && <div className="report-section"><h3><Brain size={18} style={{ color: 'var(--accent-purple)' }} /> Summary</h3><div className="markdown-body"><ReactMarkdown>{report.summary}</ReactMarkdown></div></div>}
                                    {report.insights?.length > 0 && (
                                        <div className="report-section"><h3><Sparkles size={18} style={{ color: 'var(--accent-orange)' }} /> Key Insights</h3>
                                            <ul className="insight-list">{report.insights.map((ins, i) => <li key={i} className="insight-item"><div className="insight-bullet" />{ins}</li>)}</ul>
                                        </div>
                                    )}
                                    {report.extracted_data && <div className="report-section"><h3><Blocks size={18} style={{ color: 'var(--accent-cyan)' }} /> Extracted Data</h3><pre>{JSON.stringify(report.extracted_data, null, 2)}</pre></div>}
                                </div>
                            )}

                            {/* Raw text */}
                            {doc.text_content && (
                                <div className="card" style={{ marginBottom: 24 }}>
                                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, borderBottom: '1px solid var(--border-color)', paddingBottom: 12 }}>
                                        <h3 style={{ fontSize: 16, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8, margin: 0 }}>
                                            <FileText size={18} style={{ color: 'var(--accent-blue)' }} /> Extracted Text Preview
                                        </h3>
                                        <button className="btn btn-secondary btn-sm" onClick={handleCopyText} style={{ minWidth: 100 }}>
                                            {copied ? '✅ Copied!' : '📋 Copy Text'}
                                        </button>
                                    </div>
                                    <pre className="text-preview-block" style={{
                                        maxHeight: 400,
                                        overflow: 'auto',
                                        background: '#040711',
                                        color: '#cbd5e1',
                                        padding: '16px',
                                        borderRadius: 'var(--radius-sm)',
                                        border: '1px solid var(--border-color)',
                                        fontSize: '13px',
                                        lineHeight: 1.6,
                                        fontFamily: 'SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace',
                                        whiteSpace: 'pre-wrap',
                                        wordBreak: 'break-word',
                                    }}>
                                        {doc.text_content}
                                    </pre>
                                </div>
                            )}
                        </>
                    )}
                </main>
            </div>
        </>
    );
}
