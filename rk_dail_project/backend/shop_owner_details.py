from fastapi import APIRouter, Form, UploadFile, File, Query
from bson import ObjectId
from datetime import datetime
import hashlib, base64
from common_urldb import db
router = APIRouter()
col_user = db["user"]
col_shop = db["shop"]
col_city = db["city"]
col_category = db["category"]
col_offers = db["slideshow"]


def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()


def oid(x):
    return str(x) if isinstance(x, ObjectId) else x


#REGISTER
@router.post("/register/")
def register(email: str = Form(...), password: str = Form(...)):
    if col_user.find_one({"email": email}):
        return {"status": "error", "message": "Email already exists"}

    hashed_pwd = hash_password(password)
    user_id = col_user.insert_one({"email": email, "password": hashed_pwd}).inserted_id

    return {"status": "success", "user_id": str(user_id)}


#LOGIN
@router.post("/login/")
def login(email: str = Form(...), password: str = Form(...)):
    user = col_user.find_one({"email": email})

    # Check login
    if not user or hash_password(password) != user["password"]:
        return {"status": "error", "message": "Invalid email or password"}
    # Get shops
    result = get_user_shops(str(user["_id"]))
    shops = result.get("data", [])
    return {
        "status": "success",
        "data": {
            "user_id": str(user["_id"]),
            "shops": shops
        }
    }
#SEARCH CATEGORY
@router.get("/search_category")
def search_category(query: str = Query("")):
    data = list(col_category.find({"name": {"$regex": query, "$options": "i"}}))
    return {"status": "success", "data": [{**item, "_id": oid(item["_id"])} for item in data]}


#SEARCH CITY
@router.get("/search_city")
def search_city(query: str = Query("")):
    data = list(col_city.find({"city_name": {"$regex": query, "$options": "i"}}).limit(20))
    return {"status": "success", "data": [{**item, "_id": oid(item["_id"])} for item in data]}


#ADD SHOP
@router.post("/add_shop/")
def add_shop(
    user_id: str = Form(...),
    shop_name: str = Form(...),
    description: str = Form(...),
    address: str = Form(...),
    phone_number: str = Form(...),
    email: str = Form(...),
    landmark: str = Form(...),
    category_list: str = Form(...),
    city_name: str = Form(...),
    district: str = Form(...),
    pincode: str = Form(...),
    state: str = Form(...),
    photos: list[UploadFile] = File(None),
    keywords: str = Form(...)
):
    try:
        u_oid = ObjectId(user_id)
    except:
        return {"status": "error", "message": "Invalid user id"}

    # City
    city_data = {"city_name": city_name, "district": district, "pincode": pincode, "state": state}
    existing_city = col_city.find_one(city_data)
    city_id = existing_city["_id"] if existing_city else col_city.insert_one(city_data).inserted_id

    # Categories
    cat_ids = []
    for name in category_list.split(","):
        name = name.strip()
        cat = col_category.find_one({"name": name})
        if not cat:
            return {"status": "error", "message": f"Category '{name}' not found"}
        cat_ids.append(str(cat["_id"]))

    # Photos
    photos_b64 = []
    if photos:
        for f in photos:
            photos_b64.append(base64.b64encode(f.file.read()).decode())

    col_shop.insert_one({
        "shop_name": shop_name,
        "description": description,
        "address": address,
        "phone_number": phone_number,
        "email": email,
        "landmark": landmark,
        "category": cat_ids,
        "city_id": str(city_id),
        "photos": photos_b64,
        "keywords": [k.strip() for k in keywords.split(",") if k.strip()],
        "user_id": u_oid
    })

    return {"status": "success", "message": "Shop added"}


#UPDATE SHOP
@router.post("/update_shop/")
def update_shop(
    shop_id: str = Form(...),
    shop_name: str = Form(None),
    description: str = Form(None),
    address: str = Form(None),
    phone_number: str = Form(None),
    email: str = Form(None),
    landmark: str = Form(None),
    category_list: str = Form(None),
    city_name: str = Form(None),
    district: str = Form(None),
    pincode: str = Form(None),
    state: str = Form(None),
    keywords: str = Form(None),
    photos: list[UploadFile] = File(None)
):
    try:
        soid = ObjectId(shop_id)
    except:
        return {"status": "error", "message": "Invalid shop id"}

    update = {}

    if shop_name: update["shop_name"] = shop_name
    if description: update["description"] = description
    if address: update["address"] = address
    if phone_number: update["phone_number"] = phone_number
    if email: update["email"] = email
    if landmark: update["landmark"] = landmark

    if category_list:
        new_ids = []
        for name in category_list.split(","):
            name = name.strip()
            cat = col_category.find_one({"name": name})
            if not cat:
                return {"status": "error", "message": f"Category '{name}' not found"}
            new_ids.append(str(cat["_id"]))
        update["category"] = new_ids

    if city_name:
        city_data = {"city_name": city_name, "district": district, "pincode": pincode, "state": state}
        existing_city = col_city.find_one(city_data)
        city_id = existing_city["_id"] if existing_city else col_city.insert_one(city_data).inserted_id
        update["city_id"] = str(city_id)

    if keywords:
        update["keywords"] = [k.strip() for k in keywords.split(",") if k.strip()]

    if photos:
        old_photos = col_shop.find_one({"_id": soid}).get("photos", [])
        new_b64 = [base64.b64encode(f.file.read()).decode() for f in photos]
        update["photos"] = old_photos + new_b64

    col_shop.update_one({"_id": soid}, {"$set": update})
    return {"status": "success", "message": "Shop updated"}


