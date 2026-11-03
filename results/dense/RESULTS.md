# forehear benchmark results
4,018 human-recorded spoken questions (HeySQuAD dev), streamed through Vosk en-us-0.22-lgraph in 100 ms chunks; retrieval over 19,831 SQuAD v2 passages with dense (minishlab/potion-retrieval-32M, model2vec), top-5. End of turn fires 500 ms after the last word. Wait = time from end of turn until retrieved context is ready (lower is better). All numbers are deterministic; rerun with `forehear bench`.

## Scenario `interims_only`: mean retrieval wait after end of turn
| policy | local | hosted_kb | rerank | web_search | calls/turn |
|---|---:|---:|---:|---:|---:|
| `final_only` | 10 ms | 280 ms | 806 ms | 1,790 ms | 1.00 |
| `interval_1000ms` | 5 ms | 161 ms | 564 ms | 1,496 ms | 3.52 |
| `interval_500ms` | 3 ms | 106 ms | 455 ms | 1,400 ms | 5.40 |
| `local_agreement` | 5 ms | 169 ms | 593 ms | 1,550 ms | 3.64 |
| `stable_prefix` | 2 ms | 76 ms | 392 ms | 1,347 ms | 3.53 |
| `stable_prefix_lean` | 3 ms | 90 ms | 413 ms | 1,366 ms | 2.60 |
| `stable_prefix_overlap` | 3 ms | 102 ms | 423 ms | 1,295 ms | 3.60 |
| `adaptive` | 10 ms | 98 ms | 430 ms | 1,368 ms | 2.64 |
| `oracle` | 0 ms | 0 ms | 1 ms | 78 ms | 1.00 |

### `interims_only` / `local`
| policy | wait mean | wait p90 | saved mean | ready at EOT | coverage | accuracy | calls/turn | recall@k Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `final_only` | 10 | 19 | -0 | 0% | 0% | 0% | 1.00 | +0.0 pt |
| `interval_1000ms` | 5 | 14 | 5 | 50% | 50% | 17% | 3.52 | -2.7 pt |
| `interval_500ms` | 3 | 11 | 7 | 70% | 71% | 14% | 5.40 | -2.7 pt |
| `local_agreement` | 5 | 15 | 5 | 48% | 48% | 15% | 3.64 | -4.0 pt |
| `stable_prefix` | 2 | 8 | 8 | 80% | 80% | 24% | 3.53 | -2.1 pt |
| `stable_prefix_lean` | 3 | 10 | 7 | 73% | 74% | 32% | 2.60 | -2.1 pt |
| `stable_prefix_overlap` | 3 | 10 | 8 | 73% | 73% | 22% | 3.60 | -0.3 pt |
| `adaptive` | 10 | 19 | 0 | 0% | 0% | 23% | 1.01 | +0.0 pt |
| `oracle` | 0 | 0 | 10 | 100% | 100% | 100% | 1.00 | +0.0 pt |

### `interims_only` / `hosted_kb`
| policy | wait mean | wait p90 | saved mean | ready at EOT | coverage | accuracy | calls/turn | recall@k Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `final_only` | 280 | 458 | 0 | 0% | 0% | 0% | 1.00 | +0.0 pt |
| `interval_1000ms` | 161 | 389 | 119 | 37% | 50% | 17% | 3.52 | -2.8 pt |
| `interval_500ms` | 106 | 323 | 173 | 56% | 71% | 14% | 5.40 | -3.6 pt |
| `local_agreement` | 169 | 400 | 110 | 35% | 48% | 15% | 3.64 | -4.1 pt |
| `stable_prefix` | 76 | 283 | 203 | 67% | 80% | 24% | 3.53 | -3.6 pt |
| `stable_prefix_lean` | 90 | 309 | 190 | 64% | 74% | 32% | 2.60 | -3.6 pt |
| `stable_prefix_overlap` | 102 | 326 | 177 | 57% | 73% | 22% | 3.60 | -0.8 pt |
| `adaptive` | 98 | 319 | 181 | 60% | 72% | 30% | 2.64 | -3.3 pt |
| `oracle` | 0 | 0 | 280 | 100% | 100% | 100% | 1.00 | +0.0 pt |

