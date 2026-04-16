# Copyright (c) 2024-2026 Morris A. Aguilar. All Rights Reserved.
# Licensed under the Apache License, Version 2.0.
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.routers import aggregate, guidelines, inference, patients

load_dotenv()

app = FastAPI(title="QuICR API", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(patients.router, prefix="/api")
app.include_router(aggregate.router, prefix="/api")
app.include_router(guidelines.router, prefix="/api")
app.include_router(inference.router, prefix="/api")
