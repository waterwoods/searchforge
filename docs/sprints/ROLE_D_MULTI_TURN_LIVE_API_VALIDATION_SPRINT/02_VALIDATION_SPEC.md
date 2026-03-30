# Validation spec

## Cases

| ID  | Template        | Custom note (verbatim) | Difficulty |
| --- | --------------- | ---------------------- | ---------- |
| D1  | 价格敏感型       | 价格敏感型，同时又想获得最好的deal | 刁钻 (`tough`) |
| D2  | 老年客户型       | 我是年纪大一点的客户，容易打错字，也会改口 | 刁钻 (`tough`) |
| D3  | 家庭车辆型       | 我太太那台车也想加，我们平时都开，而且我习惯先把材料发过去 | 真实 (`realistic`) |

Turn text is produced by `buildRoleDScenario()` in `ui/src/components/simulation/roleDReplay.ts` (same as UI).

## API contract (must match UI)

- **URL:** `POST /api/inbox/triage`  
- **Fields:** `text`, `persist_case: false`, `soft_route: "add_car"`, `session_id` (stable per run), `client_id: "chen_kui"`, optional `conversation_turns` (prior customer + system messages).  

## Checks per case

1. Each turn returns HTTP 200 and a JSON body that **differs** from prior turn in at least one of: `collected_fields`, `still_needed_fields`, `handoff_ready`, `client_reply_draft`, `triage_path`.  
2. `collection_stage` / `handoff_ready` progression is plausible.  
3. `still_needed_fields` shrinks or stays justified after handoff.  
4. Note simulation vs portal: **AddCarFlowExplanation** not mounted on simulation tab.  

## Evidence method (2026-03-29 run)

- Backend: `uvicorn services.fiqa_api.app_main:app --port 8001`  
- Client: `httpx` multi-turn script mirroring UI payload shape  
