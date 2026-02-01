from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI


def add_cors(app: FastAPI) -> None:
    """Enable permissive CORS for development/network-readiness.

    Tighten origins and methods when authentication is introduced.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
