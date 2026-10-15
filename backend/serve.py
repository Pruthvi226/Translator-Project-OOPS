"""Container entrypoint honors the hosting platform's dynamic PORT."""
import os
import uvicorn


if __name__ == '__main__':
    uvicorn.run('backend.app.main:app', host='0.0.0.0', port=int(os.getenv('PORT', '8000')),
                workers=1, proxy_headers=False, access_log=False)
