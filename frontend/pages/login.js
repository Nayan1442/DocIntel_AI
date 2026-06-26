import Head from 'next/head';
import Link from 'next/link';
import { useState } from 'react';
import { useAuth } from '../components/AuthContext';
import { Lock, Mail, User, Shield, ArrowRight, Sparkles, AlertCircle } from 'lucide-react';

export default function LoginPage() {
    const [isSignUp, setIsSignUp] = useState(false);
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const { login, register, loading } = useAuth();

    async function handleSubmit(e) {
        e.preventDefault();
        setError('');

        if (!email.trim() || !password) {
            setError('Please fill in all fields');
            return;
        }

        if (isSignUp && !name.trim()) {
            setError('Please enter your name');
            return;
        }

        if (password.length < 6) {
            setError('Password must be at least 6 characters long');
            return;
        }

        let res;
        if (isSignUp) {
            res = await register(name, email, password);
        } else {
            res = await login(email, password);
        }

        if (res && !res.success) {
            setError(res.error);
        }
    }

    return (
        <>
            <Head>
                <title>{isSignUp ? 'Sign Up' : 'Sign In'} — DocIntel AI</title>
                <meta name="description" content="Access your AI Document Intelligence Platform dashboard." />
            </Head>

            <div className="auth-page-container">
                <div className="auth-glow auth-glow-1" />
                <div className="auth-glow auth-glow-2" />

                <div className="auth-card-wrapper">
                    {/* Brand Logo */}
                    <Link href="/" className="auth-brand">
                        <div className="auth-brand-icon">🧠</div>
                        <span>DocIntel AI</span>
                    </Link>

                    {/* Main Auth Card */}
                    <div className="card auth-card">
                        <div className="auth-card-header">
                            <h2>{isSignUp ? 'Create Account' : 'Welcome Back'}</h2>
                            <p>{isSignUp ? 'Start supercharging your documents' : 'Access your document intelligence dashboard'}</p>
                        </div>

                        {error && (
                            <div className="auth-error-box">
                                <AlertCircle size={16} />
                                <span>{error}</span>
                            </div>
                        )}

                        <form onSubmit={handleSubmit} className="auth-form">
                            {isSignUp && (
                                <div className="form-group">
                                    <label htmlFor="name-input">Full Name</label>
                                    <div className="input-with-icon">
                                        <User size={16} className="input-icon" />
                                        <input
                                            id="name-input"
                                            className="input"
                                            type="text"
                                            placeholder="John Doe"
                                            value={name}
                                            onChange={e => setName(e.target.value)}
                                            disabled={loading}
                                            autoComplete="name"
                                        />
                                    </div>
                                </div>
                            )}

                            <div className="form-group">
                                <label htmlFor="email-input">Email Address</label>
                                <div className="input-with-icon">
                                    <Mail size={16} className="input-icon" />
                                    <input
                                        id="email-input"
                                        className="input"
                                        type="email"
                                        placeholder="you@example.com"
                                        value={email}
                                        onChange={e => setEmail(e.target.value)}
                                        disabled={loading}
                                        autoComplete="email"
                                    />
                                </div>
                            </div>

                            <div className="form-group">
                                <label htmlFor="password-input">Password</label>
                                <div className="input-with-icon">
                                    <Lock size={16} className="input-icon" />
                                    <input
                                        id="password-input"
                                        className="input"
                                        type="password"
                                        placeholder="••••••••"
                                        value={password}
                                        onChange={e => setPassword(e.target.value)}
                                        disabled={loading}
                                        autoComplete={isSignUp ? 'new-password' : 'current-password'}
                                    />
                                </div>
                            </div>

                            <button className="btn btn-primary auth-submit-btn" type="submit" disabled={loading}>
                                {loading ? (
                                    <div className="spinner-sm" />
                                ) : (
                                    <>
                                        {isSignUp ? 'Sign Up' : 'Sign In'} <ArrowRight size={16} />
                                    </>
                                )}
                            </button>
                        </form>

                        <div className="auth-footer">
                            <button
                                className="auth-toggle-btn"
                                onClick={() => {
                                    setIsSignUp(!isSignUp);
                                    setError('');
                                }}
                                disabled={loading}
                            >
                                {isSignUp ? 'Already have an account? Sign In' : "Don't have an account? Sign Up"}
                            </button>
                        </div>
                    </div>

                    {/* Features highlight footer */}
                    <div className="auth-features-footer">
                        <div className="auth-feature-item">
                            <Shield size={14} />
                            <span>JWT Protected Isolation</span>
                        </div>
                        <div className="auth-feature-item-dot">•</div>
                        <div className="auth-feature-item">
                            <Sparkles size={14} />
                            <span>Vibrant AI Agents</span>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
}
