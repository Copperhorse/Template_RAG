# qp-core

Shared foundations used by the app and the pipeline: storage, auth tokens, device selection and the
model registry. Import name: `qp_core`.

| Module | Purpose |
|---|---|
| `DBManager.py` | Every SQLite operation: users and password hashing, files, chunks, enrichments, questions, rejections, session results, pending deletions, per-user duplicate lookups. Creates and migrates the schema on start ([schema](../../docs/data-model.md)). |
| `auth.py` | Stdlib-only HS256 bearer tokens (`create_token`, `verify_token`) and `load_secret` (`QP_JWT_SECRET` or `data/.jwt_secret`). |
| `models.py` | Process-wide, lazy, thread-safe loaders: `get_bi_encoder()`, `get_cross_encoder()`, `get_docling_converter()`; `loaded_models()`, preload helpers. |
| `device.py` | `get_device()`: CUDA → MPS → CPU, override with `QP_DEVICE`. |
| `reconcile.py` | Compare SQLite with Chroma (orphan embeddings, unindexed files). CLI wrapper: `scripts/reconcile_chroma.py`. |
| `SimHashHandler.py` | SimHash generation and near-duplicate index. |
| `IDGenerator.py` | UUIDs for files and chunks. |
| `CSVManager.py`, `VectorStore.py` | **Legacy, unused** by the app (CSV export helper; an older Chroma wrapper superseded by `qp_pipeline.Embedder.QAVectorStore`). |

## Rules of thumb

* Load models only through `models.py`.
* Add schema changes as additive `ALTER TABLE` migrations in `DBManager._init_db`.
* `auth.py` must stay dependency-free; its tests cover tampered, expired, `alg:none` and wrong-secret tokens.

Tests: `tests/test_db_manager.py`, `test_auth.py`, `test_ids_simhash.py`, `test_models_registry.py`, `test_deletion.py`.
