# Trade Opportunities API - Modular Architecture

A production-grade FastAPI service with **LangGraph** multi-agent workflow for AI-powered market analysis and trade opportunity insights for Indian sectors.

## 🏗️ Modular Project Structure

This project follows clean architecture principles with clear separation of concerns:

```
trade-opportunities-api/
├── main.py                    # FastAPI application entry point
├── requirements.txt           # Python dependencies
├── .env                      # Environment variables (GEMINI_API_KEY)
├── README.md                 # This file
│
├── app/                      # FastAPI Application Layer (HTTP Interface & Security)
│   ├── __init__.py
│   ├── models.py            # Pydantic request/response models
│   │
│   ├── api/                 # API Routes
│   │   └── v1/
│   │       └── endpoints.py  # GET /v1/analyze/{sector} route
│   │
│   ├── core/                # Core FastAPI functionality
│   │   ├── config.py         # Environment configuration
│   │   ├── auth.py           # API Key authentication logic
│   │   └── dependencies.py   # Rate limiting dependency
│   │
│   └── services/            # Application services
│       └── in_memory_store.py # In-memory API keys & rate limiter
│
├── analysis_engine/          # LangGraph Core Logic Layer (Business Logic)
│   ├── __init__.py
│   ├── graph_state.py        # Pydantic State model for workflow
│   ├── analysis_graph.py     # Graph construction & compilation
│   │
│   └── nodes/               # Individual graph nodes
│       ├── collector_node.py  # Node A: Data collection
│       ├── analyzer_node.py   # Node B: AI analysis generation
│       ├── critic_node.py     # Node C: Quality validation
│       └── refiner_node.py    # Node D: Report refinement
│
└── external_tools/           # External Service Wrappers (I/O Layer)
    ├── __init__.py
    ├── ai_client.py           # Gemini API wrapper & prompts
    └── data_collector.py      # Web search wrapper (DuckDuckGo)
```

### 🎯 Key Architectural Decisions

| Layer | Responsibility | Benefits |
|-------|---------------|----------|
| **`app/`** | HTTP interface, security, routing | Clean API boundary, testable endpoints |
| **`analysis_engine/`** | Stateful workflow & business logic | Reusable core logic, independent of transport |
| **`external_tools/`** | External API integrations | Easy to swap implementations, mock for testing |

## 🚀 Quick Start

### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your Gemini API key:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
SECRET_KEY=generate_with_openssl_rand_hex_32
```

### 3. Run the Server

```bash
# Development mode
python main.py

# Or with uvicorn directly
uvicorn main:app --reload
```

### 4. Access API

- **API Root**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📡 API Usage

### Authentication

Include API key in header:
```bash
curl "http://localhost:8000/v1/analyze/pharmaceuticals" \
  -H "X-API-Key: demo-key-12345"
```

**Demo API Keys:**
- `demo-key-12345` (user: demo)
- `guest-key-67890` (user: guest)
- `test-key-abcde` (user: test)

**Guest Access** (no authentication):
```bash
curl "http://localhost:8000/v1/analyze/technology"
```

### Analyze a Sector

```bash
# Basic request
curl "http://localhost:8000/v1/analyze/fintech" \
  -H "X-API-Key: demo-key-12345"

# Download as markdown file
curl "http://localhost:8000/v1/analyze/agriculture/download" \
  -H "X-API-Key: demo-key-12345" \
  -o agriculture_report.md

# Check rate limits
curl "http://localhost:8000/v1/rate-limits" \
  -H "X-API-Key: demo-key-12345"
```

## 🔄 LangGraph Workflow

### Multi-Agent Pipeline

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Data      │───▶│   AI         │───▶│   Report    │
│   Collector │    │   Analyzer   │    │   Critic    │
└─────────────┘    └──────────────┘    └──────┬──────┘
                                              │
                                         PASS │ FAIL
                                              │
                                              ▼
                                        ┌─────────────┐
                                        │   Report    │
                                        │   Refiner   │
                                        └──────┬──────┘
                                              │
                                              └──▶ Loop (max 2x)
```

### Workflow Steps

