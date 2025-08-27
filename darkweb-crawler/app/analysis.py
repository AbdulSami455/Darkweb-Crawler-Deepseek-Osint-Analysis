#!/usr/bin/env python3
"""
Non-interactive analyzer that vendors TorCrawl and calls OpenRouter DeepSeek
to produce structured JSON analysis for a provided URL (including .onion).
Supports both traditional JSON analysis and LangChain structured data extraction.
"""

import os
import json
import time
import socket
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Any

import requests
import sys

try:
    from .langchain_analysis import LangChainAnalyzer
    from .models import DarkWebAnalysis
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

DEFAULT_MODEL = "deepseek/deepseek-r1:free"

POPULAR_MODELS = {
    "deepseek": "deepseek/deepseek-r1:free",
    "claude": "anthropic/claude-3.5-sonnet:free", 
    "gpt": "openai/gpt-3.5-turbo:free",
    "llama": "meta-llama/llama-3.1-8b-instruct:free",
    "gemini": "google/gemini-flash-1.5:free",
    "gpt4": "openai/gpt-4:free",
    "claude3": "anthropic/claude-3-haiku:free",
}


def _get_torcrawl_path() -> Path:
    return (Path(__file__).resolve().parent.parent / "torcrawl" / "torcrawl.py").resolve()


