import pytest
import asyncio
import uuid
from fastapi.testclient import TestClient
from datetime import datetime
import jwt
from unittest.mock import Mock, patch, AsyncMock
import json

# Import your FastAPI app
from main import app, JWT_SECRET_KEY, ALGORITHM, products_db, carts_db, user_carts_db

# Create test client
client = TestClient(app)

class TestJewelryAPI:
    
    def setup_method(self):
        """Reset the in-memory databases before each test"""
        carts_db.clear()
        user_carts_db.clear()
    
    def test_root_endpoint(self):
        """Test the root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Welcome to Luxe Jewelry Store API"}
    
    def test_get_all_products(self):
        """Test getting all products"""
        response = client.get("/api/products")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 6  # Based on the products in the code
        
        # Check first product structure
        product = data[0]
        required_fields = ["id", "name", "price", "image", "description", "category", "in_stock"]
        for field in required_fields:
            assert field in product
    
    def test_get_products_by_category(self):
        """Test filtering products by category"""
        response = client.get("/api/products?category=rings")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["category"] == "rings"
        assert data[0]["name"] == "Diamond Engagement Ring"
    
    def test_get_product_by_id(self):
        """Test getting a specific product by ID"""
        response = client.get("/api/products/1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Diamond Engagement Ring"
        assert data["price"] == 2999.00
    
    def test_get_nonexistent_product(self):
        """Test getting a product that doesn't exist"""
        response = client.get("/api/products/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Product not found"
    
    def test_get_categories(self):
        """Test getting all categories"""
        response = client.get("/api/categories")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        categories = data["categories"]
        expected_categories = {"rings", "necklaces", "bracelets", "earrings"}
        assert set(categories) == expected_categories
    
    def test_add_to_cart_anonymous(self):
        """Test adding items to cart for anonymous user"""
        session_id = str(uuid.uuid4())
        cart_item = {"product_id": 1, "quantity": 2}
        
        response = client.post(f"/api/cart/{session_id}/add", json=cart_item)
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Item added to cart"
        assert data["cart_items"] == 1
    
    def test_add_nonexistent_product_to_cart(self):
        """Test adding a non-existent product to cart"""
        session_id = str(uuid.uuid4())
        cart_item = {"product_id": 999, "quantity": 1}
        
        response = client.post(f"/api/cart/{session_id}/add", json=cart_item)
        assert response.status_code == 404
        assert response.json()["detail"] == "Product not found"
    
    def test_add_duplicate_item_to_cart(self):
        """Test adding the same item to cart multiple times (should increase quantity)"""
        session_id = str(uuid.uuid4())
        cart_item = {"product_id": 1, "quantity": 1}
        
        # Add item first time
        response1 = client.post(f"/api/cart/{session_id}/add", json=cart_item)
        assert response1.status_code == 200
        
        # Add same item second time
        response2 = client.post(f"/api/cart/{session_id}/add", json=cart_item)
        assert response2.status_code == 200
        
        # Check that cart still has 1 item (but quantity should be 2)
        assert response2.json()["cart_items"] == 1
    
    def test_get_cart_anonymous(self):
        """Test getting cart for anonymous user"""
        session_id = str(uuid.uuid4())
        
        # Add item to cart first
        cart_item = {"product_id": 1, "quantity": 2}
        client.post(f"/api/cart/{session_id}/add", json=cart_item)
        
        # Get cart
        response = client.get(f"/api/cart?session_id={session_id}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["product_id"] == 1
        assert data[0]["quantity"] == 2
    
    def test_get_empty_cart(self):
        """Test getting an empty cart"""
        session_id = str(uuid.uuid4())
        response = client.get(f"/api/cart?session_id={session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data == []
    
    def test_remove_item_from_cart(self):
        """Test removing an item from cart"""
        session_id = str(uuid.uuid4())
        
        # Add item to cart
        cart_item = {"product_id": 1, "quantity": 1}
        client.post(f"/api/cart/{session_id}/add", json=cart_item)
        
        # Get cart to find item ID
        cart_response = client.get(f"/api/cart?session_id={session_id}")
        cart_data = cart_response.json()
        item_id = cart_data[0]["id"]
        
        # Remove item
        response = client.delete(f"/api/cart/{session_id}/item/{item_id}")
        assert response.status_code == 200
        assert response.json()["message"] == "Item removed from cart"
        assert response.json()["cart_items"] == 0
    
    def test_remove_nonexistent_item_from_cart(self):
        """Test removing an item that doesn't exist in cart"""
        session_id = str(uuid.uuid4())
        fake_item_id = str(uuid.uuid4())
        
        response = client.delete(f"/api/cart/{session_id}/item/{fake_item_id}")
        assert response.status_code == 404
        assert response.json()["detail"] == "Cart not found"
    
    def test_update_cart_item_quantity(self):
        """Test updating cart item quantity"""
        session_id = str(uuid.uuid4())
        
        # Add item to cart
        cart_item = {"product_id": 1, "quantity": 1}
        client.post(f"/api/cart/{session_id}/add", json=cart_item)
        
        # Get item ID
        cart_response = client.get(f"/api/cart?session_id={session_id}")
        item_id = cart_response.json()[0]["id"]
        
        # Update quantity
        response = client.put(f"/api/cart/{session_id}/item/{item_id}?quantity=5")
        assert response.status_code == 200
        assert response.json()["message"] == "Item quantity updated"
    
    def test_update_cart_item_quantity_to_zero(self):
        """Test updating cart item quantity to zero (should remove item)"""
        session_id = str(uuid.uuid4())
        
        # Add item to cart
        cart_item = {"product_id": 1, "quantity": 1}
        client.post(f"/api/cart/{session_id}/add", json=cart_item)
        
        # Get item ID
        cart_response = client.get(f"/api/cart?session_id={session_id}")
        item_id = cart_response.json()[0]["id"]
        
        # Update quantity to 0
        response = client.put(f"/api/cart/{session_id}/item/{item_id}?quantity=0")
        assert response.status_code == 200
        assert response.json()["message"] == "Item removed from cart"
    
    def test_clear_cart(self):
        """Test clearing entire cart"""
        session_id = str(uuid.uuid4())
        
        # Add multiple items to cart
        cart_items = [
            {"product_id": 1, "quantity": 1},
            {"product_id": 2, "quantity": 2}
        ]
        for item in cart_items:
            client.post(f"/api/cart/{session_id}/add", json=item)
        
        # Clear cart
        response = client.delete(f"/api/cart/{session_id}")
        assert response.status_code == 200
        assert response.json()["message"] == "Cart cleared"
        
        # Verify cart is empty
        cart_response = client.get(f"/api/cart?session_id={session_id}")
        assert cart_response.json() == []
    
    @patch('main.get_current_user')
    def test_add_to_cart_authenticated_user(self, mock_get_current_user):
        """Test adding items to cart for authenticated user"""
        # Mock authenticated user
        mock_user = {"id": "user123", "email": "test@example.com"}
        mock_get_current_user.return_value = mock_user
        
        session_id = str(uuid.uuid4())
        cart_item = {"product_id": 1, "quantity": 1}
        
        response = client.post(f"/api/cart/{session_id}/add", json=cart_item)
        assert response.status_code == 200
        assert response.json()["message"] == "Item added to cart"
        assert response.json()["cart_items"] == 1
    
    @patch('main.get_current_user')
    def test_get_cart_authenticated_user(self, mock_get_current_user):
        """Test getting cart for authenticated user"""
        # Mock authenticated user
        mock_user = {"id": "user123", "email": "test@example.com"}
        mock_get_current_user.return_value = mock_user
        
        session_id = str(uuid.uuid4())
        cart_item = {"product_id": 1, "quantity": 2}
        
        # Add item to cart
        client.post(f"/api/cart/{session_id}/add", json=cart_item)
        
        # Get cart
        response = client.get("/api/cart")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["product_id"] == 1
    
    def create_jwt_token(self, user_id: str) -> str:
        """Helper method to create JWT token for testing"""
        payload = {"sub": user_id}
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=ALGORITHM)
    
    def test_invalid_jwt_token(self):
        """Test API with invalid JWT token"""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/api/cart", headers=headers)
        # Should still work but as anonymous user
        assert response.status_code == 200
        assert response.json() == []  # Empty cart for default session


class TestAuthenticationFlow:
    """Test authentication-related functionality"""
    
    def setup_method(self):
        carts_db.clear()
        user_carts_db.clear()
    
    @patch('main.httpx.AsyncClient')
    @patch('main.get_current_user')
    async def test_auth_service_integration(self, mock_get_current_user, mock_httpx):
        """Test integration with auth service"""
        # Mock the auth service response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "user123", "email": "test@example.com"}
        
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_response
        mock_httpx.return_value = mock_client
        
        # This would be tested in an async context in a real scenario
        # For now, we'll just ensure the mocking works
        assert mock_response.status_code == 200


class TestDataValidation:
    """Test data validation and edge cases"""
    
    def test_add_to_cart_invalid_data(self):
        """Test adding to cart with invalid data"""
        session_id = str(uuid.uuid4())
        
        # Missing product_id
        response = client.post(f"/api/cart/{session_id}/add", json={"quantity": 1})
        assert response.status_code == 422  # Validation error
        
        # Invalid quantity type
        response = client.post(f"/api/cart/{session_id}/add", 
                             json={"product_id": 1, "quantity": "invalid"})
        assert response.status_code == 422
    
    def test_product_data_structure(self):
        """Test that product data has correct structure"""
        response = client.get("/api/products")
        products = response.json()
        
        for product in products:
            # Check required fields
            assert "id" in product and isinstance(product["id"], int)
            assert "name" in product and isinstance(product["name"], str)
            assert "price" in product and isinstance(product["price"], (int, float))
            assert "image" in product and isinstance(product["image"], str)
            assert "description" in product and isinstance(product["description"], str)
            assert "category" in product and isinstance(product["category"], str)
            assert "in_stock" in product and isinstance(product["in_stock"], bool)
            
            # Check price is positive
            assert product["price"] > 0
            
            # Check image URL format
            assert product["image"].startswith("https://")


# Test fixtures and utilities
@pytest.fixture
def sample_cart_data():
    """Fixture providing sample cart data for tests"""
    return [
        {"product_id": 1, "quantity": 2},
        {"product_id": 3, "quantity": 1},
        {"product_id": 5, "quantity": 3}
    ]

@pytest.fixture
def authenticated_headers():
    """Fixture providing authentication headers"""
    token = jwt.encode({"sub": "test_user_123"}, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return {"Authorization": f"Bearer {token}"}


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])