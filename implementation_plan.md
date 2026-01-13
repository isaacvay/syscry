# Binance API URL Configuration Implementation Plan

## Goal Description
The user is experiencing a "451 Client Error" from the Binance API when deploying to Railway. This is a geo-blocking error because `api.binance.com` is restricted in certain regions (like the US, where many cloud servers are located).
The goal is to make the Binance API base URL configurable so the user can switch to `https://api.binance.us` or a proxy URL via environment variables without changing the code.

## User Review Required
> [!IMPORTANT]
> If your Railway service is in the US, you **MUST** set `BINANCE_BASE_URL=https://api.binance.us` in your Railway variables after this change. Note that Binance.US has different data availability than Binance.com.

## Proposed Changes

### Backend Configuration

#### [MODIFY] [backend/config.py](file:///d:/deep/syscry/backend/config.py)
- Add `binance_base_url` field to the `Settings` class.
- Default it to `"https://api.binance.com"` to preserve existing behavior.
- Allow it to be overridden by the `BINANCE_BASE_URL` environment variable.

#### [MODIFY] [backend/indicators/signals.py](file:///d:/deep/syscry/backend/indicators/signals.py)
- Import `settings` from `config`.
- Replace the hardcoded `https://api.binance.com` string with `settings.binance_base_url`.

#### [MODIFY] [backend/.env.example](file:///d:/deep/syscry/backend/.env.example)
- Add `BINANCE_BASE_URL=https://api.binance.com` as a documented example variable.

### Documentation

#### [MODIFY] [RAILWAY_DEPLOY.md](file:///d:/deep/syscry/RAILWAY_DEPLOY.md)
- Update the deployment guide to explicitly mention the `BINANCE_BASE_URL` variable and the 451 error solution.

## Verification Plan

### Automated Tests
- Run `pytest` to ensure no regressions in existing tests.
- I will create a small script `verify_binance_url.py` that imports `settings` and prints the configured URL to verify it picks up the environment variable.

### Manual Verification
- I will simulate the change by setting `BINANCE_BASE_URL` to a dummy value locally and running the verification script.
- The user will need to redeploy and set the variable in Railway to verify the fix in production.