1. **Node A (Collector)**: Searches DuckDuckGo for market data
2. **Node B (Analyzer)**: Generates comprehensive report with Gemini Pro
3. **Node C (Critic)**: Validates quality (completeness, trade focus, actionability)
4. **Node D (Refiner)**: Addresses feedback if FAIL (up to 2 iterations)
5. **Self-Correction**: Loops until PASS or max iterations reached

### Quality Criteria

Every report is validated against:
- ✅ Completeness (all sections present)
- ✅ Trade Focus (clear opportunities)
- ✅ Actionability (specific recommendations)
- ✅ Data-Driven (numbers & trends)
- ✅ Professional Structure
- ✅ Business Value

## 📊 Report Structure

Each analysis includes:

- **Executive Summary**: 3-4 sentence overview
- **Market Overview**: Size, growth, key players, developments
- **Trade Opportunities**: Export/Import/Domestic opportunities
- **Sector Analysis**: Strengths, challenges, emerging trends
- **Investment Considerations**: Capital, risks, ROI, timeframes
- **Regulatory Framework**: Compliance, policies, procedures
- **Actionable Recommendations**: 5-7 specific steps
- **Market Outlook**: 12-24 month projections

## 🔒 Security Features

### Authentication & Authorization

**API Key Authentication** (`app/core/auth.py`)
- Header-based authentication via `X-API-Key`
- Guest access fallback (no authentication required)
- User identification for rate limiting and tracking
- Non-blocking error handling with clear error messages

**Implementation:**
```python
# Automatic verification on protected endpoints
@router.get("/v1/analyze/{sector}")
async def analyze_sector(
    sector: str,
    current_user: User = Depends(get_current_user)  # Auto-verifies API key
)
```

**Demo API Keys:**
- `demo-key-12345` (user: demo)
- `guest-key-67890` (user: guest)
- `test-key-abcde` (user: test)

### Rate Limiting

**Intelligent Rate Limiter** (`app/services/in_memory_store.py`)
- **5 requests per minute** (per user/API key)
- **30 requests per hour** (per user/API key)
- In-memory sliding window tracking
- Automatic cleanup of expired entries
- Per-user isolation

**Features:**
- Returns remaining quota in response headers
- Clear error messages on limit exceeded
- Resets automatically without manual intervention

### Input Validation

**Pydantic Models** (`app/models.py`)
- Type-safe request/response schemas
- Automatic validation of all inputs
- Sanitization of sector names
- Prevention of injection attacks

### Error Handling

**Structured Error Responses:**
- `400 Bad Request`: Invalid parameters
- `401 Unauthorized`: Invalid/missing API key
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: System errors with stack traces in logs

### Security Best Practices

✅ **Environment Variables**: Sensitive data in `.env` (never committed)
✅ **API Key Storage**: In-memory store (easily upgradeable to encrypted DB)
✅ **CORS Configuration**: Configurable origins in `main.py`
✅ **Input Sanitization**: All user inputs validated and cleaned
✅ **Error Masking**: Internal errors don't leak implementation details
✅ **Dependency Pinning**: `requirements.txt` with exact versions

### Generate New API Key

```bash
curl -X POST "http://localhost:8000/v1/api-keys?user_id=myuser"
```

## 🧪 Testing

### Test Individual Nodes

```python
from analysis_engine.nodes.collector_node import collector_node

state = {"sector": "fintech", "country": "India", "iterations": 0}
result = collector_node(state)
print(result['raw_data'])
```

### Test Full Workflow

```python
from analysis_engine.analysis_graph import execute_analysis

final_state = execute_analysis("pharmaceuticals", "India")
print(final_state['markdown_report'])
print(f"Iterations: {final_state['iterations']}")
```

### Test API Endpoint

```bash
# Health check
curl http://localhost:8000/health

# Analysis
curl "http://localhost:8000/v1/analyze/technology" \
  -H "X-API-Key: demo-key-12345"

# Rate limits
curl "http://localhost:8000/v1/rate-limits" \
  -H "X-API-Key: demo-key-12345"
```

## 📈 Performance

