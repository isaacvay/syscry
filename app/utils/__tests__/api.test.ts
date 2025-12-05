import { render, screen, waitFor } from '@testing-library/react';
import { fetchWithRetry, ApiClient } from '../api';

// Mock fetch
global.fetch = jest.fn();

describe('fetchWithRetry', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        jest.useFakeTimers();
    });

    afterEach(() => {
        jest.useRealTimers();
    });

    it('returns data on successful request', async () => {
        const mockData = { success: true };
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => mockData,
        });

        const promise = fetchWithRetry('/test');
        const result = await promise;

        expect(result).toEqual(mockData);
        expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    it('retries on network error', async () => {
        const mockData = { success: true };

        // First call fails, second succeeds
        (global.fetch as jest.Mock)
            .mockRejectedValueOnce(new TypeError('Network error'))
            .mockResolvedValueOnce({
                ok: true,
                json: async () => mockData,
            });

        const promise = fetchWithRetry('/test', {}, { maxRetries: 1, initialDelay: 100 });

        // Fast-forward timers
        setTimeout(() => jest.advanceTimersByTime(100), 0);

        const result = await promise;

        expect(result).toEqual(mockData);
        expect(global.fetch).toHaveBeenCalledTimes(2);
    });

    it('retries on 500 error', async () => {
        const mockData = { success: true };

        (global.fetch as jest.Mock)
            .mockResolvedValueOnce({
                ok: false,
                status: 500,
                statusText: 'Internal Server Error',
            })
            .mockResolvedValueOnce({
                ok: true,
                json: async () => mockData,
            });

        const promise = fetchWithRetry('/test', {}, { maxRetries: 1, initialDelay: 100 });

        setTimeout(() => jest.advanceTimersByTime(100), 0);

        const result = await promise;

        expect(result).toEqual(mockData);
        expect(global.fetch).toHaveBeenCalledTimes(2);
    });

    it('throws error after max retries', async () => {
        (global.fetch as jest.Mock).mockRejectedValue(new TypeError('Network error'));

        const promise = fetchWithRetry('/test', {}, { maxRetries: 2, initialDelay: 100 });

        // Advance timers for all retries
        setTimeout(() => {
            jest.advanceTimersByTime(100); // First retry
            setTimeout(() => jest.advanceTimersByTime(200), 0); // Second retry
        }, 0);

        await expect(promise).rejects.toThrow('Network error');
        expect(global.fetch).toHaveBeenCalledTimes(3); // Initial + 2 retries
    });

    it('does not retry on 404 error', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: false,
            status: 404,
            statusText: 'Not Found',
        });

        await expect(
            fetchWithRetry('/test', {}, { maxRetries: 2 })
        ).rejects.toThrow('HTTP 404');

        expect(global.fetch).toHaveBeenCalledTimes(1); // No retries
    });
});

describe('ApiClient', () => {
    let client: ApiClient;

    beforeEach(() => {
        jest.clearAllMocks();
        client = new ApiClient('http://test-api.com');
    });

    it('makes GET request', async () => {
        const mockData = { data: 'test' };
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => mockData,
        });

        const result = await client.get('/endpoint');

        expect(result).toEqual(mockData);
        expect(global.fetch).toHaveBeenCalledWith(
            'http://test-api.com/endpoint',
            expect.objectContaining({ method: 'GET' })
        );
    });

    it('makes POST request with body', async () => {
        const mockData = { success: true };
        const postBody = { symbol: 'BTCUSDT' };

        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => mockData,
        });

        const result = await client.post('/endpoint', postBody);

        expect(result).toEqual(mockData);
        expect(global.fetch).toHaveBeenCalledWith(
            'http://test-api.com/endpoint',
            expect.objectContaining({
                method: 'POST',
                body: JSON.stringify(postBody),
                headers: expect.objectContaining({
                    'Content-Type': 'application/json',
                }),
            })
        );
    });
});