### `interims_only` / `rerank`
| policy | wait mean | wait p90 | saved mean | ready at EOT | coverage | accuracy | calls/turn | recall@k Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `final_only` | 806 | 1,193 | -0 | 0% | 0% | 0% | 1.00 | +0.0 pt |
| `interval_1000ms` | 564 | 1,079 | 243 | 17% | 50% | 17% | 3.52 | -2.9 pt |
| `interval_500ms` | 455 | 1,000 | 351 | 28% | 71% | 14% | 5.40 | -3.8 pt |
| `local_agreement` | 593 | 1,099 | 213 | 14% | 48% | 15% | 3.64 | -4.3 pt |
| `stable_prefix` | 392 | 948 | 414 | 35% | 80% | 24% | 3.53 | -3.9 pt |
| `stable_prefix_lean` | 413 | 969 | 394 | 34% | 74% | 32% | 2.60 | -3.9 pt |
| `stable_prefix_overlap` | 423 | 988 | 383 | 33% | 73% | 22% | 3.60 | -1.2 pt |
| `adaptive` | 430 | 976 | 376 | 31% | 72% | 30% | 2.64 | -3.5 pt |
| `oracle` | 1 | 0 | 806 | 100% | 100% | 100% | 1.00 | +0.0 pt |

### `interims_only` / `web_search`
| policy | wait mean | wait p90 | saved mean | ready at EOT | coverage | accuracy | calls/turn | recall@k Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `final_only` | 1,790 | 2,929 | -0 | 0% | 0% | 0% | 1.00 | +0.0 pt |
| `interval_1000ms` | 1,496 | 2,689 | 293 | 4% | 50% | 17% | 3.52 | -2.8 pt |
| `interval_500ms` | 1,400 | 2,592 | 390 | 7% | 71% | 14% | 5.40 | -3.1 pt |
| `local_agreement` | 1,550 | 2,747 | 240 | 3% | 48% | 15% | 3.64 | -4.1 pt |
| `stable_prefix` | 1,347 | 2,573 | 443 | 9% | 80% | 24% | 3.53 | -2.9 pt |
| `stable_prefix_lean` | 1,366 | 2,604 | 423 | 9% | 74% | 32% | 2.60 | -2.9 pt |
| `stable_prefix_overlap` | 1,295 | 2,581 | 495 | 14% | 73% | 22% | 3.60 | -0.9 pt |
| `adaptive` | 1,368 | 2,573 | 422 | 9% | 72% | 30% | 2.64 | -2.7 pt |
| `oracle` | 78 | 0 | 1,712 | 91% | 100% | 100% | 1.00 | +0.0 pt |

## Scenario `with_eager_eot`: mean retrieval wait after end of turn
| policy | local | hosted_kb | rerank | web_search | calls/turn |
|---|---:|---:|---:|---:|---:|
| `final_only` | 10 ms | 280 ms | 806 ms | 1,790 ms | 1.00 |
| `eager_eot` | 0 ms | 45 ms | 507 ms | 1,490 ms | 1.13 |
| `interval_1000ms` | 0 ms | 31 ms | 413 ms | 1,415 ms | 3.86 |
| `interval_500ms` | 0 ms | 22 ms | 365 ms | 1,385 ms | 5.74 |
| `local_agreement` | 0 ms | 32 ms | 434 ms | 1,445 ms | 3.94 |
| `stable_prefix` | 0 ms | 17 ms | 323 ms | 1,327 ms | 3.96 |
| `stable_prefix_lean` | 0 ms | 18 ms | 329 ms | 1,331 ms | 3.03 |
| `stable_prefix_overlap` | 0 ms | 23 ms | 332 ms | 1,251 ms | 3.96 |
| `adaptive` | 0 ms | 22 ms | 352 ms | 1,348 ms | 2.75 |
| `oracle` | 0 ms | 0 ms | 1 ms | 78 ms | 1.00 |

### `with_eager_eot` / `local`
| policy | wait mean | wait p90 | saved mean | ready at EOT | coverage | accuracy | calls/turn | recall@k Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `final_only` | 10 | 19 | -0 | 0% | 0% | 0% | 1.00 | +0.0 pt |
| `eager_eot` | 0 | 0 | 10 | 100% | 100% | 88% | 1.13 | +0.0 pt |
| `interval_1000ms` | 0 | 0 | 10 | 100% | 100% | 26% | 3.86 | +0.0 pt |
| `interval_500ms` | 0 | 0 | 10 | 100% | 100% | 17% | 5.74 | +0.0 pt |
| `local_agreement` | 0 | 0 | 10 | 100% | 100% | 25% | 3.94 | +0.0 pt |
| `stable_prefix` | 0 | 0 | 10 | 100% | 100% | 25% | 3.96 | +0.0 pt |
| `stable_prefix_lean` | 0 | 0 | 10 | 100% | 100% | 33% | 3.03 | +0.0 pt |
| `stable_prefix_overlap` | 0 | 0 | 10 | 100% | 100% | 25% | 3.96 | +0.0 pt |
| `adaptive` | 0 | 0 | 10 | 100% | 100% | 87% | 1.15 | +0.0 pt |
| `oracle` | 0 | 0 | 10 | 100% | 100% | 100% | 1.00 | +0.0 pt |

