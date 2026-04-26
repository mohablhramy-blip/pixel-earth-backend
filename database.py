"""
🗄️ PIXEL EARTH DATABASE
Draw the World. Own the World.

Database operations for Supabase (PostgreSQL)
Handles: Users, Pixels, Drawing Sessions, Transactions, Leaderboard
"""

from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime, timedelta
import uuid
import json

# ==================== SUPABASE CLIENT ====================
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==================== USERS ====================

def create_user(user_id: str, username: str, first_name: str) -> dict:
    """
    Create a new user if they don't exist.
    New users get 100 ⭐ welcome bonus.
    
    Returns: User data dict
    """
    # Check if user already exists
    existing = supabase.table("users").select("*").eq("user_id", user_id).execute()
    
    if not existing.data:
        # New user — create with welcome bonus
        new_user = {
            "user_id": user_id,
            "username": username or "unknown",
            "first_name": first_name or "User",
            "stars_balance": 100,          # Welcome bonus
            "total_pixels_owned": 0,
            "total_spent": 0,
            "total_earned": 0,
            "created_at": datetime.now().isoformat()
        }
        supabase.table("users").insert(new_user).execute()
        return new_user
    
    return existing.data[0]


def get_user(user_id: str) -> dict:
    """
    Get user data by Telegram user ID.
    
    Returns: User data dict or None
    """
    result = supabase.table("users").select("*").eq("user_id", user_id).execute()
    return result.data[0] if result.data else None


def update_balance(user_id: str, amount: int) -> int:
    """
    Update user's star balance.
    Positive amount = add stars
    Negative amount = deduct stars
    
    Returns: New balance
    """
    user = get_user(user_id)
    if not user:
        return 0
    
    new_balance = user["stars_balance"] + amount
    
    # Prevent negative balance
    if new_balance < 0:
        return user["stars_balance"]
    
    supabase.table("users").update({
        "stars_balance": new_balance
    }).eq("user_id", user_id).execute()
    
    return new_balance


def update_pixel_stats(user_id: str, pixel_count: int, spent_amount: int):
    """
    Update user's pixel ownership stats.
    """
    user = get_user(user_id)
    if not user:
        return
    
    current_pixels = user.get("total_pixels_owned", 0)
    current_spent = user.get("total_spent", 0)
    
    supabase.table("users").update({
        "total_pixels_owned": current_pixels + pixel_count,
        "total_spent": current_spent + spent_amount
    }).eq("user_id", user_id).execute()


# ==================== PIXELS ====================

def claim_pixels(user_id: str, pixels: list) -> int:
    """
    Claim a list of pixels for a user.
    
    pixels = [
        {"x": 12345, "y": 67890, "color": "#FF0000", "zoom": 5},
        ...
    ]
    
    Returns: Number of pixels claimed
    """
    claimed_count = 0
    
    for pixel in pixels:
        x = pixel["x"]
        y = pixel["y"]
        zoom = pixel.get("zoom", 5)
        color = pixel["color"]
        
        # Check if this pixel already exists
        existing = supabase.table("pixels").select("*")\
            .eq("x", x)\
            .eq("y", y)\
            .eq("zoom_level", zoom)\
            .execute()
        
        if existing.data:
            # Update existing pixel (new owner)
            supabase.table("pixels").update({
                "color": color,
                "owner_id": user_id,
                "purchased_at": datetime.now().isoformat()
            }).eq("id", existing.data[0]["id"]).execute()
        else:
            # Insert new pixel
            supabase.table("pixels").insert({
                "x": x,
                "y": y,
                "zoom_level": zoom,
                "color": color,
                "owner_id": user_id,
                "purchased_at": datetime.now().isoformat()
            }).execute()
        
        claimed_count += 1
    
    # Update user stats
    update_pixel_stats(user_id, claimed_count, claimed_count)
    
    return claimed_count


def get_all_pixels(zoom_level: int = None) -> list:
    """
    Get all claimed pixels.
    Optionally filter by zoom level.
    
    Returns: List of pixel dicts
    """
    query = supabase.table("pixels").select("*")
    
    if zoom_level is not None:
        query = query.eq("zoom_level", zoom_level)
    
    result = query.execute()
    return result.data if result.data else []


