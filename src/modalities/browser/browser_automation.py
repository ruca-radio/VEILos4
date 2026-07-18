import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
from typing import Optional, Dict, Any
import os

logger = logging.getLogger(__name__)

class BrowserAutomationError(Exception):
    """Custom exception for browser automation errors."""
    pass

class BrowserAutomationClient:
    """Manages a headless browser for automation tasks."""

    def __init__(
        self,
        browser_type: str = "chrome",
        headless: bool = True,
        timeout: int = 10,
        driver_path: Optional[str] = None,
    ):
        self.browser_type = browser_type.lower()
        self.headless = headless
        self.timeout = timeout
        self.driver_path = driver_path
        self.driver: Optional[webdriver.Remote] = None
        self._initialize_driver()

    def _initialize_driver(self):
        """
        Initializes the WebDriver based on the configured browser_type.
        """
        if self.browser_type == "chrome":
            options = webdriver.ChromeOptions()
            if self.headless:
                options.add_argument("--headless")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--window-size=1920,1080")
            
            if self.driver_path:
                service = Service(self.driver_path)
                self.driver = webdriver.Chrome(service=service, options=options)
            else:
                self.driver = webdriver.Chrome(options=options)
        else:
            raise BrowserAutomationError(f"Unsupported browser type: {self.browser_type}")
        
        logger.info(f"Browser initialized: {self.browser_type} (headless={self.headless})")

    def navigate(self, url: str) -> str:
        """
        Navigates the browser to the specified URL and returns the page title.
        """
        try:
            if not self.driver:
                self._initialize_driver() # Re-initialize if driver somehow lost
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            WebDriverWait(self.driver, self.timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            return self.driver.title
        except WebDriverException as e:
            raise BrowserAutomationError(f"Failed to navigate to {url}: {e}")

    def get_page_source(self) -> str:
        """
        Returns the full HTML source of the current page.
        """
        if not self.driver:
            raise BrowserAutomationError("Browser not initialized. Call navigate() first.")
        return self.driver.page_source

    def close(self):
        """
        Closes the browser and quits the WebDriver session.
        """
        if self.driver:
            logger.info("Closing browser.")
            self.driver.quit()
            self.driver = None

    # Additional methods like click, type, find_element will be added later