| Scenario | Refinements | Duration |
|----------|------------|----------|
| High-quality first draft | 0 | 30-45s |
| One refinement cycle | 1 | 60-90s |
| Two refinement cycles | 2 | 90-120s |

**API Calls per Request:**
- Minimum: 3 Gemini API calls
- Maximum: 7 Gemini API calls

## 🛠️ Development

### Add New Node

```python
# 1. Create node file in analysis_engine/nodes/
def my_node(state: AnalysisState) -> AnalysisState:
    # Node logic
    return state

# 2. Add to analysis_graph.py
workflow.add_node("my_node", my_node)
workflow.add_edge("previous_node", "my_node")
```

### Modify Prompts

Edit prompts in `external_tools/ai_client.py`:
- `_build_analysis_prompt()`: Initial generation
- `_build_critique_prompt()`: Quality validation
- `_build_refinement_prompt()`: Improvement instructions

### Change Data Source

Replace DuckDuckGo in `external_tools/data_collector.py`:
```python
class DataCollector:
    def collect_sector_data(self, sector, country):
        # Your custom data source here
        pass
```

## 📚 API Documentation

### Interactive Documentation

**Swagger UI** (Recommended): http://localhost:8000/docs
- Try endpoints directly in browser
- Auto-generated from code
- Request/response schemas
- Authentication testing

**ReDoc**: http://localhost:8000/redoc
- Clean, readable format
- Downloadable OpenAPI spec
- Printable documentation

### Available Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | Service information and endpoint list | No |
| GET | `/health` | Health check with timestamp | No |
| GET | `/v1/analyze/{sector}` | Generate sector analysis report | Optional |
| GET | `/v1/analyze/{sector}/download` | Download report as `.md` file | Optional |
| GET | `/v1/rate-limits` | Check current rate limit status | Yes |
| POST | `/v1/api-keys` | Generate new API key | No |

### Response Schemas

**StructuredAnalysisResponse:**
```json
{
  "sector": "pharmaceuticals",
  "country": "India",
  "markdown_report": "# Report content...",
  "json_summary": {
    "market_size": "USD 50 billion",
    "growth_cagr": "12% CAGR (2024-2028)",
    "top_recommendations": ["...", "...", "..."]
  },
  "data_summary": {
    "sources_count": 8,
    "data_quality": "high",
    "articles": [...]
  },
  "timestamp": "2025-12-16T19:00:00Z",
  "refinement_iterations": 1
}
```

### Error Responses

**401 Unauthorized:**
```json
{
  "detail": "Invalid or expired API key"
}
```

**429 Too Many Requests:**
```json
{
  "detail": "Rate limit exceeded. Try again in 45 seconds."
}
```

### Code Examples

**Python Client:**
```python
import requests

response = requests.get(
    "http://localhost:8000/v1/analyze/fintech",
    headers={"X-API-Key": "demo-key-12345"}
)

data = response.json()
print(data['markdown_report'])
```

**JavaScript/Node.js:**
```javascript
const response = await fetch('http://localhost:8000/v1/analyze/fintech', {
  headers: { 'X-API-Key': 'demo-key-12345' }
});

const data = await response.json();
console.log(data.markdown_report);
```

**cURL:**
```bash
curl "http://localhost:8000/v1/analyze/fintech" \
  -H "X-API-Key: demo-key-12345" \
  | jq '.markdown_report'
```

## 🔮 Roadmap

- [ ] Database persistence (PostgreSQL/MongoDB)
- [ ] WebSocket streaming progress updates
- [ ] Multi-language support
- [ ] PDF report generation
- [ ] Email delivery
- [ ] Advanced caching layer
- [ ] Sector comparison analysis
- [ ] Historical trend analysis

## 🤝 Contributing

This is a reference implementation demonstrating:
- ✅ Clean architecture with separation of concerns
- ✅ LangGraph multi-agent workflows
- ✅ Self-correcting AI systems
- ✅ Production-ready error handling
- ✅ Comprehensive logging and observability

## 📝 License

MIT License - Feel free to use this as a reference for your projects.

---

**Built with FastAPI 🚀 • Google Gemini Pro 🤖 • LangGraph 🔄**

*Enterprise-grade AI system architecture with self-correction and quality assurance*