def get_pixel(x: int, y: int, zoom_level: int = 5) -> dict:
    """
    Get a specific pixel by coordinates.
    
    Returns: Pixel dict or None
    """
    result = supabase.table("pixels").select("*")\
        .eq("x", x)\
        .eq("y", y)\
        .eq("zoom_level", zoom_level)\
        .execute()
    
    return result.data[0] if result.data else None


def get_user_pixels(user_id: str) -> list:
    """
    Get all pixels owned by a specific user.
    
    Returns: List of pixel dicts
    """
    result = supabase.table("pixels").select("*")\
        .eq("owner_id", user_id)\
        .order("purchased_at", desc=True)\
        .execute()
    
    return result.data if result.data else []


def get_pixel_count() -> int:
    """
    Get total number of claimed pixels on the entire map.
    
    Returns: Total pixel count
    """
    result = supabase.table("pixels").select("id", count="exact").execute()
    return result.count if result.count else 0


def get_pixels_by_area(x_min: int, x_max: int, y_min: int, y_max: int, zoom_level: int = 5) -> list:
    """
    Get pixels within a specific area (for map viewport loading).
    
    Returns: List of pixel dicts in the area
    """
    result = supabase.table("pixels").select("*")\
        .gte("x", x_min)\
        .lte("x", x_max)\
        .gte("y", y_min)\
        .lte("y", y_max)\
        .eq("zoom_level", zoom_level)\
        .execute()
    
    return result.data if result.data else []


# ==================== DRAWING SESSIONS ====================

def create_drawing_session(user_id: str) -> str:
    """
    Create a temporary drawing session.
    Users draw first, then decide to pay or cancel.
    
    Returns: Session ID
    """
    session_id = str(uuid.uuid4())[:12]
    
    session_data = {
        "session_id": session_id,
        "user_id": user_id,
        "pixels_data": json.dumps([]),
        "total_cost": 0,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(minutes=30)).isoformat(),
        "status": "active"
    }
    
    supabase.table("drawing_sessions").insert(session_data).execute()
    
    return session_id


def update_session_pixels(session_id: str, pixels_data: list, total_cost: int):
    """
    Update the pixels in a drawing session.
    Called each time the user draws or undoes a pixel.
    """
    supabase.table("drawing_sessions").update({
        "pixels_data": json.dumps(pixels_data),
        "total_cost": total_cost,
        "expires_at": (datetime.now() + timedelta(minutes=30)).isoformat()
    }).eq("session_id", session_id).execute()


def get_session(session_id: str) -> dict:
    """
    Get drawing session data.
    
    Returns: Session dict or None
    """
    result = supabase.table("drawing_sessions").select("*")\
        .eq("session_id", session_id)\
        .execute()
    
    return result.data[0] if result.data else None


def end_session(session_id: str, status: str = "completed"):
    """
    End a drawing session.
    Status: "completed" (paid) or "cancelled" (freed)
    """
    supabase.table("drawing_sessions").update({
        "status": status,
        "expires_at": datetime.now().isoformat()
    }).eq("session_id", session_id).execute()


def cleanup_expired_sessions():
    """
    Delete expired drawing sessions older than 1 hour.
    Run this periodically to keep the database clean.
    """
    one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
    
    supabase.table("drawing_sessions").delete()\
        .eq("status", "active")\
        .lt("expires_at", one_hour_ago)\
        .execute()


def get_active_user_sessions(user_id: str) -> list:
    """
    Get all active drawing sessions for a user.
    
    Returns: List of session dicts
    """
    result = supabase.table("drawing_sessions").select("*")\
        .eq("user_id", user_id)\
        .eq("status", "active")\
        .execute()
    
    return result.data if result.data else []


# ==================== TRANSACTIONS ====================

def add_transaction(user_id: str, tx_type: str, amount: int, description: str):
    """
    Record a transaction.
    
    tx_type: "deposit", "purchase", "refund", "reward"
    """
    supabase.table("transactions").insert({
        "user_id": user_id,
        "type": tx_type,
        "amount": amount,
        "description": description,
        "timestamp": datetime.now().isoformat()
    }).execute()


