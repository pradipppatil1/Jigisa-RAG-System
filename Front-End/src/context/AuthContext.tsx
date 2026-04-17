'use client';
import React, { createContext, useContext, useState, useEffect } from 'react';
import { fetchWithAuth } from '@/lib/api';

export type UserProfile = {
  user_id: number;
  username: string;
  role: string;
  collections: string[];
  department?: string;
};

type AuthContextType = {
  user: UserProfile | null;
  isLoading: boolean;
  login: (user: UserProfile) => void;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // On mount, silently try to restore the session via the /auth/me endpoint.
  // The HttpOnly access_token cookie is automatically sent by the browser.
  // If it's expired, fetchWithAuth will transparently call /refresh and retry.
  useEffect(() => {
    fetchWithAuth('/auth/me', { method: 'GET' })
      .then((data: UserProfile) => setUser(data))
      .catch(() => setUser(null))
      .finally(() => setIsLoading(false));
  }, []);

  const login = (newUser: UserProfile) => {
    // Tokens are stored in HttpOnly cookies by the backend /login response.
    // We only need to store the user profile in React state.
    setUser(newUser);
  };

  const logout = async () => {
    try {
      // Ask the backend to revoke the refresh token and clear cookies
      await fetch('http://localhost:8000/api/v1/auth/logout', {
        method: 'POST',
        credentials: 'include',
      });
    } catch {
      // Best-effort logout
    } finally {
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
