from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import Routers
from category_get import router as category_router
from shop_owner_details import router as owner_router
from category_show_home import router as category_home_router

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(category_router)
app.include_router(owner_router)
app.include_router(category_home_router)

@app.get("/")
def root():
    return {"message": "API is running!"}
