import type { Config } from 'jest';
import nextJest from 'next/jest';

const createJestConfig = nextJest({
    // Provide the path to your Next.js app to load next.config.js and .env files in your test environment
    dir: './',
});

// Add any custom config to be passed to Jest
const config: Config = {
    coverageProvider: 'v8',
    testEnvironment: 'jsdom',

    // Setup files
    setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],

    // Module paths
    moduleNameMapper: {
        '^@/(.*)$': '<rootDir>/app/$1',
    },

    // Test match patterns
    testMatch: [
        '**/__tests__/**/*.[jt]s?(x)',
        '**/?(*.)+(spec|test).[jt]s?(x)',
    ],

    // Coverage configuration
    collectCoverageFrom: [
        'app/**/*.{js,jsx,ts,tsx}',
        '!app/**/*.d.ts',
        '!app/**/*.stories.{js,jsx,ts,tsx}',
        '!app/**/_*.{js,jsx,ts,tsx}',
        '!app/**/layout.tsx',
        '!app/**/page.tsx',
    ],

    coverageThreshold: {
        global: {
            branches: 50,
            functions: 50,
            lines: 50,
            statements: 50,
        },
    },

    // Transform files
    transform: {
        '^.+\\.(ts|tsx)$': ['@swc/jest', {
            jsc: {
                transform: {
                    react: {
                        runtime: 'automatic',
                    },
                },
            },
        }],
    },

    // Ignore patterns
    testPathIgnorePatterns: ['/node_modules/', '/.next/'],
    transformIgnorePatterns: [
        '/node_modules/',
        '^.+\\.module\\.(css|sass|scss)$',
    ],
};

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
export default createJestConfig(config);
