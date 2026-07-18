"""
HTTP Client Module

This module provides a robust HTTP client for making requests to web services
and APIs. It supports various HTTP methods, authentication schemes, error
handling, retries, and backoff strategies.
"""

import asyncio
import logging
import time
from enum import Enum, auto
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

# Third-party imports with fallback handling
import requests
from requests.adapters import HTTPAdapter
from requests.auth import AuthBase
from urllib3.util.retry import Retry

# Optional async support
try:
    import aiohttp

    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    aiohttp = None  # For type checking

# Logger for the module
logger = logging.getLogger(__name__)


class HttpMethod(Enum):
    """Enumeration of supported HTTP methods"""

    GET = auto()
    POST = auto()
    PUT = auto()
    DELETE = auto()
    PATCH = auto()
    HEAD = auto()
    OPTIONS = auto()


class AuthType(Enum):
    """Enumeration of supported authentication types"""

    NONE = auto()
    BASIC = auto()
    BEARER = auto()
    DIGEST = auto()
    OAUTH = auto()
    API_KEY = auto()
    CUSTOM = auto()


class HttpClientError(Exception):
    """Base exception for HTTP client-related errors"""

    pass


class RequestError(HttpClientError):
    """Exception raised when a request fails"""

    pass


class AuthenticationError(HttpClientError):
    """Exception raised when authentication fails"""

    pass


class RateLimitError(HttpClientError):
    """Exception raised when rate limit is exceeded"""

    pass


class TimeoutError(HttpClientError):
    """Exception raised when a request times out"""

    pass


class ConnectionError(HttpClientError):
    """Exception raised when connection fails"""

    pass


class ResponseError(HttpClientError):
    """Exception raised when response parsing fails"""

    pass


class BearerAuth(AuthBase):
    """Authentication handler for Bearer token auth"""

    def __init__(self, token: str):
        self.token = token

    def __call__(self, r):
        r.headers["Authorization"] = f"Bearer {self.token}"
        return r


class ApiKeyAuth(AuthBase):
    """Authentication handler for API key auth"""

    def __init__(self, key: str, header_name: str = "X-API-Key"):
        self.key = key
        self.header_name = header_name

    def __call__(self, r):
        r.headers[self.header_name] = self.key
        return r