class OnionScrapAnalyzer:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = model or os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL)
        self.headers = {
            "Authorization": f"Bearer {self.api_key}" if self.api_key else "",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/GENAI-RAG",
            "X-Title": "OnionScrap-API",
        }

    def _is_tor_listening(self, host: str = None, port: int = None, timeout_s: float = 1.5) -> bool:
        # Use environment variables if not provided
        host = host or os.getenv("TOR_SOCKS_HOST", "127.0.0.1")
        port = port or int(os.getenv("TOR_SOCKS_PORT", "9050"))
        
        try:
            with socket.create_connection((host, port), timeout_s):
                return True
        except OSError:
            return False

    def test_connectivity_through_tor(self, url: str) -> Tuple[bool, Optional[int], str, str]:
        # Always require Tor to be running and reachable, and validate connectivity via SOCKS5
        tor_host = os.getenv("TOR_SOCKS_HOST", "127.0.0.1")
        tor_port = os.getenv("TOR_SOCKS_PORT", "9050")
        
        if not self._is_tor_listening():
            return False, None, "", f"Tor SOCKS5 {tor_host}:{tor_port} is not listening"
        try:
            result = subprocess.run(
                [
                    "curl", "--socks5", f"{tor_host}:{tor_port}", "--socks5-hostname", f"{tor_host}:{tor_port}",
                    "--connect-timeout", "20", "--max-time", "40", "-s", "-o", "/dev/null", "-w", "%{http_code}", url,
                ],
                capture_output=True,
                text=True,
                timeout=45,
            )
            if result.returncode == 0 and result.stdout.strip().isdigit():
                status_code = int(result.stdout.strip())
                ok = status_code >= 100 and status_code < 600 
                return ok, status_code, result.stdout, result.stderr
            else:
                error_msg = f"Curl failed with return code {result.returncode}, stdout: {result.stdout}, stderr: {result.stderr}"
                return False, None, result.stdout, result.stderr
        except Exception as exc:
            return False, None, "", str(exc)

    def _normalize_onion_url(self, url: str) -> str:
        if ".onion" in url:
            if not url.startswith(("http://", "https://")):
                return "http://" + url
            if url.startswith("https://"):
                return url.replace("https://", "http://", 1)
        return url

    def _test_model_availability(self, model: str) -> bool:
        """Test if a specific model is available."""
        if not self.api_key:
            # If no API key, assume model is available (for testing)
            return True
            
        try:
            # Simple test request to check model availability
            test_payload = {
                "model": model,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10,
            }
            
            response = requests.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers=self.headers,
                json=test_payload,
                timeout=10,
            )
            
            # If we get a 200, model is available
            if response.status_code == 200:
                return True
            # If we get 429 (rate limit), model is available but rate limited
            elif response.status_code == 429:
                print(f"[OnionScrap] Warning: Model {model} is rate limited")
                return False
            # Other errors might indicate model is available but request was malformed
            else:
                print(f"[OnionScrap] Warning: Model {model} returned status {response.status_code}")
                return True
                
        except Exception as exc:
            print(f"[OnionScrap] Error testing model {model}: {exc}")
            return False

    def get_available_models(self) -> List[str]:
        """Get list of available models from OpenRouter."""
        if not self.api_key:
            return list(POPULAR_MODELS.values())
            
        try:
            response = requests.get(
                f"{OPENROUTER_BASE_URL}/models",
                headers=self.headers,
                timeout=10,
            )
            
            if response.status_code == 200:
                models_data = response.json()
                return [model["id"] for model in models_data.get("data", [])]
            else:
                print(f"[OnionScrap] Error fetching models: {response.status_code}")
                return list(POPULAR_MODELS.values())
                
        except Exception as exc:
            print(f"[OnionScrap] Error fetching available models: {exc}")
            return list(POPULAR_MODELS.values())

    def run_torcrawl(
        self,
        url: str,
        depth: int = 1,
        extract: bool = True,
        verbose: bool = False,
        proxy_host: str = None,
        proxy_port: int = None,
    ) -> Tuple[Optional[str], Optional[str], str, str, List[str]]:
        """
        Execute vendored torcrawl.py and capture its output.
        Returns: (content, output_folder, raw_stdout)
        """
        normalized_url = self._normalize_onion_url(url)
        torcrawl_path = _get_torcrawl_path()
        torcrawl_dir = torcrawl_path.parent

        # Use environment variables for proxy settings
        proxy_host = proxy_host or os.getenv("TOR_SOCKS_HOST", "127.0.0.1")
        proxy_port = proxy_port or int(os.getenv("TOR_SOCKS_PORT", "9050"))

        # Use sys.executable to ensure we use the same Python interpreter
        python_executable = sys.executable
        
        cmd = [
            python_executable, str(torcrawl_path),
            "-u", normalized_url,
            "-d", str(depth),
            "-pr", str(proxy_port),
            "-px", proxy_host,
        ]
        if extract:
            cmd.append("-e")
        if verbose:
            cmd.append("-v")

        # Use relative script path; working directory is torcrawl_dir
        debug_cmd = [
            python_executable, "torcrawl.py",
            "-u", normalized_url,
            "-d", str(depth),
            "-pr", str(proxy_port),  # SOCKS proxy port
            "-px", proxy_host,       # SOCKS proxy host
        ] + (["-e"] if extract else []) + (["-v"] if verbose else [])

        # Always write to file to avoid stdout decoding issues; read back later
        output_filename = "result.htm"
        debug_cmd += ["-o", output_filename]

        print(f"[OnionScrap] Step: Running TorCrawl (depth={depth})")
        print(f"[OnionScrap] Command: {' '.join(debug_cmd)}")
        print(f"[OnionScrap] Working directory: {torcrawl_dir}")
        
        # Set up environment with proper Python path
        env = os.environ.copy()
        env['PYTHONPATH'] = str(torcrawl_dir) + ':' + env.get('PYTHONPATH', '')
        
        try:
            result = subprocess.run(
                debug_cmd,
                capture_output=True,
                text=True,
                cwd=str(torcrawl_dir),
                timeout=180,
                env=env  # Pass environment with proper Python path
            )
        except subprocess.TimeoutExpired as exc:
            print(f"[OnionScrap] TorCrawl timeout: {exc}")
            return None, None, "", f"Timeout running torcrawl: {exc}", ["timeout"]
        except Exception as exc:
            print(f"[OnionScrap] Error starting TorCrawl: {exc}")
            return None, None, "", f"Error starting torcrawl: {exc}", ["exception"]

        print(f"[OnionScrap] TorCrawl return code: {result.returncode}")
        print(f"[OnionScrap] TorCrawl stdout: {result.stdout[:200]}...")
        print(f"[OnionScrap] TorCrawl stderr: {result.stderr[:200]}...")

        if result.returncode != 0:
            print("[OnionScrap] TorCrawl returned non-zero exit code")
            return None, None, result.stdout, result.stderr or result.stdout, ["nonzero_returncode"]

        # Calculate potential output folder used by torcrawl
        domain = normalized_url.replace("http://", "").replace("https://", "")
        domain = domain.split("/")[0]
        output_folder_path = (torcrawl_dir / "output" / domain).resolve()
        output_folder = str(output_folder_path)

        # Prefer reading written file content
        file_path = output_folder_path / output_filename
        content = None
        if file_path.exists():
            try:
                # Read bytes and decode leniently to avoid failures
                raw = file_path.read_bytes()
                try:
                    content = raw.decode("utf-8", errors="replace")
                except Exception:
                    content = raw.decode("latin-1", errors="replace")
            except Exception as exc:
                print(f"[OnionScrap] Error reading TorCrawl output file: {exc}")
                content = None

        # Fallback to raw stdout if no file content
        if not content and result.stdout:
            content = result.stdout

        return content or None, output_folder, result.stdout, result.stderr, debug_cmd

    def analyze_with_deepseek(self, content: str, analysis_prompt: Optional[str] = None, model: Optional[str] = None) -> Dict:
        """Traditional JSON analysis using direct API calls with specified model."""
        if not self.api_key:
            return {"success": False, "error": "Missing OPENROUTER_API_KEY"}

        # Use specified model or default
        selected_model = model or self.model
        print(f"[OnionScrap] Using model: {selected_model}")

        if not analysis_prompt:
            analysis_prompt = (
                """Analyze the following dark-web content captured from a .onion page and return ONLY JSON\n"""
                """that matches the schema provided below.\n\n"""
                """Tasks:\n"""
                """1) Content Summary — What this page is about (plain, factual).\n"""
                """2) Key Information — Extract concrete details: names/aliases, contact methods \n"""
                """   (e.g., Telegram/Jabber/Tox/Email), URLs (.onion/.clearnet), PGP keys/fingerprints, \n"""
                """   crypto wallets (BTC/ETH/XMR/etc.), product/service listings, prices/currencies, \n"""
                """   dates/timestamps, target industries/regions, and any claims of affiliation or reputation.\n"""
                """3) Security Assessment — Note indicators of malware/phishing/scams, escrow claims, \n"""
                """   operational security practices, external links/downloads, and any signs of LE impersonation.\n"""
                """4) Categories — Classify page type using this set (choose one or more):\n"""
                """   [\"marketplace\",\"vendor_shop\",\"forum\",\"leak_site\",\"ransomware_blog\",\"carding\",\"fraud_service\",\n"""
                """    \"malware_service\",\"hosting\",\"mixing_laundry\",\"search_index\",\"news\",\"phishing\",\"scam\",\"other\"]\n"""
                """5) Notable Elements — Anything unusual or high-signal.\n"""
                """6) Recommendations — Safety and handling guidance for analysts.\n"""
                """7) Source Reliability — Rate 1–5 and explain briefly.\n"""
                """8) Confidence — 0–1 with a one-sentence justification.\n"""
                """9) Limitations — Note truncation, language barriers, or low-quality OCR if applicable.\n\n"""
                """Normalization rules:\n"""
                """- Normalize dates to ISO 8601.\n"""
                """- For PGP: include fingerprint (40 hex), key block presence.\n"""
                """- For crypto: include type, address, network/tag.\n"""
                """- For onion links: flag v2 as deprecated.\n"""
                """- If non-English, include a short English summary and detected language.\n"""
            )

        payload = {
            "model": selected_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an OSINT-focused cybersecurity analyst specializing in dark-web (.onion) content. "
                        "Output only the requested JSON fields."
                    ),
                },
                {"role": "user", "content": f"{analysis_prompt}\n\nContent to analyze:\n{content[:4000]}"},
            ],
            "max_tokens": 2000,
            "temperature": 0.3,
        }

        # Simple retry logic for network issues (not model switching)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{OPENROUTER_BASE_URL}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=90,
                )
                
                if response.status_code == 200:
                    result = response.json()
                    analysis = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    return {
                        "success": True,
                        "analysis": analysis,
                        "model": selected_model,
                        "tokens_used": result.get("usage", {}).get("total_tokens", 0),
                    }
                elif response.status_code == 429:
                    return {
                        "success": False,
                        "error": f"Rate limited on model {selected_model}",
                        "details": response.text,
                    }
                else:
                    return {
                        "success": False,
                        "error": f"API Error: {response.status_code}",
                        "details": response.text,
                    }
                    
            except Exception as exc:
                if attempt < max_retries - 1:
                    print(f"[OnionScrap] API call failed on attempt {attempt + 1}: {exc}")
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    return {"success": False, "error": f"API call error after {max_retries} attempts: {exc}"}

        return {"success": False, "error": "All retry attempts failed"}

    def analyze_with_langchain(self, content: str, model: Optional[str] = None) -> Dict:
        """Structured analysis using LangChain and Pydantic models."""
        if not LANGCHAIN_AVAILABLE:
            return {
                "success": False, 
                "error": "LangChain not available. Install langchain, langchain-openai, and langchain-community packages."
            }
        
        if not self.api_key:
            return {"success": False, "error": "Missing OPENROUTER_API_KEY"}

        try:
            langchain_analyzer = LangChainAnalyzer(api_key=self.api_key, model=model)
            result = langchain_analyzer.analyze_content_with_fallback(content, model)
            
            # Add metadata about the analysis method
            if result["success"]:
                result["analysis_method"] = "langchain_structured"
                result["model"] = "deepseek/deepseek-r1-0528:free"
            
            return result
            
        except Exception as exc:
            return {
                "success": False,
                "error": f"LangChain analysis error: {str(exc)}",
                "analysis_method": "langchain_structured"
            }

    def run_full_analysis(
        self,
        url: str,
        depth: int = 1,
        custom_prompt: Optional[str] = None,
        use_langchain: bool = False,
        model: Optional[str] = None,
    ) -> Dict:
        started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Require Tor running and connectivity through Tor for all URLs
        tor_host = os.getenv("TOR_SOCKS_HOST", "127.0.0.1")
        tor_port = os.getenv("TOR_SOCKS_PORT", "9050")
        
        if not self._is_tor_listening():
            print(f"[OnionScrap] Step: Tor check -> NOT LISTENING at {tor_host}:{tor_port}")
            return {
                "success": False,
                "error": f"Tor is not running on {tor_host}:{tor_port}",
                "metadata": {"started_at": started_at},
            }
        print(f"[OnionScrap] Step: Tor check -> OK ({tor_host}:{tor_port})")

        normalized_url = self._normalize_onion_url(url)
        ok, status_code, curl_out, curl_err = self.test_connectivity_through_tor(normalized_url)
        print(f"[OnionScrap] Step: Connectivity test via Tor -> ok={ok} status={status_code}")
        connectivity_warning = None
        if not ok:
            connectivity_warning = f"Connectivity test failed (status={status_code}, curl_out={curl_out}, curl_err={curl_err})"
            print(f"[OnionScrap] Warning: {connectivity_warning}")
            print(f"[OnionScrap] Continuing with TorCrawl anyway - some onion sites fail connectivity tests but are still accessible")

        # Run torcrawl
        content, output_folder, raw_stdout, raw_stderr, cmd = self.run_torcrawl(url=normalized_url, depth=depth)
        print(f"[OnionScrap] Step: TorCrawl finished. stdout_len={len(raw_stdout) if raw_stdout else 0} stderr_len={len(raw_stderr) if raw_stderr else 0}")
        if not content:
            brief_err = ""
            if raw_stderr:
                lines = raw_stderr.strip().splitlines()
                if lines:
                    brief_err = lines[-1][-400:]
            return {
                "success": False,
                "error": "No response from site or scraping failed",
                "details": brief_err or None,
                "torcrawl_stdout": raw_stdout,
                "metadata": {"started_at": started_at, "url": url},
            }

        # AI Analysis
        if use_langchain:
            print(f"[OnionScrap] Step: Using LangChain structured analysis")
            analysis_result = self.analyze_with_langchain(content, model)
        else:
            print(f"[OnionScrap] Step: Using traditional JSON analysis")
            analysis_result = self.analyze_with_deepseek(content, custom_prompt, model)
        
        print(f"[OnionScrap] Step: Analysis -> success={analysis_result.get('success')} tokens={analysis_result.get('tokens_used')}")

        response: Dict[str, Any] = {
            "success": analysis_result.get("success", False),
            "analysis": analysis_result.get("analysis"),
            "model": analysis_result.get("model"),
            "tokens_used": analysis_result.get("tokens_used"),
            "analysis_method": analysis_result.get("analysis_method", "traditional_json"),
            "metadata": {
                "started_at": started_at,
                "url": url,
                "depth": depth,
                "tor_listening": self._is_tor_listening(),
                "use_langchain": use_langchain,
                "connectivity_warning": connectivity_warning,
            },
            "error": analysis_result.get("error"),
            "details": analysis_result.get("details"),
        }
        # Remove internal path details from response
        return response


