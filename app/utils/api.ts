/**
 * API Utility with Retry Logic
 * Provides resilient API calls with exponential backoff
 */

interface RetryOptions {
    maxRetries?: number;
    initialDelay?: number;
    maxDelay?: number;
    backoffMultiplier?: number;
    shouldRetry?: (error: any) => boolean;
}

interface FetchOptions extends RequestInit {
    timeout?: number;
}

const DEFAULT_RETRY_OPTIONS: Required<RetryOptions> = {
    maxRetries: 3,
    initialDelay: 1000,
    maxDelay: 10000,
    backoffMultiplier: 2,
    shouldRetry: (error: any) => {
        // Retry on network errors or 5xx server errors
        if (error.name === 'TypeError') return true; // Network error
        if (error.status >= 500 && error.status < 600) return true; // Server error
        if (error.status === 429) return true; // Rate limit
        return false;
    },
};

/**
 * Sleep utility for delays
 */
const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Fetch with timeout
 */
async function fetchWithTimeout(
    url: string,
    options: FetchOptions = {}
): Promise<Response> {
    const { timeout = 30000, ...fetchOptions } = options;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
        const response = await fetch(url, {
            ...fetchOptions,
            signal: controller.signal,
        });
        clearTimeout(timeoutId);
        return response;
    } catch (error) {
        clearTimeout(timeoutId);
        throw error;
    }
}

/**
 * Fetch with automatic retry and exponential backoff
 */
export async function fetchWithRetry<T = any>(
    url: string,
    options: FetchOptions = {},
    retryOptions: RetryOptions = {}
): Promise<T> {
    const opts = { ...DEFAULT_RETRY_OPTIONS, ...retryOptions };
    let lastError: any;

    for (let attempt = 0; attempt <= opts.maxRetries; attempt++) {
        try {
            const response = await fetchWithTimeout(url, options);

            // Check if response is ok
            if (!response.ok) {
                const error: any = new Error(`HTTP ${response.status}: ${response.statusText}`);
                error.status = response.status;
                error.response = response;
                throw error;
            }

            // Parse JSON response
            const data = await response.json();
            return data;

        } catch (error: any) {
            lastError = error;

            // Don't retry if it's the last attempt
            if (attempt === opts.maxRetries) {
                break;
            }

            // Check if we should retry this error
            if (!opts.shouldRetry(error)) {
                throw error;
            }

            // Calculate delay with exponential backoff
            const delay = Math.min(
                opts.initialDelay * Math.pow(opts.backoffMultiplier, attempt),
                opts.maxDelay
            );

            console.warn(
                `Request failed (attempt ${attempt + 1}/${opts.maxRetries + 1}). ` +
                `Retrying in ${delay}ms...`,
                error.message
            );

            await sleep(delay);
        }
    }

    // All retries exhausted
    console.error(`Request failed after ${opts.maxRetries + 1} attempts`, lastError);
    throw lastError;
}

/**
 * Specialized API client for the Crypto AI backend
 */
export class ApiClient {
    private baseUrl: string;
    private defaultRetryOptions: RetryOptions;

    constructor(
        baseUrl: string = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
        retryOptions: RetryOptions = {}
    ) {
        this.baseUrl = baseUrl;
        this.defaultRetryOptions = retryOptions;
    }

    /**
     * GET request with retry
     */
    async get<T = any>(
        endpoint: string,
        options: FetchOptions = {},
        retryOptions?: RetryOptions
    ): Promise<T> {
        const url = `${this.baseUrl}${endpoint}`;
        return fetchWithRetry<T>(
            url,
            { ...options, method: 'GET' },
            { ...this.defaultRetryOptions, ...retryOptions }
        );
    }

    /**
     * POST request with retry
     */
    async post<T = any>(
        endpoint: string,
        body?: any,
        options: FetchOptions = {},
        retryOptions?: RetryOptions
    ): Promise<T> {
        const url = `${this.baseUrl}${endpoint}`;
        return fetchWithRetry<T>(
            url,
            {
                ...options,
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers,
                },
                body: body ? JSON.stringify(body) : undefined,
            },
            { ...this.defaultRetryOptions, ...retryOptions }
        );
    }
}

// Export singleton instance
export const apiClient = new ApiClient();

/**
 * React Query helper for API calls with retry
 */
export const queryOptions = {
    retry: 3,
    retryDelay: (attemptIndex: number) => Math.min(1000 * Math.pow(2, attemptIndex), 10000),
    staleTime: 30000, // 30 seconds
    cacheTime: 300000, // 5 minutes
};
