from fastapi import {%- if 'crud' in project_type %}FastAPI, HTTPException{% else %}FastAPI{% endif -%}
{%- if 'crud' in project_type %}from pydantic import BaseModel{% endif -%}
from typing import {%- if 'crud' in project_type %}List, Optional{% else %}Dict, Any{% endif -%}
import logging

app = FastAPI(
    title="{{ name|title }} API",
    description="{{ description }}",
    version="{{ version }}"
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

{% if 'crud' in project_type %}
# Models
class Item(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    price: float = 0.0

# Sample data
items_db: List[Item] = []

@app.get("/")
async def root():
    return {"message": "Welcome to {{ name }} API"}

@app.get("/items", response_model=List[Item])
async def get_items():
    return items_db

@app.post("/items", response_model=Item)
async def create_item(item: Item):
    items_db.append(item)
    return item

@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int):
    try:
        return items_db[item_id]
    except IndexError:
        raise HTTPException(status_code=404, detail="Item not found")

@app.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, item: Item):
    try:
        items_db[item_id] = item
        return items_db[item_id]
    except IndexError:
        raise HTTPException(status_code=404, detail="Item not found")

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    try:
        items_db.pop(item_id)
        return {"message": "Item deleted"}
    except IndexError:
        raise HTTPException(status_code=404, detail="Item not found")
{% else %}
@app.get("/")
async def root():
    return {"message": "Welcome to {{ name }} API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/items/")
async def get_items():
    # Return some sample data
    return [
        {"id": 1, "name": "Sample Item 1"},
        {"id": 2, "name": "Sample Item 2"}
    ]

@app.post("/items/")
async def create_item(item: Dict[str, Any]):
    # Handle item creation
    logger.info(f"Creating item: {item}")
    return {"id": 1, "message": "Item created", "item": item}
{% endif %}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)