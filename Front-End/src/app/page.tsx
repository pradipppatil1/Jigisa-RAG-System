'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { fetchWithAuth } from '@/lib/api';

const DEMO_ACCOUNTS = [
  { username: 'emp_user', role: 'employee' },
  { username: 'fin_user', role: 'finance' },
  { username: 'eng_user', role: 'engineering' },
  { username: 'mkt_user', role: 'marketing' },
  { username: 'ceo_user', role: 'c_level' },
];

export default function LoginPage() {
  const [username, setUsername] = useState('emp_user');
  const [password, setPassword] = useState('emp123');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const { login } = useAuth();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = await fetchWithAuth('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, password })
      });

      login(res.access_token, res.user);

      if (res.user.role === 'c_level') {
        router.push('/chat'); // even C-Level uses chat mostly, or we could redirect to admin. Let's just go to chat and they can click admin.
      } else {
        router.push('/chat');
      }
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="login-box">
        <h1 style={{ marginBottom: '0.5rem', marginTop: 0 }}>Welcome to FinBot</h1>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>Sign in to safely query company knowledge.</p>

        {error && (
          <div style={{ background: 'var(--danger-bg)', color: 'var(--danger-color)', padding: '0.75rem', borderRadius: '4px', marginBottom: '1rem' }}>
            {error}
          </div>
        )}

        <form className="login-form" onSubmit={handleLogin}>
          <div className="input-group">
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          <div className="input-group">
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button type="submit" className="btn-primary" disabled={loading} style={{ marginTop: '1rem' }}>
            {loading ? 'Authenticating...' : 'Sign In'}
          </button>
        </form>

        <div style={{ marginTop: '2.5rem' }}>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: '1px' }}>Quick Select Demo Accounts</p>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {DEMO_ACCOUNTS.map((acc) => (
              <button
                key={acc.username}
                type="button"
                onClick={() => { setUsername(acc.username); setPassword('password123'); }}
                style={{
                  background: 'var(--bg-color)',
                  color: 'var(--text-secondary)',
                  border: '1px solid var(--border-color)',
                  padding: '0.5rem 1rem',
                  borderRadius: '16px',
                  fontSize: '0.8rem',
                  transition: 'background 0.2s'
                }}
                onMouseOver={e => e.currentTarget.style.background = 'var(--border-color)'}
                onMouseOut={e => e.currentTarget.style.background = 'var(--bg-color)'}
              >
                {acc.role.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
