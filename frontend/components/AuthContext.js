import { createContext, useContext, useState, useEffect } from 'react';
import { useRouter } from 'next/router';

const AuthContext = createContext(null);

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(null);
    const [loading, setLoading] = useState(true);
    const router = useRouter();

    useEffect(() => {
        // Load token and user from localStorage on mount
        const storedToken = localStorage.getItem('token');
        if (storedToken) {
            setToken(storedToken);
            fetchProfile(storedToken);
        } else {
            setLoading(false);
        }
    }, []);

    async function fetchProfile(jwtToken) {
        try {
            const res = await fetch(`${API}/auth/me`, {
                headers: {
                    Authorization: `Bearer ${jwtToken}`,
                },
            });
            if (res.ok) {
                const userData = await res.json();
                setUser(userData);
            } else {
                // Token invalid or expired
                logout();
            }
        } catch (e) {
            console.error('Failed to fetch user profile:', e);
        } finally {
            setLoading(false);
        }
    }

    async function login(email, password) {
        setLoading(true);
        try {
            const res = await fetch(`${API}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }),
            });
            const data = await res.json();
            if (res.ok) {
                localStorage.setItem('token', data.token);
                setToken(data.token);
                setUser(data.user);
                router.push('/app');
                return { success: true };
            } else {
                return { success: false, error: data.detail || 'Login failed' };
            }
        } catch (e) {
            return { success: false, error: 'Network error. Please try again.' };
        } finally {
            setLoading(false);
        }
    }

    async function register(name, email, password) {
        setLoading(true);
        try {
            const res = await fetch(`${API}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, password }),
            });
            const data = await res.json();
            if (res.ok) {
                localStorage.setItem('token', data.token);
                setToken(data.token);
                setUser(data.user);
                router.push('/app');
                return { success: true };
            } else {
                return { success: false, error: data.detail || 'Registration failed' };
            }
        } catch (e) {
            return { success: false, error: 'Network error. Please try again.' };
        } finally {
            setLoading(false);
        }
    }

    function logout() {
        localStorage.removeItem('token');
        setToken(null);
        setUser(null);
        router.push('/login');
    }

    async function authFetch(url, options = {}) {
        const activeToken = token || localStorage.getItem('token');
        const headers = {
            ...options.headers,
        };
        if (activeToken) {
            headers['Authorization'] = `Bearer ${activeToken}`;
        }
        return fetch(url, { ...options, headers });
    }

    return (
        <AuthContext.Provider value={{ user, token, loading, login, register, logout, authFetch }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
