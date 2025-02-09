from typing import Optional, Set
import gzip
import brotli
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.datastructures import Headers
from app.core.logging import logger

class CompressionMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        minimum_size: int = 500,
        compressible_types: Optional[Set[str]] = None
    ):
        super().__init__(app)
        self.minimum_size = minimum_size
        self.compressible_types = compressible_types or {
            'text/plain',
            'text/html',
            'text/css',
            'text/javascript',
            'application/javascript',
            'application/json',
            'application/xml',
            'application/x-yaml'
        }

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        if not self._should_compress(request, response):
            return response

        return await self._compress_response(request, response)

    def _should_compress(self, request: Request, response: Response) -> bool:
        # Check if client accepts compression
        accept_encoding = request.headers.get('Accept-Encoding', '')
        if not ('gzip' in accept_encoding or 'br' in accept_encoding):
            return False

        # Check content type
        content_type = response.headers.get('Content-Type', '').split(';')[0]
        if content_type not in self.compressible_types:
            return False

        # Check content length
        content_length = len(response.body) if hasattr(response, 'body') else 0
        if content_length < self.minimum_size:
            return False

        return True

    async def _compress_response(
        self,
        request: Request,
        response: Response
    ) -> Response:
        accept_encoding = request.headers.get('Accept-Encoding', '')
        content = response.body

        # Try brotli first if supported
        if 'br' in accept_encoding:
            try:
                compressed = brotli.compress(content)
                return Response(
                    content=compressed,
                    status_code=response.status_code,
                    headers=self._get_compressed_headers(
                        response.headers,
                        'br',
                        len(content),
                        len(compressed)
                    ),
                    media_type=response.media_type
                )
            except Exception as e:
                logger.error(f"Brotli compression failed: {str(e)}")

        # Fall back to gzip
        if 'gzip' in accept_encoding:
            try:
                compressed = gzip.compress(content)
                return Response(
                    content=compressed,
                    status_code=response.status_code,
                    headers=self._get_compressed_headers(
                        response.headers,
                        'gzip',
                        len(content),
                        len(compressed)
                    ),
                    media_type=response.media_type
                )
            except Exception as e:
                logger.error(f"Gzip compression failed: {str(e)}")

        return response

    def _get_compressed_headers(
        self,
        headers: Headers,
        encoding: str,
        original_size: int,
        compressed_size: int
    ) -> Dict[str, str]:
        new_headers = dict(headers)
        new_headers['Content-Encoding'] = encoding
        new_headers['Content-Length'] = str(compressed_size)
        new_headers['X-Compression-Ratio'] = f"{compressed_size/original_size:.2f}"
        return new_headers 