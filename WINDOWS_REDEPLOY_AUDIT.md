# Windows Redeploy Audit

Remote host audited:
- `192.168.3.120:2222`
- user: `Roy`

## Present

- `C:\Users\Roy\.openclaw\workspace\MEMORY.md`
- `C:\Users\Roy\.openclaw\openclaw.json`
- `C:\Users\Roy\.openclaw\workspace\matrix_scheduler.py`
- `C:\Users\Roy\.openclaw\workspace\day5_nurture_runner.py`
- `C:\Users\Roy\.openclaw\workspace\autopipeline_brain_content_publisher.py`
- `C:\Users\Roy\ComfyUI`
- `Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors`

## Missing

- `faceless_cash_cow_complete.md`
- `memory_manager.py`
- `sandbox_lab/`
- `viral_assets_vault.json`
- `video_maker.py`

## Not Wired Into Main Flow

A remote code search found no references to:
- `faceless_cash_cow_complete`
- `memory_manager`
- `viral_assets_vault`
- `retrieve_lessons`
- `record_mistake`
- `Approve Merge`

That means the older Ubuntu strategy was not fully re-deployed on this Windows host.

## Current Scheduler Reality

The active scheduler still points at a nurturing/tagging flow:
- `matrix_scheduler.py` -> `phase2_precision_tagging.py`

It does not currently prove:
- memory-anchor injection at runtime
- mistake-book retrieval before platform actions
- sandbox-only R&D workflow
- viral asset recycle routing
- HITL merge approvals

## ComfyUI Reality

- ComfyUI is installed.
- Current checkpoint inventory is very thin: `1` checkpoint, `0` usable LoRAs.
- ComfyUI was offline during audit.

## Practical Conclusion

This host has a working OpenClaw runtime plus partial content/publishing scripts, but it is not yet a faithful Windows redeploy of the full Ubuntu-era architecture.
