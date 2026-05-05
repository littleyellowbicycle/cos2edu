import os
import sys
import pytest
import pytest_asyncio
from io import BytesIO
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

os.environ["APP_ENV"] = "test"

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.core.database import BackgroundConfig
from tests.helpers import create_test_app


@pytest.mark.asyncio
class TestUploadAPI:
    
    async def test_upload_avatar_success(self, test_session: AsyncSession, test_upload_dirs):
        app = create_test_app(test_session)
        
        # 创建测试图片
        img_buffer = BytesIO()
        try:
            from PIL import Image
            img = Image.new('RGB', (100, 100), color='red')
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
        except ImportError:
            img_buffer = BytesIO(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
            img_buffer.seek(0)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/upload/avatar",
                files={"file": ("test.png", img_buffer, "image/png")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
    
    async def test_upload_avatar_invalid_type(self, test_session: AsyncSession, test_upload_dirs):
        app = create_test_app(test_session)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/upload/avatar",
                files={"file": ("test.txt", BytesIO(b"not an image"), "text/plain")}
            )
        
        assert response.status_code == 400
    
    async def test_upload_background_success(self, test_session: AsyncSession, test_upload_dirs):
        app = create_test_app(test_session)
        
        img_buffer = BytesIO()
        try:
            from PIL import Image
            img = Image.new('RGB', (100, 100), color='blue')
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
        except ImportError:
            img_buffer = BytesIO(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
            img_buffer.seek(0)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/upload/background",
                files={"file": ("bg.png", img_buffer, "image/png")}
            )
        
        assert response.status_code == 200
    
    async def test_upload_background_invalid_type(self, test_session: AsyncSession, test_upload_dirs):
        app = create_test_app(test_session)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/upload/background",
                files={"file": ("test.txt", BytesIO(b"not an image"), "text/plain")}
            )
        
        assert response.status_code == 400


@pytest.mark.asyncio
class TestBackgroundConfigsAPI:
    
    async def test_get_backgrounds(self, test_session: AsyncSession, test_background_config: BackgroundConfig):
        app = create_test_app(test_session)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/backgrounds")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
    
    async def test_get_default_background(self, test_session: AsyncSession):
        app = create_test_app(test_session)
        
        # 创建默认背景
        bg = BackgroundConfig(
            name="默认背景",
            background_type="color",
            background_value="#ffffff",
            is_default=True,
            is_active=True
        )
        test_session.add(bg)
        await test_session.commit()
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/backgrounds/default")
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_default"] is True
    
    async def test_get_background_by_id(self, test_session: AsyncSession, test_background_config: BackgroundConfig):
        app = create_test_app(test_session)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/api/backgrounds/{test_background_config.id}")
        
        assert response.status_code == 200
    
    async def test_get_background_not_found(self, test_session: AsyncSession):
        app = create_test_app(test_session)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/backgrounds/999")
        
        assert response.status_code == 404
    
    async def test_create_background(self, test_session: AsyncSession):
        app = create_test_app(test_session)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/backgrounds", json={
                "name": "新背景",
                "background_type": "color",
                "background_value": "#000000"
            })
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "新背景"
    
    async def test_update_background(self, test_session: AsyncSession, test_background_config: BackgroundConfig):
        app = create_test_app(test_session)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put(f"/api/backgrounds/{test_background_config.id}", json={
                "name": "更新后的背景"
            })
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "更新后的背景"
    
    async def test_delete_background(self, test_session: AsyncSession, test_background_config: BackgroundConfig):
        app = create_test_app(test_session)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete(f"/api/backgrounds/{test_background_config.id}")
        
        assert response.status_code == 200
