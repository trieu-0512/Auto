# CDP Host - Chrome DevTools Protocol Controller
# Connect to Orbita browser via CDP WebSocket

import json
import asyncio
import aiohttp
import websockets
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
import base64
import os


@dataclass
class CDPResponse:
    """Response from CDP command."""
    id: int
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    
    @property
    def success(self) -> bool:
        return self.error is None


class CDPHost:
    """
    CDP Host - Controls browser via Chrome DevTools Protocol.
    No WebDriver, no Selenium - pure CDP over WebSocket.
    """
    
    def __init__(self, debug_port: int = 9222):
        self.debug_port = debug_port
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.ws_url: Optional[str] = None
        self.command_id = 0
        self.pending_commands: Dict[int, asyncio.Future] = {}
        self.event_handlers: Dict[str, List[Callable]] = {}
        self._listener_task: Optional[asyncio.Task] = None
    
    async def connect(self, target_id: str = None) -> bool:
        """
        Connect to browser CDP endpoint.
        
        Args:
            target_id: Specific target/tab ID, or None for first page
        """
        try:
            # Get WebSocket URL from /json/version or /json
            base_url = f"http://127.0.0.1:{self.debug_port}"
            
            async with aiohttp.ClientSession() as session:
                if target_id:
                    # Connect to specific target
                    async with session.get(f"{base_url}/json") as resp:
                        targets = await resp.json()
                        for t in targets:
                            if t.get('id') == target_id:
                                self.ws_url = t.get('webSocketDebuggerUrl')
                                break
                else:
                    # Get first page target
                    async with session.get(f"{base_url}/json") as resp:
                        targets = await resp.json()
                        for t in targets:
                            if t.get('type') == 'page':
                                self.ws_url = t.get('webSocketDebuggerUrl')
                                break
            
            if not self.ws_url:
                print("No WebSocket URL found")
                return False
            
            # Connect WebSocket
            self.ws = await websockets.connect(self.ws_url, max_size=50 * 1024 * 1024)
            
            # Start listener
            self._listener_task = asyncio.create_task(self._listen())
            
            # Enable required domains
            await self.send("Page.enable")
            await self.send("DOM.enable")
            await self.send("Runtime.enable")
            await self.send("Network.enable")
            
            print(f"Connected to CDP at {self.ws_url}")
            return True
            
        except Exception as e:
            print(f"CDP connect error: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from CDP."""
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        
        if self.ws:
            await self.ws.close()
            self.ws = None
    
    async def send(self, method: str, params: Dict[str, Any] = None) -> CDPResponse:
        """
        Send CDP command and wait for response.
        
        Args:
            method: CDP method (e.g., "Page.navigate")
            params: Method parameters
        """
        if not self.ws:
            return CDPResponse(id=-1, error={"message": "Not connected"})
        
        self.command_id += 1
        cmd_id = self.command_id
        
        message = {
            "id": cmd_id,
            "method": method,
            "params": params or {}
        }
        
        # Create future for response
        future = asyncio.get_event_loop().create_future()
        self.pending_commands[cmd_id] = future
        
        # Send command
        await self.ws.send(json.dumps(message))
        
        # Wait for response
        try:
            response = await asyncio.wait_for(future, timeout=30)
            return response
        except asyncio.TimeoutError:
            del self.pending_commands[cmd_id]
            return CDPResponse(id=cmd_id, error={"message": "Timeout"})
    
    async def _listen(self):
        """Listen for CDP messages."""
        try:
            async for message in self.ws:
                data = json.loads(message)
                
                if "id" in data:
                    # Response to command
                    cmd_id = data["id"]
                    if cmd_id in self.pending_commands:
                        future = self.pending_commands.pop(cmd_id)
                        response = CDPResponse(
                            id=cmd_id,
                            result=data.get("result"),
                            error=data.get("error")
                        )
                        future.set_result(response)
                
                elif "method" in data:
                    # Event
                    method = data["method"]
                    if method in self.event_handlers:
                        for handler in self.event_handlers[method]:
                            try:
                                await handler(data.get("params", {}))
                            except Exception as e:
                                print(f"Event handler error: {e}")
                                
        except websockets.ConnectionClosed:
            print("CDP connection closed")
        except Exception as e:
            print(f"CDP listener error: {e}")
    
    def on(self, event: str, handler: Callable):
        """Register event handler."""
        if event not in self.event_handlers:
            self.event_handlers[event] = []
        self.event_handlers[event].append(handler)
    
    # ==================== HIGH-LEVEL COMMANDS ====================
    
    async def navigate(self, url: str) -> bool:
        """Navigate to URL."""
        resp = await self.send("Page.navigate", {"url": url})
        if resp.success:
            # Wait for load
            await self.wait_for_load()
        return resp.success
    
    async def wait_for_load(self, timeout: float = 30):
        """Wait for page load complete."""
        await self.send("Page.setLifecycleEventsEnabled", {"enabled": True})
        
        load_event = asyncio.Event()
        
        async def on_lifecycle(params):
            if params.get("name") == "load":
                load_event.set()
        
        self.on("Page.lifecycleEvent", on_lifecycle)
        
        try:
            await asyncio.wait_for(load_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            pass
    
    async def wait(self, seconds: float):
        """Wait for specified seconds."""
        await asyncio.sleep(seconds)
    
    async def evaluate(self, expression: str) -> Any:
        """Execute JavaScript and return result."""
        resp = await self.send("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": True
        })
        if resp.success and resp.result:
            result = resp.result.get("result", {})
            return result.get("value")
        return None
    
    async def query_selector(self, selector: str) -> Optional[int]:
        """Find element by CSS selector, return nodeId."""
        # Get document
        doc_resp = await self.send("DOM.getDocument")
        if not doc_resp.success:
            return None
        
        root_id = doc_resp.result["root"]["nodeId"]
        
        # Query selector
        resp = await self.send("DOM.querySelector", {
            "nodeId": root_id,
            "selector": selector
        })
        
        if resp.success and resp.result:
            node_id = resp.result.get("nodeId", 0)
            return node_id if node_id > 0 else None
        return None
    
    async def query_selector_all(self, selector: str) -> List[int]:
        """Find all elements by CSS selector."""
        doc_resp = await self.send("DOM.getDocument")
        if not doc_resp.success:
            return []
        
        root_id = doc_resp.result["root"]["nodeId"]
        
        resp = await self.send("DOM.querySelectorAll", {
            "nodeId": root_id,
            "selector": selector
        })
        
        if resp.success and resp.result:
            return resp.result.get("nodeIds", [])
        return []
    
    async def wait_for_selector(self, selector: str, timeout: float = 10) -> Optional[int]:
        """Wait for element to appear."""
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < timeout:
            node_id = await self.query_selector(selector)
            if node_id:
                return node_id
            await asyncio.sleep(0.5)
        return None
    
    async def get_box_model(self, node_id: int) -> Optional[Dict]:
        """Get element box model for clicking."""
        resp = await self.send("DOM.getBoxModel", {"nodeId": node_id})
        if resp.success and resp.result:
            return resp.result.get("model")
        return None
    
    async def click(self, selector: str) -> bool:
        """Click element by selector."""
        node_id = await self.wait_for_selector(selector, timeout=5)
        if not node_id:
            print(f"Element not found: {selector}")
            return False
        
        # Get element position
        box = await self.get_box_model(node_id)
        if not box:
            # Try JavaScript click
            await self.evaluate(f'document.querySelector("{selector}").click()')
            return True
        
        # Calculate center point
        content = box.get("content", [])
        if len(content) >= 4:
            x = (content[0] + content[2]) / 2
            y = (content[1] + content[5]) / 2
        else:
            return False
        
        # Mouse events
        await self.send("Input.dispatchMouseEvent", {
            "type": "mousePressed",
            "x": x, "y": y,
            "button": "left",
            "clickCount": 1
        })
        await self.send("Input.dispatchMouseEvent", {
            "type": "mouseReleased",
            "x": x, "y": y,
            "button": "left",
            "clickCount": 1
        })
        
        return True
    
    async def type_text(self, text: str, delay: float = 0.05):
        """Type text character by character."""
        for char in text:
            await self.send("Input.dispatchKeyEvent", {
                "type": "keyDown",
                "text": char
            })
            await self.send("Input.dispatchKeyEvent", {
                "type": "keyUp",
                "text": char
            })
            await asyncio.sleep(delay)
    
    async def type_into(self, selector: str, text: str) -> bool:
        """Click element and type text."""
        if not await self.click(selector):
            return False
        await asyncio.sleep(0.2)
        await self.type_text(text)
        return True
    
    async def press_key(self, key: str):
        """Press special key (Enter, Tab, Escape, etc.)."""
        key_codes = {
            "Enter": 13, "Tab": 9, "Escape": 27,
            "Backspace": 8, "Delete": 46,
            "ArrowUp": 38, "ArrowDown": 40,
            "ArrowLeft": 37, "ArrowRight": 39
        }
        
        await self.send("Input.dispatchKeyEvent", {
            "type": "keyDown",
            "key": key,
            "code": key,
            "windowsVirtualKeyCode": key_codes.get(key, 0)
        })
        await self.send("Input.dispatchKeyEvent", {
            "type": "keyUp",
            "key": key,
            "code": key
        })
    
    async def scroll(self, x: int = 0, y: int = 300):
        """Scroll page."""
        await self.evaluate(f"window.scrollBy({x}, {y})")
    
    async def scroll_to_element(self, selector: str) -> bool:
        """Scroll element into view."""
        result = await self.evaluate(f'''
            (function() {{
                const el = document.querySelector("{selector}");
                if (el) {{
                    el.scrollIntoView({{behavior: "smooth", block: "center"}});
                    return true;
                }}
                return false;
            }})()
        ''')
        return result == True
    
    async def upload_file(self, selector: str, file_path: str) -> bool:
        """Upload file to input element."""
        node_id = await self.wait_for_selector(selector)
        if not node_id:
            return False
        
        abs_path = os.path.abspath(file_path)
        resp = await self.send("DOM.setFileInputFiles", {
            "nodeId": node_id,
            "files": [abs_path]
        })
        return resp.success
    
    async def get_text(self, selector: str) -> Optional[str]:
        """Get text content of element."""
        return await self.evaluate(f'''
            (function() {{
                const el = document.querySelector("{selector}");
                return el ? el.textContent : null;
            }})()
        ''')
    
    async def get_attribute(self, selector: str, attr: str) -> Optional[str]:
        """Get attribute value of element."""
        return await self.evaluate(f'''
            (function() {{
                const el = document.querySelector("{selector}");
                return el ? el.getAttribute("{attr}") : null;
            }})()
        ''')
    
    async def exists(self, selector: str) -> bool:
        """Check if element exists."""
        result = await self.evaluate(f'document.querySelector("{selector}") !== null')
        return result == True
    
    async def screenshot(self, path: str = None) -> Optional[bytes]:
        """Take screenshot."""
        resp = await self.send("Page.captureScreenshot", {"format": "png"})
        if resp.success and resp.result:
            data = base64.b64decode(resp.result["data"])
            if path:
                with open(path, "wb") as f:
                    f.write(data)
            return data
        return None
    
    async def get_cookies(self) -> List[Dict]:
        """Get all cookies."""
        resp = await self.send("Network.getAllCookies")
        if resp.success and resp.result:
            return resp.result.get("cookies", [])
        return []
    
    async def set_cookie(self, name: str, value: str, domain: str, **kwargs):
        """Set cookie."""
        await self.send("Network.setCookie", {
            "name": name,
            "value": value,
            "domain": domain,
            **kwargs
        })
