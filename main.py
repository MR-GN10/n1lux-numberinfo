import os
from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
import duckdb

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Hugging Face Token from Environment
HF_TOKEN = os.getenv("HF_TOKEN", "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")

# DuckDB Connection
con = None

@app.on_event("startup")
def startup():
    global con
    con = duckdb.connect()
    con.execute("INSTALL httpfs;")
    con.execute("LOAD httpfs;")
    
    # Set authentication header for all HTTP requests
    if HF_TOKEN:
        con.execute(f"SET http_headers = 'Authorization: Bearer {HF_TOKEN}';")
        print("✅ Hugging Face authentication configured")
    else:
        print("⚠️ No HF_TOKEN found, trying without authentication")

@app.on_event("shutdown")
def shutdown():
    global con
    if con:
        con.close()
        print("✅ Database connection closed")

# ... (LANDING_PAGE_HTML and all other functions remain exactly as before)
# I'll include the full code below for easy copy-paste.

# LANDING_PAGE_HTML = ... (keep your existing HTML)

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return JSONResponse(
            status_code=404,
            content={
                "status": "rejected",
                "message": "Invalid endpoint. STRICTLY use /FetchData?Number=XXXXXXXXXX",
                "Developer": "@Maybechx"
            }
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "Developer": "@Maybechx"}
    )

@app.get("/", response_class=HTMLResponse)
def root_landing_page():
    return HTMLResponse(content=LANDING_PAGE_HTML, status_code=200)

@app.get("/FetchData")
def fetch_data(Number: str = Query(None)):
    if not Number or not Number.isdigit() or len(Number) < 10 or len(Number) > 15:
        return JSONResponse(
            status_code=400,
            content={
                "status": "rejected",
                "message": "Invalid parameter. STRICTLY use /FetchData?Number=XXXXXXXXXX",
                "Developer": "@Maybechx"
            }
        )
    
    last_digit = Number[-1]
    primary_url = f"https://huggingface.co/datasets/CutehackX/hitek-data-bucket/resolve/main/final_master_shard_{last_digit}.parquet"
    alt_url = f"https://huggingface.co/datasets/CutehackX/hitek-data-bucket/resolve/main/alt_master_shard_{last_digit}.parquet"
    
    main_records = []
    alt_records = []
    
    try:
        main_query = f"SELECT * FROM read_parquet('{primary_url}') WHERE mobile = '{Number}'"
        main_res = con.execute(main_query)
        main_cols = [desc[0] for desc in main_res.description] if main_res.description else []
        main_rows = main_res.fetchall()
        for row in main_rows:
            main_records.append(dict(zip(main_cols, row)))
    except Exception as e:
        pass
    
    try:
        alt_query = f"SELECT * FROM read_parquet('{alt_url}') WHERE alt = '{Number}'"
        alt_res = con.execute(alt_query)
        alt_cols = [desc[0] for desc in alt_res.description] if alt_res.description else []
        alt_rows = alt_res.fetchall()
        for row in alt_rows:
            alt_records.append(dict(zip(alt_cols, row)))
    except Exception as e:
        pass
    
    if not main_records and not alt_records:
        return JSONResponse(
            status_code=404,
            content={
                "status": "not_found",
                "phone": Number,
                "Developer": "@Maybechx"
            }
        )
    
    return {
        "status": "success",
        "Data": {
            "Main_Records": main_records,
            "Alt_Records": alt_records
        },
        "Developer": "@Maybechx"
    }
