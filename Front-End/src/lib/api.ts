const BASE_URL = 'http://localhost:8000/api/v1';

// Track whether a token refresh is currently in progress to prevent retry loops
let isRefreshing = false;

/**
 * Helper to read a cookie value by name.
 * Required to extract the (non-HttpOnly) csrf_token for request headers.
 */
function getCookie(name: string): string | null {
    if (typeof document === 'undefined') return null;
    const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return match ? decodeURIComponent(match[2]) : null;
}

/**
 * Core fetch wrapper. Uses credentials: 'include' so the browser
 * automatically sends HttpOnly cookies (access_token, refresh_token).
 * Injects X-CSRF-Token header on all requests.
 * On 401, attempts a silent token refresh then retries once.
 */
export async function fetchWithAuth(
    endpoint: string,
    options: RequestInit = {},
    _isRetry = false
): Promise<any> {
    const headers = new Headers(options.headers || {});

    if (!headers.has('Content-Type')) {
        headers.set('Content-Type', 'application/json');
    }

    // Attach CSRF token from the readable (non-HttpOnly) cookie
    const csrfToken = getCookie('csrf_token');
    if (csrfToken) {
        headers.set('X-CSRF-Token', csrfToken);
    }

    const response = await fetch(`${BASE_URL}${endpoint}`, {
        ...options,
        headers,
        credentials: 'include', // Sends HttpOnly cookies automatically
    });

    // If 401 and not already a retry, attempt to refresh
    if (response.status === 401 && !_isRetry) {
        if (isRefreshing) {
            // Another refresh is already in progress, just fail
            throw new Error('Session expired. Please log in again.');
        }
        isRefreshing = true;
        try {
            const refreshRes = await fetch(`${BASE_URL}/auth/refresh`, {
                method: 'POST',
                credentials: 'include',
            });
            if (!refreshRes.ok) {
                // Refresh failed: force the app to log out
                throw new Error('Session expired. Please log in again.');
            }
            // Retry the original request once with the fresh cookies
            return fetchWithAuth(endpoint, options, true);
        } finally {
            isRefreshing = false;
        }
    }

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'API request failed');
    }

    return response.json();
}

export async function uploadFileWithAuth(endpoint: string, formData: FormData) {
    const headers = new Headers();
    
    // Attach CSRF token for file uploads too
    const csrfToken = getCookie('csrf_token');
    if (csrfToken) {
        headers.set('X-CSRF-Token', csrfToken);
    }
    // Do NOT set Content-Type - browser sets boundary for multipart/form-data

    const response = await fetch(`${BASE_URL}${endpoint}`, {
        method: 'POST',
        headers,
        body: formData,
        credentials: 'include',
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'API request failed');
    }

    return response.json();
}
