"""
Professional AI - Compression Middleware
Gzip and Brotli compression for faster response times.
"""

from typing import Callable, Optional
from fastapi import Request
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

try:
    import brotli as brotli_module
    BROTLI_AVAILABLE = True
except ImportError:
    BROTLI_AVAILABLE = False

try:
    import gzip
    GZIP_AVAILABLE = True
except ImportError:
    GZIP_AVAILABLE = False


class CompressionMiddleware(BaseHTTPMiddleware):
    """
    Compression middleware with Brotli (preferred) and Gzip fallback.
    Reduces response size by 60-80% for text-based content.
    """

    # Minimum size to compress (1KB)
    MIN_SIZE = 1024

    # Content types to compress
    COMPRESSIBLE_TYPES = {
        'text/html',
        'text/css',
        'text/xml',
        'text/plain',
        'application/json',
        'application/javascript',
        'application/xml',
        'application/rss+xml',
        'application/atom+xml',
        'image/svg+xml',
        'application/wasm',
    }

    def __init__(self, app, minimum_size: int = 1024):
        super().__init__(app)
        self.minimum_size = minimum_size

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Skip if response is already compressed
        if response.headers.get('Content-Encoding'):
            return response

        # Skip if body is too small
        body = b''
        async for chunk in response.body_iterator:
            body += chunk

        if len(body) < self.minimum_size:
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        # Check if content type is compressible
        content_type = response.headers.get('Content-Type', '')
        if not any(ct in content_type for ct in self.COMPRESSIBLE_TYPES):
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        # Get accepted encodings
        accept_encoding = request.headers.get('Accept-Encoding', '')
        
        # Try Brotli first (better compression)
        if BROTLI_AVAILABLE and 'br' in accept_encoding:
            compressed = self._brotli_compress(body)
            if compressed:
                response.headers['Content-Encoding'] = 'br'
                response.headers['Content-Length'] = str(len(compressed))
                response.headers['Vary'] = 'Accept-Encoding'
                return Response(
                    content=compressed,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                )

        # Fallback to Gzip
        if GZIP_AVAILABLE and 'gzip' in accept_encoding:
            compressed = self._gzip_compress(body)
            if compressed:
                response.headers['Content-Encoding'] = 'gzip'
                response.headers['Content-Length'] = str(len(compressed))
                response.headers['Vary'] = 'Accept-Encoding'
                return Response(
                    content=compressed,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                )

        # No compression
        return Response(
            content=body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )

    def _brotli_compress(self, data: bytes) -> Optional[bytes]:
        """Compress data with Brotli."""
        if not BROTLI_AVAILABLE:
            return None
        try:
            return brotli_module.compress(data, quality=4)
        except Exception as e:
            logger.debug(f"Brotli compression failed: {e}")
            return None

    def _gzip_compress(self, data: bytes) -> Optional[bytes]:
        """Compress data with Gzip."""
        if not GZIP_AVAILABLE:
            return None
        try:
            import io
            buffer = io.BytesIO()
            with gzip.GzipFile(fileobj=buffer, mode='wb', compresslevel=6) as f:
                f.write(data)
            return buffer.getvalue()
        except Exception as e:
            logger.debug(f"Gzip compression failed: {e}")
            return None