class HttpClient:
    """
    Robust HTTP client for making requests to web services and APIs.

    This client provides a flexible interface for making HTTP requests with
    support for various authentication methods, automatic retries,
    rate limiting, and comprehensive error handling.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        auth_type: AuthType = AuthType.NONE,
        auth_credentials: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        rate_limit: Optional[int] = None,
        verify_ssl: bool = True,
        proxies: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize the HTTP client.

        Args:
            base_url: Optional base URL for all requests
            auth_type: Type of authentication to use
            auth_credentials: Credentials for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            backoff_factor: Backoff factor for retry delay
            rate_limit: Maximum requests per minute (None for no limit)
            verify_ssl: Whether to verify SSL certificates
            proxies: Optional proxy configuration
            headers: Default headers to include in all requests
        """
        self.base_url = base_url
        self.auth_type = auth_type
        self.auth_credentials = auth_credentials or {}
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.rate_limit = rate_limit
        self.verify_ssl = verify_ssl
        self.proxies = proxies or {}
        self.headers = headers or {}

        # Add a user agent that identifies as VEILos
        ua = "VEILos/1.0 Internet Modality Client"
        self.headers.setdefault("User-Agent", ua)

        # Rate limiting state
        self._request_timestamps: List[float] = []
        self._lock = (
            asyncio.Lock()
            if asyncio.get_event_loop_policy().get_event_loop().is_running()
            else None
        )

        # Create session with retry configuration
        self.session = self._create_session()

        # Initialize auth handler
        self.auth = self._setup_auth()

    def _create_session(self) -> requests.Session:
        """
        Create and configure a requests session.

        Returns:
            Configured requests.Session object
        """
        session = requests.Session()

        # Configure retry behavior
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=self.backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=[
                "GET",
                "POST",
                "PUT",
                "DELETE",
                "PATCH",
                "HEAD",
                "OPTIONS",
            ],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Apply default headers
        session.headers.update(self.headers)

        # Apply proxies if configured
        if self.proxies:
            session.proxies.update(self.proxies)

        # Configure SSL verification
        session.verify = self.verify_ssl

        return session

    def _setup_auth(self) -> Optional[AuthBase]:
        """
        Set up authentication based on auth_type and auth_credentials.

        Returns:
            Authentication handler for requests

        Raises:
            AuthenticationError: If authentication configuration is invalid
        """
        try:
            if self.auth_type == AuthType.NONE:
                return None

            elif self.auth_type == AuthType.BASIC:
                if (
                    "username" not in self.auth_credentials
                    or "password" not in self.auth_credentials
                ):
                    raise AuthenticationError(
                        "Basic auth requires username and password"
                    )
                username = self.auth_credentials["username"]
                password = self.auth_credentials["password"]
                return requests.auth.HTTPBasicAuth(username, password)

            elif self.auth_type == AuthType.BEARER:
                if "token" not in self.auth_credentials:
                    raise AuthenticationError("Bearer auth requires token")
                return BearerAuth(self.auth_credentials["token"])

            elif self.auth_type == AuthType.DIGEST:
                if (
                    "username" not in self.auth_credentials
                    or "password" not in self.auth_credentials
                ):
                    raise AuthenticationError(
                        "Digest auth requires username and password"
                    )
                username = self.auth_credentials["username"]
                password = self.auth_credentials["password"]
                return requests.auth.HTTPDigestAuth(username, password)

            elif self.auth_type == AuthType.API_KEY:
                if "key" not in self.auth_credentials:
                    raise AuthenticationError("API key auth requires key")
                default_header = "X-API-Key"
                key = "header_name"
                header_name = self.auth_credentials.get(key, default_header)
                return ApiKeyAuth(self.auth_credentials["key"], header_name)

            elif self.auth_type == AuthType.OAUTH:
                # OAuth authentication should be handled separately
                # This is a placeholder for future implementation
                logger.warning("OAuth authentication not fully implemented")
                return None

            elif self.auth_type == AuthType.CUSTOM:
                # For custom auth, the client code should handle auth manually
                logger.info("Using custom authentication")
                return None

            else:
                error_msg = f"Unsupported auth type: {self.auth_type}"
                raise AuthenticationError(error_msg)

        except Exception as e:
            error_msg = f"Authentication setup failed: {str(e)}"
            logger.error(error_msg)
            raise AuthenticationError(error_msg)

    def _enforce_rate_limit(self) -> None:
        """
        Enforce rate limiting by sleeping if necessary.

        This method tracks request timestamps and delays execution if
        the rate limit would be exceeded.
        """
        if not self.rate_limit:
            return

        current_time = time.time()

        # Remove timestamps older than 60 seconds
        self._request_timestamps = [
            ts for ts in self._request_timestamps if current_time - ts < 60
        ]

        # If we've reached the rate limit, sleep until we can
        # make another request
        if len(self._request_timestamps) >= self.rate_limit:
            sleep_time = 60 - (current_time - self._request_timestamps[0])
            if sleep_time > 0:
                msg = f"Rate limit reached, sleeping for {sleep_time:.2f}s"
                logger.debug(msg)
                time.sleep(sleep_time)

        # Add current request timestamp
        self._request_timestamps.append(time.time())

    async def _async_enforce_rate_limit(self) -> None:
        """
        Async version of rate limit enforcement.
        """
        if not self.rate_limit:
            return

        current_time = time.time()

        async with self._lock:
            # Remove timestamps older than 60 seconds
            self._request_timestamps = [
                ts for ts in self._request_timestamps if current_time - ts < 60
            ]

            # If we've reached the rate limit, sleep until we can
            # make another request
            if len(self._request_timestamps) >= self.rate_limit:
                sleep_time = 60 - (current_time - self._request_timestamps[0])
                if sleep_time > 0:
                    msg = f"Rate limit reached, sleeping for {sleep_time:.2f}s"
                    logger.debug(msg)
                    await asyncio.sleep(sleep_time)

            # Add current request timestamp
            self._request_timestamps.append(time.time())

    def _build_url(self, url: str) -> str:
        """
        Build the complete URL by joining the base URL and path.

        Args:
            url: The URL path or complete URL

        Returns:
            The complete URL
        """
        if self.base_url and not (
            url.startswith("http://") or url.startswith("https://")
        ):
            return urljoin(self.base_url, url)
        return url

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Process the HTTP response and handle errors.

        Args:
            response: The HTTP response

        Returns:
            Dict containing response data

        Raises:
            RequestError: If the request fails
            ResponseError: If response parsing fails
        """
        try:
            # Check if the request was successful (2xx status code)
            response.raise_for_status()

            # Try to parse response as JSON
            try:
                result = response.json()
            except ValueError:
                # Not a JSON response
                result = {"content": response.text}

            # Build and return the response data
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "data": result,
                "url": response.url,
                "elapsed": response.elapsed.total_seconds(),
            }

        except requests.exceptions.HTTPError as e:
            status_code = response.status_code
            error_msg = f"HTTP error {status_code}: {str(e)}"

            # Handle specific status codes
            if status_code == 401:
                raise AuthenticationError(error_msg)
            elif status_code == 429:
                raise RateLimitError(error_msg)
            else:
                raise RequestError(error_msg)

        except ValueError as e:
            error_msg = f"Failed to parse response: {str(e)}"
            logger.error(error_msg)
            raise ResponseError(error_msg)

    def request(
        self,
        method: HttpMethod,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        auth: Optional[AuthBase] = None,
        timeout: Optional[int] = None,
        verify_ssl: Optional[bool] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request.

        Args:
            method: HTTP method to use
            url: URL to request
            data: Optional form data to send
            json_data: Optional JSON data to send
            params: Optional query parameters
            headers: Optional headers to send
            auth: Optional auth handler (overrides instance auth)
            timeout: Optional timeout (overrides instance timeout)
            verify_ssl: Optional SSL verification
                (overrides instance verify_ssl)
            stream: Whether to stream the response

        Returns:
            Dict containing response data

        Raises:
            Various HttpClientError subclasses for different error scenarios
        """
        try:
            # Apply rate limiting if configured
            self._enforce_rate_limit()

            # Build the complete URL
            full_url = self._build_url(url)

            # Merge headers with instance headers
            merged_headers = self.headers.copy()
            if headers:
                merged_headers.update(headers)

            # Prepare request arguments
            # SSL verification setting
            has_ssl = verify_ssl is not None
            ssl_verify = verify_ssl if has_ssl else self.verify_ssl
            # Prepare timeout
            req_timeout = timeout or self.timeout

            request_args = {
                "method": method.name,
                "url": full_url,
                "headers": merged_headers,
                "params": params,
                "data": data,
                "json": json_data,
                "auth": auth or self.auth,
                "timeout": req_timeout,
                "verify": ssl_verify,
                "stream": stream,
            }

            # Log the request
            logger.debug(f"Making {method.name} request to {full_url}")

            # Make the request
            response = self.session.request(**request_args)

            # Process and return the response
            return self._handle_response(response)

        except RateLimitError:
            # Re-raise rate limit errors without modification
            raise

        except AuthenticationError:
            # Re-raise authentication errors without modification
            raise

        except requests.exceptions.Timeout as e:
            error_msg = f"Request timed out: {str(e)}"
            logger.error(error_msg)
            raise TimeoutError(error_msg)

        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error: {str(e)}"
            logger.error(error_msg)
            raise ConnectionError(error_msg)

        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            logger.error(error_msg)
            raise RequestError(error_msg)

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            raise HttpClientError(error_msg)

    async def async_request(
        self,
        method: HttpMethod,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        auth: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Make an asynchronous HTTP request.

        Args:
            method: HTTP method to use
            url: URL to request
            data: Optional form data to send
            json_data: Optional JSON data to send
            params: Optional query parameters
            headers: Optional headers to send
            auth: Optional auth credentials
            timeout: Optional timeout (overrides instance timeout)

        Returns:
            Dict containing response data

        Raises:
            Various HttpClientError subclasses for different error scenarios
        """
        try:
            # Apply rate limiting if configured
            if self._lock:
                await self._async_enforce_rate_limit()
            else:
                self._enforce_rate_limit()

            # Build the complete URL
            full_url = self._build_url(url)

            # Merge headers with instance headers
            merged_headers = self.headers.copy()
            if headers:
                merged_headers.update(headers)

            # Prepare authentication
            auth_headers = {}
            if auth:
                # Simple auth header handling for async requests
                if "type" in auth and auth["type"] == "bearer":
                    auth_headers["Authorization"] = f"Bearer {auth['token']}"
                elif "type" in auth and auth["type"] == "basic":
                    import base64

                    auth_str = f"{auth['username']}:{auth['password']}"
                    encoded = base64.b64encode(auth_str.encode()).decode()
                    auth_headers["Authorization"] = f"Basic {encoded}"
                elif "type" in auth and auth["type"] == "api_key":
                    header_name = auth.get("header_name", "X-API-Key")
                    auth_headers[header_name] = auth["key"]

            merged_headers.update(auth_headers)

            # Log the request
            logger.debug(f"Making async {method.name} request to {full_url}")

            # Create aiohttp session and make the request
            async with aiohttp.ClientSession() as session:
                # Determine timeout value
                req_timeout = timeout or self.timeout
                # Convert to aiohttp format
                timeout_obj = aiohttp.ClientTimeout(total=req_timeout)

                # Prepare request arguments
                request_args = {
                    "method": method.name,
                    "url": full_url,
                    "headers": merged_headers,
                    "params": params,
                    "data": data,
                    "json": json_data,
                    "timeout": timeout_obj,
                    "ssl": None if not self.verify_ssl else None,
                }

                # Make the request
                async with session.request(**request_args) as response:
                    # Check if the request was successful
                    if response.status >= 400:
                        text = await response.text()
                        status_code = response.status
                        error_msg = f"HTTP error {status_code}: {text}"

                        # Handle specific status codes
                        if status_code == 401:
                            raise AuthenticationError(error_msg)
                        elif status_code == 429:
                            raise RateLimitError(error_msg)
                        else:
                            raise RequestError(error_msg)

                    # Try to parse response as JSON
                    try:
                        result = await response.json()
                    except ValueError:
                        # Not a JSON response
                        text = await response.text()
                        result = {"content": text}

                    # Build and return the response data
                    return {
                        "status_code": response.status,
                        "headers": dict(response.headers),
                        "data": result,
                        "url": str(response.url),
                        "elapsed": None,  # Not available in aiohttp
                    }

        except RateLimitError:
            # Re-raise rate limit errors without modification
            raise

        except AuthenticationError:
            # Re-raise authentication errors without modification
            raise

        except asyncio.TimeoutError as e:
            error_msg = f"Request timed out: {str(e)}"
            logger.error(error_msg)
            raise TimeoutError(error_msg)

        except aiohttp.ClientConnectorError as e:
            error_msg = f"Connection error: {str(e)}"
            logger.error(error_msg)
            raise ConnectionError(error_msg)

        except aiohttp.ClientError as e:
            error_msg = f"Request failed: {str(e)}"
            logger.error(error_msg)
            raise RequestError(error_msg)

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            raise HttpClientError(error_msg)

    # Convenience methods for common HTTP methods
    def get(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make a GET request"""
        return self.request(HttpMethod.GET, url, **kwargs)

    def post(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make a POST request"""
        return self.request(HttpMethod.POST, url, **kwargs)

    def put(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make a PUT request"""
        return self.request(HttpMethod.PUT, url, **kwargs)

    def delete(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make a DELETE request"""
        return self.request(HttpMethod.DELETE, url, **kwargs)

    def patch(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make a PATCH request"""
        return self.request(HttpMethod.PATCH, url, **kwargs)

    # Async convenience methods
    async def async_get(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make an async GET request"""
        return await self.async_request(HttpMethod.GET, url, **kwargs)

    async def async_post(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make an async POST request"""
        return await self.async_request(HttpMethod.POST, url, **kwargs)

    async def async_put(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make an async PUT request"""
        return await self.async_request(HttpMethod.PUT, url, **kwargs)

    async def async_delete(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make an async DELETE request"""
        return await self.async_request(HttpMethod.DELETE, url, **kwargs)

    async def async_patch(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make an async PATCH request"""
        return await self.async_request(HttpMethod.PATCH, url, **kwargs)

    def close(self) -> None:
        """Close the HTTP session and release resources"""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