# DELETE SHOP
@router.post("/delete_shop/")
def delete_shop(shop_id: str = Form(...)):
    try:
        soid = ObjectId(shop_id)
    except:
        return {"status": "error", "message": "Invalid shop id"}

    res = col_shop.delete_one({"_id": soid})
    return {"status": "success", "message": "Shop deleted"} if res.deleted_count else {"status": "error", "message": "Shop not found"}


#DELETE SHOP PHOTO
@router.post("/delete_photo/")
def delete_photo(shop_id: str = Form(...), photo_index: int = Form(...)):
    try:
        soid = ObjectId(shop_id)
    except:
        return {"status": "error", "message": "Invalid shop id"}

    shop = col_shop.find_one({"_id": soid})
    if not shop:
        return {"status": "error", "message": "Shop not found"}

    photos = shop.get("photos", [])
    if not (0 <= photo_index < len(photos)):
        return {"status": "error", "message": "Invalid photo index"}

    photos.pop(photo_index)
    col_shop.update_one({"_id": soid}, {"$set": {"photos": photos}})
    return {"status": "success", "message": "Photo deleted"}


#GET SHOPS WITH OFFERS
@router.get("/get_shops/{user_id}")
def get_user_shops(user_id: str):
    try:
        uid = ObjectId(user_id)
    except:
        return {"status": "error", "message": "Invalid user id"}

    shops = list(col_shop.find({"user_id": uid}))
    final = []

    for s in shops:
        s_clean = {k: oid(v) for k, v in s.items()}

        # Categories
        categories = []
        for cid in s.get("category", []):
            try:
                c = col_category.find_one({"_id": ObjectId(cid)})
                if c:
                    categories.append({k: oid(v) for k, v in c.items()})
            except:
                pass

        # City
        city_doc = None
        if s.get("city_id"):
            c = col_city.find_one({"_id": ObjectId(s["city_id"])})
            if c:
                city_doc = {k: oid(v) for k, v in c.items()}

        # Offers
        offer_docs = list(col_offers.find({"shop_ids": s_clean["_id"]}).sort("uploaded_at", -1))
        offers_b64, offers_types, offer_ids = [], [], []

        for od in offer_docs:
            fb64 = od.get("file_base64")
            ftype = od.get("file_type", "image")
            if fb64:
                offers_b64.append(fb64)
                offers_types.append(ftype)
                offer_ids.append(oid(od["_id"]))   # <-- important for delete

        final.append({
            "shop": s_clean,
            "categories": categories,
            "city": city_doc,
            "offers": offers_b64,
            "offer_types": offers_types,
            "offer_ids": offer_ids
        })

    return {"status": "success", "data": final}


@router.post("/add_offer/")
def add_offer(user_id: str = Form(...), target_shop: str = Form(...), file: UploadFile = File(...)):
    try:
        u_oid = ObjectId(user_id)
    except:
        return {"status": "error", "message": "Invalid user id"}

    shop_ids, city_ids = [], []

    # All shops
    if target_shop == "ALL":
        shops = list(col_shop.find({"user_id": u_oid}))
        if not shops:
            return {"status": "error", "message": "No shops found"}
        for s in shops:
            shop_ids.append(str(s["_id"]))
            city_ids.append(s.get("city_id"))

    # Single shop
    else:
        try:
            soid = ObjectId(target_shop)
        except:
            return {"status": "error", "message": "Invalid shop id"}

        shop = col_shop.find_one({"_id": soid})
        if not shop:
            return {"status": "error", "message": "Shop not found"}

        shop_ids.append(str(shop["_id"]))
        city_ids.append(shop.get("city_id"))

    # File processing
    fbytes = file.file.read()
    fb64 = base64.b64encode(fbytes).decode()

    if file.content_type.startswith("video/"): ftype = "video"
    elif file.content_type.startswith("image/"): ftype = "image"
    else: return {"status": "error", "message": "Only image/video allowed"}

    col_offers.insert_one({
        "user_id": user_id,
        "shop_ids": shop_ids,
        "city_ids": city_ids,
        "file_base64": fb64,
        "file_type": ftype,
        "filename": file.filename,
        "uploaded_at": datetime.utcnow(),
    })

    return {"status": "success", "message": "Offer added successfully"}


@router.post("/delete_offer/")
def delete_offer(offer_id: str = Form(...)):
    try:
        oidv = ObjectId(offer_id)
    except:
        return {"status": "error", "message": "Invalid offer id"}

    res = col_offers.delete_one({"_id": oidv})
    return {"status": "success", "message": "Offer deleted"} if res.deleted_count else {"status": "error", "message": "Offer not found"}
