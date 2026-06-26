import Head from 'next/head';
import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Sidebar, API } from './index';
import { useAuth } from '../../components/AuthContext';
import { Upload as UploadIcon, FileText, CheckCircle, AlertCircle, Loader, Tags, Files } from 'lucide-react';

const PIPELINE_STEPS = [
    { id: 'upload', label: 'Upload', icon: '📤', threshold: 5 },
    { id: 'ocr', label: 'OCR', icon: '🔍', threshold: 20 },
    { id: 'chunk', label: 'Chunk', icon: '✂️', threshold: 40 },
    { id: 'embed', label: 'Embed', icon: '🧠', threshold: 60 },
    { id: 'classify', label: 'Classify', icon: '🏷️', threshold: 80 },
    { id: 'store', label: 'Store', icon: '💾', threshold: 95 },
];

export default function UploadPage() {
    const [uploading, setUploading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [statusDetail, setStatusDetail] = useState('');
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
    const [selectedFiles, setSelectedFiles] = useState([]);
    const [batchMode, setBatchMode] = useState(false);
    const [batchResults, setBatchResults] = useState(null);
    const { authFetch } = useAuth();

    const onDrop = useCallback((acceptedFiles) => {
        if (acceptedFiles.length > 0) {
            setSelectedFiles(acceptedFiles);
            setBatchMode(acceptedFiles.length > 1);
            setResult(null); setError(null); setBatchResults(null);
        }
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: { 'application/pdf': ['.pdf'], 'image/*': ['.png', '.jpg', '.jpeg', '.tiff', '.bmp'] },
        maxFiles: 10, maxSize: 50 * 1024 * 1024,
        multiple: true,
    });

    async function handleUpload() {
        if (!selectedFiles.length) return;
        setUploading(true); setProgress(5); setError(null); setStatusDetail('Preparing document upload...');

        try {
            if (batchMode) {
                // Batch upload — multiple files at once
                const formData = new FormData();
                selectedFiles.forEach(f => formData.append('files', f));

                const interval = setInterval(() => { setProgress(p => Math.min(p + 2, 90)); }, 600);
                const res = await authFetch(`${API}/batch-upload`, { method: 'POST', body: formData });
                clearInterval(interval);

                if (res.ok) {
                    setProgress(100);
                    setBatchResults(await res.json());
                    setSelectedFiles([]);
                } else {
                    const errData = await res.json();
                    setError(errData.detail || 'Batch upload failed');
                }
            } else {
                // Single file upload
                const formData = new FormData();
                formData.append('file', selectedFiles[0]);

                setProgress(10);
                setStatusDetail('Uploading document to server...');
                const res = await authFetch(`${API}/upload-document`, { method: 'POST', body: formData });

                if (res.ok) {
                    const uploadRes = await res.json();
                    const docId = uploadRes.id;
                    setSelectedFiles([]);

                    setProgress(15);
                    setStatusDetail('Queued for processing...');

                    let isDone = false;
                    let doc = null;
                    while (!isDone) {
                        await new Promise(r => setTimeout(r, 1500));
                        const pollRes = await authFetch(`${API}/documents/${docId}`);
                        if (pollRes.ok) {
                            doc = await pollRes.json();
                            setProgress(doc.progress_pct || 15);
                            setStatusDetail(doc.status_detail || 'Processing...');
                            if (doc.status === 'completed' || doc.status === 'failed') {
                                isDone = true;
                            }
                        } else {
                            throw new Error('Failed to retrieve processing status.');
                        }
                    }

                    if (doc.status === 'completed') {
                        setProgress(100);
                        setStatusDetail('Pipeline completed successfully!');
                        setResult(doc);
                    } else {
                        setError(doc.error_message || 'AI Ingestion pipeline failed.');
                    }
                } else {
                    const errData = await res.json();
                    setError(errData.detail || 'Upload failed');
                }
            }
        } catch (err) { setError('Network error: ' + err.message); }
        finally { setUploading(false); }
    }

    function getStepStatus(step) {
        if (progress >= step.threshold + 15) return 'completed';
        if (progress >= step.threshold) return 'active';
        return 'pending';
    }

    return (
        <>
            <Head><title>Upload — DocIntel AI</title></Head>
            <div className="app-layout">
                <Sidebar currentPath="/app/upload" />
                <main className="main-content">
                    <div className="page-header">
                        <h2>📤 Upload Documents</h2>
                        <p>Upload single or multiple files for AI-powered analysis (up to 10 at once)</p>
                    </div>

                    <div className="card" style={{ maxWidth: '780px' }}>
                        <div {...getRootProps()} className={`upload-zone ${isDragActive ? 'active' : ''}`}>
                            <input {...getInputProps()} />
                            <div className="upload-icon"><UploadIcon size={32} color="white" /></div>
                            <h3>{isDragActive ? 'Drop your files here!' : 'Drag & drop documents'}</h3>
                            <p>or <span className="highlight">click to browse</span></p>
                            <p style={{ marginTop: '12px', fontSize: '12px', color: 'var(--text-muted)' }}>PDF, PNG, JPG, TIFF • Max 50MB each • Up to 10 files</p>
                        </div>

                        {/* Selected files list */}
                        {selectedFiles.length > 0 && !result && !batchResults && (
                            <div style={{ marginTop: '24px' }}>
                                {batchMode && (
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12, padding: '8px 14px', background: 'rgba(99,102,241,0.08)', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(99,102,241,0.15)' }}>
                                        <Files size={16} style={{ color: 'var(--accent-indigo)' }} />
                                        <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--accent-indigo)' }}>Batch Upload — {selectedFiles.length} files</span>
                                    </div>
                                )}
                                {selectedFiles.map((f, i) => (
                                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '14px', padding: '10px 16px', background: 'var(--bg-glass)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', marginBottom: 6 }}>
                                        <FileText size={20} style={{ color: 'var(--accent-blue)', flexShrink: 0 }} />
                                        <div style={{ flex: 1, minWidth: 0 }}>
                                            <div style={{ fontWeight: 600, fontSize: '14px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.name}</div>
                                            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{(f.size / 1048576).toFixed(1)} MB</div>
                                        </div>
                                    </div>
                                ))}
                                <button className="btn btn-primary" onClick={handleUpload} disabled={uploading} style={{ marginTop: 12, width: '100%' }}>
                                    {uploading ? <><Loader size={16} className="spinner" /> Processing...</> : <><UploadIcon size={16} /> {batchMode ? `Upload ${selectedFiles.length} Files` : 'Upload & Analyze'}</>}
                                </button>
                            </div>
                        )}

                        {/* Processing pipeline */}
                        {uploading && (
                            <div className="pipeline-container">
                                <div className="pipeline-steps">
                                    {PIPELINE_STEPS.map((step, i) => (
                                        <div key={step.id} style={{ display: 'contents' }}>
                                            <div className={`pipeline-step ${getStepStatus(step)}`}>
                                                <div className="pipeline-step-icon">{getStepStatus(step) === 'completed' ? '✅' : step.icon}</div>
                                                <div className="pipeline-step-label">{step.label}</div>
                                            </div>
                                            {i < PIPELINE_STEPS.length - 1 && <div className={`pipeline-connector ${progress > step.threshold + 10 ? 'active' : ''}`} />}
                                        </div>
                                    ))}
                                </div>
                                <div className="progress-bar" style={{ marginTop: '8px' }}>
                                    <div className="progress-fill" style={{ width: `${progress}%` }} />
                                </div>
                                {statusDetail && (
                                    <p style={{ marginTop: '12px', fontSize: '13px', textAlign: 'center', color: 'var(--text-secondary)', fontWeight: 500 }}>
                                        ⚙️ {statusDetail}
                                    </p>
                                )}
                            </div>
                        )}

                        {/* Single success */}
                        {result && (
                            <div style={{ marginTop: '24px', padding: '24px', background: 'rgba(16, 185, 129, 0.06)', borderRadius: 'var(--radius-lg)', border: '1px solid rgba(16, 185, 129, 0.15)' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
                                    <CheckCircle size={24} style={{ color: 'var(--accent-emerald)' }} />
                                    <strong style={{ color: 'var(--accent-emerald)', fontSize: '16px' }}>Document Processed!</strong>
                                </div>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '14px' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><FileText size={16} /> {result.filename}</div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><Tags size={16} /> <span className={`tag tag-${result.classification}`}>{result.classification}</span></div>
                                </div>
                                <p style={{ color: 'var(--text-secondary)', marginTop: '12px', fontSize: '13px' }}>{result.message}</p>
                            </div>
                        )}

                        {/* Batch results */}
                        {batchResults && (
                            <div style={{ marginTop: '24px' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                                    <CheckCircle size={24} style={{ color: 'var(--accent-emerald)' }} />
                                    <div>
                                        <strong style={{ fontSize: 16 }}>Batch Processing Complete</strong>
                                        <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                                            ✅ {batchResults.success} succeeded • {batchResults.failed > 0 ? `❌ ${batchResults.failed} failed` : 'No failures'} • {batchResults.total} total
                                        </div>
                                    </div>
                                </div>
                                {batchResults.results.map((r, i) => (
                                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 14px', background: r.status === 'success' ? 'rgba(16,185,129,0.04)' : 'rgba(244,63,94,0.04)', borderRadius: 'var(--radius-sm)', border: `1px solid ${r.status === 'success' ? 'rgba(16,185,129,0.12)' : 'rgba(244,63,94,0.12)'}`, marginBottom: 6 }}>
                                        {r.status === 'success' ? <CheckCircle size={16} style={{ color: 'var(--accent-emerald)' }} /> : <AlertCircle size={16} style={{ color: 'var(--accent-rose)' }} />}
                                        <span style={{ flex: 1, fontSize: 14, fontWeight: 500 }}>{r.filename}</span>
                                        {r.classification && <span className={`tag tag-${r.classification}`}>{r.classification}</span>}
                                        {r.chunks && <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{r.chunks} chunks</span>}
                                        {r.detail && <span style={{ fontSize: 12, color: 'var(--accent-rose)' }}>{r.detail}</span>}
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Error */}
                        {error && (
                            <div style={{ marginTop: '24px', padding: '20px', background: 'rgba(244, 63, 94, 0.06)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(244, 63, 94, 0.15)', display: 'flex', alignItems: 'center', gap: '10px' }}>
                                <AlertCircle size={22} style={{ color: 'var(--accent-rose)' }} />
                                <strong style={{ color: 'var(--accent-rose)' }}>{error}</strong>
                            </div>
                        )}
                    </div>
                </main>
            </div>
        </>
    );
}
