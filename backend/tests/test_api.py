import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "System Operational"
        assert "version" in data

@pytest.mark.asyncio
async def test_health_endpoint():
    """Test health check"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

@pytest.mark.asyncio
async def test_cryptos_list():
    """Test cryptos list endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/cryptos/list")
        assert response.status_code == 200
        data = response.json()
        assert "cryptos" in data
        assert "timeframes" in data
        assert len(data["cryptos"]) > 0
        assert len(data["timeframes"]) > 0

@pytest.mark.asyncio
async def test_get_signal_valid():
    """Test signal generation with valid data"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/get-signal",
            json={"symbol": "BTCUSDT", "timeframe": "1h"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "signal" in data
        assert "confidence" in data

@pytest.mark.asyncio
async def test_get_signal_invalid_symbol():
    """Test signal with invalid symbol"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/get-signal",
            json={"symbol": "INVALID", "timeframe": "1h"}
        )
        assert response.status_code == 422  # Validation error

@pytest.mark.asyncio
async def test_get_signal_invalid_timeframe():
    """Test signal with invalid timeframe"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/get-signal",
            json={"symbol": "BTCUSDT", "timeframe": "99h"}
        )
        assert response.status_code == 422  # Validation error

@pytest.mark.asyncio
async def test_signals_history():
    """Test signal history endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/signals/history?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "signals" in data
        assert "count" in data
