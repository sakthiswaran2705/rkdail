from fastapi import APIRouter
from bson import ObjectId
from common_urldb import db
router = APIRouter()
col_category = db["category"]
col_shop = db["shop"]
col_reviews = db["reviews"]


# Convert ObjectId → String
def serialize(doc):
    doc["_id"] = str(doc["_id"])
    return doc

# CATEGORY API
@router.get("/category/get")
def get_categories():
    try:
        data = list(col_category.find())
        data = [serialize(c) for c in data]
        return {"status": True, "data": data}
    except Exception as e:
        return {"status": False, "error": str(e)}
# GET ALL SHOPS   REQUIRED FOR TOP RATING
@router.get("/shop/all")
def get_all_shops():
    try:
        shops = list(col_shop.find())
        for s in shops:
            s["_id"] = str(s["_id"])
        return {"status": True, "data": shops}
    except Exception as e:
        return {"status": False, "error": str(e)}
# SHOP PHOTOS API
@router.get("/shop/photos")
def get_shop_photos(id: str):
    try:
        shop = col_shop.find_one({"_id": ObjectId(id)})
        if not shop:
            return {"status": False, "message": "Shop not found"}

        photos = shop.get("photos", [])
        return {"status": True, "photos": photos}

    except Exception as e:
        return {"status": False, "error": str(e)}
# GET REVIEWS FOR A SHOP
@router.get("/shop/reviews")
def get_reviews(id: str):
    try:
        reviews = list(col_reviews.find({"shop_id": id}))
        for r in reviews:
            r["_id"] = str(r["_id"])
        return {"status": True, "reviews": reviews}

    except Exception as e:
        return {"status": False, "error": str(e)}

# ADD REVIEW
@router.post("/shop/review/add")
def add_review(payload: dict):
    try:
        shop_id = payload.get("shop_id")
        rating = payload.get("rating")
        review = payload.get("review")

        if not shop_id:
            return {"status": False, "message": "shop_id missing"}
        if rating is None:
            return {"status": False, "message": "rating missing"}
        if not review:
            return {"status": False, "message": "review missing"}

        data = {
            "shop_id": shop_id,
            "rating": rating,
            "review": review,
        }

        inserted = col_reviews.insert_one(data)
        data["_id"] = str(inserted.inserted_id)

        return {"status": True, "message": "Review added", "data": data}

    except Exception as e:
        return {"status": False, "error": str(e)}
