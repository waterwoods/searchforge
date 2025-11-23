# Mortgage Programs MCP Server

A minimal Model Context Protocol (MCP) server that provides mortgage program search functionality. This server exposes a single tool `search_mortgage_programs` to help users find mortgage programs and assistance based on their location, profile, and financial criteria.

## What This Server Does

This MCP server searches through a local database of mortgage programs (stored in `mortgage_programs.json`) and returns programs that match the user's criteria, including:

- **Location-based matching**: Programs available in specific states or ZIP code prefixes
- **Profile-based matching**: Programs for first-time buyers, veterans, low-income families, seniors, etc.
- **Financial criteria**: Programs that accommodate specific debt-to-income (DTI) ratios

The server returns up to 5 matching programs, sorted by relevance (tag matches and DTI margin).

## Installation

1. **Create a virtual environment** (recommended):

```bash
cd /home/andy/searchforge/mcp/mortgage_programs_server
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:

```bash
pip install -r requirements.txt
```

## Running the Server

The MCP server uses stdio (standard input/output) for communication, which is the standard way MCP servers communicate with clients.

To start the server:

```bash
python server.py
```

The server will wait for JSON-RPC messages on stdin and respond on stdout. This is typically used with MCP clients or tools like the MCP Inspector.

## Running the Smoke Test

To verify the server works correctly without a full MCP client setup, run the smoke test:

```bash
python smoke_test.py
```

The smoke test will:
1. Call `search_mortgage_programs` with test parameters:
   - ZIP code: `90803`
   - State: `CA`
   - Profile tags: `["first_time_buyer"]`
   - Current DTI: `57%`
2. Display the matching programs with their details
3. Run additional test cases for different scenarios

Expected output: The test should find 1-3 matching programs and display their details including:
- Program ID and name
- Description
- Benefit summary
- Why it's relevant to the user

## Tool: `search_mortgage_programs`

### Parameters

- `zip_code` (required): ZIP code of the property location (e.g., "90803")
- `state` (optional): State code (e.g., "CA", "TX")
- `profile_tags` (optional): Array of profile tags such as:
  - `"first_time_buyer"`
  - `"veteran"`
  - `"low_income"`
  - `"high_dti"`
  - `"senior_60_plus"`
- `current_dti` (optional): Current debt-to-income ratio (0.0 to 1.0, e.g., 0.57 for 57%)

### Return Format

Returns an array of program objects, each containing:
- `id`: Program identifier
- `name`: Program name
- `description`: Detailed description
- `benefit_summary`: Summary of benefits
- `why_relevant`: Explanation of why this program matches the user's criteria

### Matching Logic

1. **Location**: Program must match either the specified state OR the ZIP code prefix
2. **Profile Tags**: Programs with matching tags are prioritized
3. **DTI Filter**: If `current_dti` is provided, only programs with `max_dti >= current_dti` are returned
4. **Sorting**: Results are sorted by:
   - Tag match count (descending)
   - DTI margin (max_dti - current_dti, descending)
5. **Limit**: Maximum 5 results returned

## Data Source

Programs are stored in `mortgage_programs.json` with 8 sample programs covering:
- VA Loans (veterans)
- First-time homebuyer assistance (CA, TX, WA)
- State down payment assistance
- Low-income programs
- High DTI accommodation programs
- Senior (60+) programs

## Future Integration with LangGraph

This MCP server is designed to be integrated into the LangGraph mortgage agent workflow as an `external_programs_node`. The integration will:

1. **Call Context**: The node will be invoked in the `tight/high_risk` branch when the system determines that external mortgage programs might help the user qualify for a loan.

2. **Input Mapping**: The node will extract relevant information from the conversation context:
   - Property location (ZIP code, state)
   - User profile (first-time buyer, veteran status, etc.)
   - Current financial metrics (DTI ratio)

3. **Output Integration**: The returned programs will be formatted and included in the agent's response to help the user understand available assistance options.

4. **Implementation Pattern**:
   ```python
   async def external_programs_node(state: MortgageState) -> MortgageState:
       # Extract context from state
       zip_code = state.property_info.get("zip_code")
       profile_tags = extract_profile_tags(state.conversation_history)
       current_dti = state.financial_info.get("dti_ratio")
       
       # Call MCP server tool
       programs = await mcp_client.call_tool(
           "search_mortgage_programs",
           {
               "zip_code": zip_code,
               "state": state.property_info.get("state"),
               "profile_tags": profile_tags,
               "current_dti": current_dti
           }
       )
       
       # Add to state
       state.external_programs = programs
       return state
   ```

## Project Structure

```
mcp/mortgage_programs_server/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── server.py                 # MCP server implementation
├── smoke_test.py            # Smoke test script
└── mortgage_programs.json    # Sample mortgage programs data
```

## Notes

- This is a **standalone subproject** that does not modify any existing mortgage service code
- The server is completely self-contained with its own dependencies
- All data is currently stored in a local JSON file (can be replaced with a database later)
- The server follows the standard MCP protocol for tool exposure