def get_transactions(user_id: str, limit: int = 20) -> list:
    """
    Get recent transactions for a user.
    
    Returns: List of transaction dicts
    """
    result = supabase.table("transactions").select("*")\
        .eq("user_id", user_id)\
        .order("timestamp", desc=True)\
        .limit(limit)\
        .execute()
    
    return result.data if result.data else []


def get_total_revenue() -> int:
    """
    Get total platform revenue (all pixel purchases).
    
    Returns: Total stars earned
    """
    result = supabase.table("transactions").select("amount")\
        .eq("type", "purchase")\
        .execute()
    
    if result.data:
        return sum(tx["amount"] for tx in result.data)
    return 0


# ==================== LEADERBOARD ====================

def get_leaderboard(limit: int = 20) -> list:
    """
    Get top users by pixels owned.
    
    Returns: List of user dicts, sorted by pixels owned
    """
    result = supabase.table("users").select("*")\
        .order("total_pixels_owned", desc=True)\
        .limit(limit)\
        .execute()
    
    return result.data if result.data else []


def get_user_rank(user_id: str) -> int:
    """
    Get a user's rank on the leaderboard.
    
    Returns: Rank number (1-based) or 0 if not found
    """
    leaders = get_leaderboard(1000)  # Check top 1000
    
    for i, leader in enumerate(leaders):
        if leader["user_id"] == user_id:
            return i + 1
    
    return 0


def get_leaderboard_stats() -> dict:
    """
    Get global statistics.
    
    Returns: Dict with total_pixels, total_users, total_stars_spent
    """
    total_pixels = get_pixel_count()
    
    users_result = supabase.table("users").select("id", count="exact").execute()
    total_users = users_result.count if users_result.count else 0
    
    total_revenue = get_total_revenue()
    
    return {
        "total_pixels": total_pixels,
        "total_users": total_users,
        "total_stars_spent": total_revenue
    }


# ==================== ADMIN FUNCTIONS ====================

def get_all_users(limit: int = 100) -> list:
    """
    Get all users (admin function).
    
    Returns: List of user dicts
    """
    result = supabase.table("users").select("*")\
        .order("created_at", desc=True)\
        .limit(limit)\
        .execute()
    
    return result.data if result.data else []


def get_daily_stats() -> dict:
    """
    Get statistics for the last 24 hours.
    
    Returns: Dict with daily stats
    """
    today = datetime.now().isoformat()
    yesterday = (datetime.now() - timedelta(days=1)).isoformat()
    
    # New users in last 24h
    new_users = supabase.table("users").select("id", count="exact")\
        .gte("created_at", yesterday)\
        .execute()
    
    # New pixels in last 24h
    new_pixels = supabase.table("pixels").select("id", count="exact")\
        .gte("purchased_at", yesterday)\
        .execute()
    
    # Revenue in last 24h
    recent_transactions = supabase.table("transactions").select("amount")\
        .eq("type", "purchase")\
        .gte("timestamp", yesterday)\
        .execute()
    
    daily_revenue = sum(tx["amount"] for tx in recent_transactions.data) if recent_transactions.data else 0
    
    return {
        "new_users": new_users.count if new_users.count else 0,
        "new_pixels": new_pixels.count if new_pixels.count else 0,
        "daily_revenue": daily_revenue
    }


# ==================== INITIALIZATION ====================

def initialize_database():
    """
    Verify database connection on startup.
    """
    try:
        # Test query
        result = supabase.table("users").select("id", count="exact").limit(1).execute()
        pixel_count = get_pixel_count()
        user_count = result.count if result.count else 0
        
        print("=" * 50)
        print("🗄️  DATABASE CONNECTED SUCCESSFULLY")
        print("=" * 50)
        print(f"👥 Total Users: {user_count}")
        print(f"🖼️  Total Pixels: {pixel_count}")
        print(f"💰 Total Revenue: {get_total_revenue()} ⭐")
        print("=" * 50)
        
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


# ==================== MAIN ====================

if __name__ == "__main__":
    initialize_database()
