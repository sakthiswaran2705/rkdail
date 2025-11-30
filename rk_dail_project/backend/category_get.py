from fastapi import APIRouter, Query
from bson import ObjectId
from common_urldb import db
router = APIRouter()

col_shop = db["shop"]
col_city = db["city"]
col_category = db["category"]
col_reviews = db["reviews"]

def safe(x):
    if isinstance(x, ObjectId):
        return str(x)
    if isinstance(x, list):
        return [safe(i) for i in x]
    if isinstance(x, dict):
        return {k: safe(v) for k, v in x.items()}
    return x

@router.get("/category/static/")
def get_static(
    place: str | None = Query(None),
    name: str | None = Query(None)
):

    if not name:
        return {"data": []}

    name_lower = name.lower()
    place_lower = place.lower() if place else None

    # CATEGORY CHECK
    cat_object_id = ObjectId(name) if ObjectId.is_valid(name) else None

    matched_categories = list(col_category.find({
        "name": {"$regex": name_lower, "$options": "i"}
    }))

    if cat_object_id:
        cat = col_category.find_one({"_id": cat_object_id})
        if cat:
            matched_categories.append(cat)

    matched_cat_ids = [c["_id"] for c in matched_categories]

    # SHOP QUERY
    query = {
        "$or": [
            {"name": {"$regex": name_lower, "$options": "i"}},
            {"shop_name": {"$regex": name_lower, "$options": "i"}},
            {"keywords": {"$regex": name_lower, "$options": "i"}},
            {"category": {"$in": matched_cat_ids}},
            {"category": {"$in": [str(x) for x in matched_cat_ids]}},
            {"category": {"$regex": name_lower, "$options": "i"}},
        ]
    }

    shops = list(col_shop.find(query))
    final_output = []

    # CALCULATE RATINGS
    for s in shops:
        sid = str(s["_id"])
        shop_reviews = list(col_reviews.find({"shop_id": sid}))

        # AVERAGE RATING
        if shop_reviews:
            avg_rating = sum([r.get("rating", 0) for r in shop_reviews]) / len(shop_reviews)
        else:
            avg_rating = 0

        # CITY FILTER
        city = None
        cid = s.get("city_id")
        if isinstance(cid, ObjectId):
            city = col_city.find_one({"_id": cid})
        elif isinstance(cid, str) and ObjectId.is_valid(cid):
            city = col_city.find_one({"_id": ObjectId(cid)})

        if place_lower and city:
            if city.get("city_name", "").lower() != place_lower:
                continue

        # CATEGORY LIST
        final_categories = []
        for c in s.get("category", []):
            if isinstance(c, ObjectId):
                cat = col_category.find_one({"_id": c})
            elif isinstance(c, str) and ObjectId.is_valid(c):
                cat = col_category.find_one({"_id": ObjectId(c)})
            else:
                cat = col_category.find_one({"name": c})
            if cat:
                final_categories.append(safe(cat))

        # PHOTO
        photo = None
        photos = s.get("photos")
        if isinstance(photos, list) and photos:
            photo = {"data": photos[0], "content_type": "image/jpeg"}

        final_output.append({
            "shop": safe(s),
            "categories": final_categories,
            "city": safe(city) if city else None,
            "photo": safe(photo),
            "shop_name": s.get("shop_name") or s.get("name") or "",
            "avg_rating": round(avg_rating, 1),     
            "reviews_count": len(shop_reviews),
        })

    #SORT HIGH TO  LOW RATING
    final_output.sort(key=lambda x: x["avg_rating"], reverse=True)

    return {"data": final_output}