### `with_eager_eot` / `hosted_kb`
| policy | wait mean | wait p90 | saved mean | ready at EOT | coverage | accuracy | calls/turn | recall@k Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `final_only` | 280 | 458 | 0 | 0% | 0% | 0% | 1.00 | +0.0 pt |
| `eager_eot` | 45 | 158 | 234 | 65% | 100% | 88% | 1.13 | +0.0 pt |
| `interval_1000ms` | 31 | 114 | 249 | 77% | 100% | 26% | 3.86 | -0.9 pt |
| `interval_500ms` | 22 | 71 | 258 | 83% | 100% | 17% | 5.74 | -1.3 pt |
| `local_agreement` | 32 | 115 | 248 | 76% | 100% | 25% | 3.94 | -1.2 pt |
| `stable_prefix` | 17 | 33 | 263 | 87% | 100% | 25% | 3.96 | -1.7 pt |
| `stable_prefix_lean` | 18 | 43 | 261 | 86% | 100% | 33% | 3.03 | -1.7 pt |
| `stable_prefix_overlap` | 23 | 74 | 257 | 82% | 100% | 25% | 3.96 | -0.3 pt |
| `adaptive` | 22 | 73 | 257 | 83% | 100% | 37% | 2.68 | -1.4 pt |
| `oracle` | 0 | 0 | 280 | 100% | 100% | 100% | 1.00 | +0.0 pt |

### `with_eager_eot` / `rerank`
| policy | wait mean | wait p90 | saved mean | ready at EOT | coverage | accuracy | calls/turn | recall@k Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `final_only` | 806 | 1,193 | -0 | 0% | 0% | 0% | 1.00 | +0.0 pt |
| `eager_eot` | 507 | 893 | 300 | 1% | 100% | 88% | 1.13 | +0.0 pt |
| `interval_1000ms` | 413 | 846 | 393 | 17% | 100% | 26% | 3.86 | -1.7 pt |
| `interval_500ms` | 365 | 814 | 442 | 27% | 100% | 17% | 5.74 | -2.2 pt |
| `local_agreement` | 434 | 853 | 372 | 14% | 100% | 25% | 3.94 | -1.4 pt |
| `stable_prefix` | 323 | 783 | 483 | 34% | 100% | 25% | 3.96 | -2.7 pt |
| `stable_prefix_lean` | 329 | 792 | 477 | 33% | 100% | 33% | 3.03 | -2.8 pt |
| `stable_prefix_overlap` | 332 | 793 | 475 | 32% | 100% | 25% | 3.96 | -1.0 pt |
| `adaptive` | 352 | 802 | 455 | 28% | 100% | 36% | 2.75 | -2.3 pt |
| `oracle` | 1 | 0 | 806 | 100% | 100% | 100% | 1.00 | +0.0 pt |

### `with_eager_eot` / `web_search`
| policy | wait mean | wait p90 | saved mean | ready at EOT | coverage | accuracy | calls/turn | recall@k Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `final_only` | 1,790 | 2,929 | -0 | 0% | 0% | 0% | 1.00 | +0.0 pt |
| `eager_eot` | 1,490 | 2,629 | 300 | 0% | 100% | 88% | 1.13 | +0.0 pt |
| `interval_1000ms` | 1,415 | 2,586 | 375 | 4% | 100% | 26% | 3.86 | -0.4 pt |
| `interval_500ms` | 1,385 | 2,569 | 405 | 5% | 100% | 17% | 5.74 | -0.3 pt |
| `local_agreement` | 1,445 | 2,613 | 345 | 3% | 100% | 25% | 3.94 | -0.1 pt |
| `stable_prefix` | 1,327 | 2,537 | 463 | 8% | 100% | 25% | 3.96 | -0.7 pt |
| `stable_prefix_lean` | 1,331 | 2,540 | 458 | 8% | 100% | 33% | 3.03 | -0.7 pt |
| `stable_prefix_overlap` | 1,251 | 2,519 | 539 | 12% | 100% | 25% | 3.96 | -0.6 pt |
| `adaptive` | 1,348 | 2,548 | 442 | 7% | 100% | 36% | 2.75 | -0.6 pt |
| `oracle` | 78 | 0 | 1,712 | 91% | 100% | 100% | 1.00 | +0.0 pt |

### Column guide

- **wait mean / p90**: ms from end of turn until context is ready.
- **saved mean**: mean per-turn reduction vs. `final_only` (paired: same latency draws).
- **ready at EOT**: share of turns with zero wait.
- **coverage**: share of turns served by a speculative call.
- **accuracy**: speculative calls that served a turn / speculative calls issued (hardware prefetchers degrade performance below ~40%; here a wrong guess only costs a call).
- **calls/turn**: total retrieval calls per turn; `final_only` is 1.00.
- **recall@k Δ**: change in gold-passage recall vs. retrieving on the final transcript.
