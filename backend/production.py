"""Serve the built frontend and API from one production origin."""
import os
from pathlib import Path

import uvicorn
from fastapi.staticfiles import StaticFiles

from .main import router


def create_app():
    directory = Path(os.environ.get('NETSIM_STATIC_DIR', Path(__file__).resolve().parents[1] / 'frontend' / 'dist')).resolve()
    if not (directory / 'index.html').is_file():
        raise RuntimeError(f'Frontend build missing at {directory}. Run npm ci and npm run build in frontend before starting production.')
    # API and documentation routes precede the static mount. Missing files
    # remain 404s instead of returning HTML to an API or asset request.
    from fastapi import FastAPI
    production = FastAPI(title='NetSim Lite')
    production.include_router(router)
    production.mount('/', StaticFiles(directory=directory, html=True), name='frontend')
    return production


def main():
    try:
        port = int(os.environ.get('PORT', '8000'))
    except ValueError as error:
        raise ValueError('PORT must be an integer between 1 and 65535') from error
    if not 1 <= port <= 65535:
        raise ValueError('PORT must be an integer between 1 and 65535')
    uvicorn.run(create_app(), host=os.environ.get('HOST', '0.0.0.0'), port=port)


if __name__ == '__main__':
    main()
