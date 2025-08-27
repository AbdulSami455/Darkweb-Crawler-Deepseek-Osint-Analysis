from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List
import json
import os
import uvicorn

from .analysis import OnionScrapAnalyzer
from .ahmia_search import AhmiaSearchAnalyzer


class AnalyzeRequest(BaseModel):
    url: str = Field(..., description="Onion or clearnet URL to analyze")
    depth: int = Field(1, ge=0, le=3, description="Crawl depth for TorCrawl")
    prompt: Optional[str] = Field(None, description="Custom analysis prompt override")
    model: Optional[str] = Field(None, description="OpenRouter model to use (e.g., 'deepseek/deepseek-r1:free', 'anthropic/claude-3.5-sonnet:free')")
    use_langchain: bool = Field(False, description="Use LangChain structured analysis instead of traditional JSON")


class AnalyzeResponse(BaseModel):
    success: bool
    analysis: Optional[Any] = None
    model: Optional[str] = None
    tokens_used: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    details: Optional[str] = None


class BulkSearchRequest(BaseModel):
    query: str = Field(..., description="Search term for Ahmia")
    max_sites: int = Field(5, ge=1, le=20, description="Maximum number of sites to analyze")
    depth: int = Field(1, ge=0, le=3, description="Crawl depth for TorCrawl")
    prompt: Optional[str] = Field(None, description="Custom analysis prompt override")
    model: Optional[str] = Field(None, description="OpenRouter model to use (e.g., 'deepseek/deepseek-r1:free', 'anthropic/claude-3.5-sonnet:free')")
    use_langchain: bool = Field(False, description="Use LangChain structured analysis instead of traditional JSON")
    days: Optional[int] = Field(None, ge=1, le=30, description="Number of days to search back (1, 7, 30)")


class BulkSearchResponse(BaseModel):
    success: bool
    query: str
    search_results_count: int
    successful_analyses: int
    failed_analyses: int
    results: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    error: Optional[str] = None


app = FastAPI(title="Darkweb Crawler API", version="1.0.0")


@app.get("/healthz")
def healthz() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    analyzer = OnionScrapAnalyzer(model=req.model)
    result = analyzer.run_full_analysis(
        url=req.url,
        depth=req.depth,
        custom_prompt=req.prompt,
        use_langchain=req.use_langchain,
        model=req.model,
    )
    # Best-effort: parse analysis string into JSON if possible
    analysis_value: Any = result.get("analysis")
    if isinstance(analysis_value, str):
        text = analysis_value.strip()
        # strip code fences if present
        if text.startswith("```") and text.endswith("```"):
            text = text.strip("`")
        try:
            analysis_value = json.loads(text)
            result["analysis"] = analysis_value
        except Exception:
            pass
    return AnalyzeResponse(**result)  # type: ignore[arg-type]


@app.post("/bulk-search", response_model=BulkSearchResponse)
def bulk_search(req: BulkSearchRequest) -> BulkSearchResponse:
    """
    Search Ahmia for onion sites and analyze each one using TorCrawl
    """
    try:
        analyzer = AhmiaSearchAnalyzer()
        result = analyzer.bulk_search_and_analyze(
            query=req.query,
            max_sites=req.max_sites,
            depth=req.depth,
            custom_prompt=req.prompt,
            model=req.model,
            use_langchain=req.use_langchain,
            days=req.days
        )
        
        if result.get("success"):
            return BulkSearchResponse(**result)
        else:
            return BulkSearchResponse(
                success=False,
                query=req.query,
                search_results_count=0,
                successful_analyses=0,
                failed_analyses=0,
                results=[],
                metadata=result.get("metadata", {}),
                error=result.get("error", "Unknown error")
            )
            
    except Exception as e:
        return BulkSearchResponse(
            success=False,
            query=req.query,
            search_results_count=0,
            successful_analyses=0,
            failed_analyses=0,
            results=[],
            metadata={"error": str(e)},
            error=f"Exception occurred: {str(e)}"
        )


def main() -> None:
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
    )


