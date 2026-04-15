const BASE_URL = 'http://localhost:8000/api/v1';

export async function fetchWithAuth(endpoint: string, options: RequestInit = {}) {
    const token = typeof window !== 'undefined' ? localStorage.getItem('finbot_token') : null;
    
    const headers = new Headers(options.headers || {});
    headers.set('Content-Type', 'application/json');
    if (token) {
        headers.set('Authorization', `Bearer ${token}`);
    }

    const response = await fetch(`${BASE_URL}${endpoint}`, {
        ...options,
        headers,
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'API request failed');
    }

    return response.json();
}

export async function uploadFileWithAuth(endpoint: string, formData: FormData) {
    const token = typeof window !== 'undefined' ? localStorage.getItem('finbot_token') : null;
    
    const headers = new Headers();
    // Deliberately do NOT set Content-Type so browser sets boundary for multipart/form-data natively
    if (token) {
        headers.set('Authorization', `Bearer ${token}`);
    }

    const response = await fetch(`${BASE_URL}${endpoint}`, {
        method: 'POST',
        headers,
        body: formData,
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'API request failed');
    }

    return response.json();
}
