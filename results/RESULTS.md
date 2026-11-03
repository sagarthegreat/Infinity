# forehear benchmark results
4,018 human-recorded spoken questions (HeySQuAD dev), streamed through Vosk en-us-0.22-lgraph in 100 ms chunks; retrieval over 19,831 SQuAD v2 passages with BM25 (forehear.BM25Index), top-5. End of turn fires 500 ms after the last word. Wait = time from end of turn until retrieved context is ready (lower is better). All numbers are deterministic; rerun with `forehear bench`.

## Scenario `interims_only`: mean retrieval wait after end of turn
| policy | local | hosted_kb | rerank | web_search | calls/turn |
|---|---:|---:|---:|---:|---:|
| `final_only` | 10 ms | 280 ms | 806 ms | 1,790 ms | 1.00 |
| `interval_1000ms` | 5 ms | 161 ms | 564 ms | 1,496 ms | 3.52 |
| `interval_500ms` | 3 ms | 106 ms | 455 ms | 1,400 ms | 5.40 |
| `local_agreement` | 5 ms | 169 ms | 593 ms | 1,550 ms | 3.64 |
| `stable_prefix` | 2 ms | 76 ms | 392 ms | 1,347 ms | 3.53 |
| `stable_prefix_lean` | 3 ms | 90 ms | 413 ms | 1,366 ms | 2.60 |
| `stable_prefix_overlap` | 3 ms | 103 ms | 436 ms | 1,337 ms | 3.60 |
| `adaptive` | 10 ms | 98 ms | 430 ms | 1,368 ms | 2.64 |
| `oracle` | 0 ms | 0 ms | 1 ms | 78 ms | 1.00 |

### `interims_only` / `local`
| policy | wait mean | wait p90 | saved mean | ready at EOT | coverage | accuracy | calls/turn | recall@k Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `final_only` | 10 | 19 | -0 | 0% | 0% | 0% | 1.00 | +0.0 pt |
| `interval_1000ms` | 5 | 14 | 5 | 50% | 50% | 17% | 3.52 | -1.8 pt |
| `interval_500ms` | 3 | 11 | 7 | 70% | 71% | 14% | 5.40 | -2.0 pt |
| `local_agreement` | 5 | 15 | 5 | 48% | 48% | 15% | 3.64 | -3.4 pt |
| `stable_prefix` | 2 | 8 | 8 | 80% | 80% | 24% | 3.53 | -1.3 pt |
| `stable_prefix_lean` | 3 | 10 | 7 | 73% | 74% | 32% | 2.60 | -1.3 pt |
| `stable_prefix_overlap` | 3 | 10 | 8 | 73% | 74% | 22% | 3.60 | -0.4 pt |
| `adaptive` | 10 | 19 | 0 | 0% | 0% | 23% | 1.01 | +0.0 pt |
| `oracle` | 0 | 0 | 10 | 100% | 100% | 100% | 1.00 | +0.0 pt |

### `interims_only` / `hosted_kb`
| policy | wait mean | wait p90 | saved mean | ready at EOT | coverage | accuracy | calls/turn | recall@k Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `final_only` | 280 | 458 | 0 | 0% | 0% | 0% | 1.00 | +0.0 pt |
| `interval_1000ms` | 161 | 389 | 119 | 37% | 50% | 17% | 3.52 | -2.0 pt |
| `interval_500ms` | 106 | 323 | 173 | 56% | 71% | 14% | 5.40 | -2.9 pt |
| `local_agreement` | 169 | 400 | 110 | 35% | 48% | 15% | 3.64 | -3.4 pt |
| `stable_prefix` | 76 | 283 | 203 | 67% | 80% | 24% | 3.53 | -2.9 pt |
| `stable_prefix_lean` | 90 | 309 | 190 | 64% | 74% | 32% | 2.60 | -2.9 pt |
| `stable_prefix_overlap` | 103 | 326 | 176 | 56% | 74% | 22% | 3.60 | -0.9 pt |
| `adaptive` | 98 | 319 | 181 | 60% | 72% | 30% | 2.64 | -2.7 pt |
| `oracle` | 0 | 0 | 280 | 100% | 100% | 100% | 1.00 | +0.0 pt |

### `interims_only` / `rerank`
| policy | wait mean | wait p90 | saved mean | ready at EOT | coverage | accuracy | calls/turn | recall@k Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `final_only` | 806 | 1,193 | -0 | 0% | 0% | 0% | 1.00 | +0.0 pt |
| `interval_1000ms` | 564 | 1,079 | 243 | 17% | 50% | 17% | 3.52 | -2.2 pt |
| `interval_500ms` | 455 | 1,000 | 351 | 28% | 71% | 14% | 5.40 | -3.0 pt |
| `local_agreement` | 593 | 1,099 | 213 | 14% | 48% | 15% | 3.64 | -3.5 pt |
| `stable_prefix` | 392 | 948 | 414 | 35% | 80% | 24% | 3.53 | -3.3 pt |
| `stable_prefix_lean` | 413 | 969 | 394 | 34% | 74% | 32% | 2.60 | -3.3 pt |
| `stable_prefix_overlap` | 436 | 990 | 370 | 31% | 74% | 22% | 3.60 | -0.9 pt |
| `adaptive` | 430 | 976 | 376 | 31% | 72% | 30% | 2.64 | -2.9 pt |
| `oracle` | 1 | 0 | 806 | 100% | 100% | 100% | 1.00 | +0.0 pt |

### `interims_only` / `web_search`
| policy | wait mean | wait p90 | saved mean | ready at EOT | coverage | accuracy | calls/turn | recall@k Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `final_only` | 1,790 | 2,929 | -0 | 0% | 0% | 0% | 1.00 | +0.0 pt |
| `interval_1000ms` | 1,496 | 2,689 | 293 | 4% | 50% | 17% | 3.52 | -1.9 pt |
| `interval_500ms` | 1,400 | 2,592 | 390 | 7% | 71% | 14% | 5.40 | -2.2 pt |
| `local_agreement` | 1,550 | 2,747 | 240 | 3% | 48% | 15% | 3.64 | -3.5 pt |
| `stable_prefix` | 1,347 | 2,573 | 443 | 9% | 80% | 24% | 3.53 | -2.0 pt |
| `stable_prefix_lean` | 1,366 | 2,604 | 423 | 9% | 74% | 32% | 2.60 | -2.0 pt |
| `stable_prefix_overlap` | 1,337 | 2,623 | 453 | 12% | 74% | 22% | 3.60 | -0.6 pt |
| `adaptive` | 1,368 | 2,573 | 422 | 9% | 72% | 30% | 2.64 | -1.8 pt |
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
| `stable_prefix_overlap` | 0 ms | 23 ms | 337 ms | 1,263 ms | 3.96 |
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
| `interval_1000ms` | 31 | 114 | 249 | 77% | 100% | 26% | 3.86 | -0.7 pt |
| `interval_500ms` | 22 | 71 | 258 | 83% | 100% | 17% | 5.74 | -1.0 pt |
| `local_agreement` | 32 | 115 | 248 | 76% | 100% | 25% | 3.94 | -0.8 pt |
| `stable_prefix` | 17 | 33 | 263 | 87% | 100% | 25% | 3.96 | -1.1 pt |
| `stable_prefix_lean` | 18 | 43 | 261 | 86% | 100% | 33% | 3.03 | -1.1 pt |
| `stable_prefix_overlap` | 23 | 72 | 257 | 82% | 100% | 25% | 3.96 | -0.3 pt |
| `adaptive` | 22 | 73 | 257 | 83% | 100% | 37% | 2.68 | -0.9 pt |
| `oracle` | 0 | 0 | 280 | 100% | 100% | 100% | 1.00 | +0.0 pt |

### `with_eager_eot` / `rerank`
| policy | wait mean | wait p90 | saved mean | ready at EOT | coverage | accuracy | calls/turn | recall@k Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `final_only` | 806 | 1,193 | -0 | 0% | 0% | 0% | 1.00 | +0.0 pt |
| `eager_eot` | 507 | 893 | 300 | 1% | 100% | 88% | 1.13 | +0.0 pt |
| `interval_1000ms` | 413 | 846 | 393 | 17% | 100% | 26% | 3.86 | -1.4 pt |
| `interval_500ms` | 365 | 814 | 442 | 27% | 100% | 17% | 5.74 | -2.0 pt |
| `local_agreement` | 434 | 853 | 372 | 14% | 100% | 25% | 3.94 | -1.2 pt |
| `stable_prefix` | 323 | 783 | 483 | 34% | 100% | 25% | 3.96 | -2.7 pt |
| `stable_prefix_lean` | 329 | 792 | 477 | 33% | 100% | 33% | 3.03 | -2.7 pt |
| `stable_prefix_overlap` | 337 | 793 | 469 | 31% | 100% | 25% | 3.96 | -0.8 pt |
| `adaptive` | 352 | 802 | 455 | 28% | 100% | 36% | 2.75 | -2.2 pt |
| `oracle` | 1 | 0 | 806 | 100% | 100% | 100% | 1.00 | +0.0 pt |

### `with_eager_eot` / `web_search`
| policy | wait mean | wait p90 | saved mean | ready at EOT | coverage | accuracy | calls/turn | recall@k Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `final_only` | 1,790 | 2,929 | -0 | 0% | 0% | 0% | 1.00 | +0.0 pt |
| `eager_eot` | 1,490 | 2,629 | 300 | 0% | 100% | 88% | 1.13 | +0.0 pt |
| `interval_1000ms` | 1,415 | 2,586 | 375 | 4% | 100% | 26% | 3.86 | -0.3 pt |
| `interval_500ms` | 1,385 | 2,569 | 405 | 5% | 100% | 17% | 5.74 | -0.3 pt |
| `local_agreement` | 1,445 | 2,613 | 345 | 3% | 100% | 25% | 3.94 | -0.2 pt |
| `stable_prefix` | 1,327 | 2,537 | 463 | 8% | 100% | 25% | 3.96 | -0.6 pt |
| `stable_prefix_lean` | 1,331 | 2,540 | 458 | 8% | 100% | 33% | 3.03 | -0.6 pt |
| `stable_prefix_overlap` | 1,263 | 2,489 | 527 | 10% | 100% | 25% | 3.96 | -0.3 pt |
| `adaptive` | 1,348 | 2,548 | 442 | 7% | 100% | 36% | 2.75 | -0.4 pt |
| `oracle` | 78 | 0 | 1,712 | 91% | 100% | 100% | 1.00 | +0.0 pt |

## How early is the answer findable?
Share of all turns whose *current interim hypothesis* already retrieves a gold passage, by time relative to the end of the last word.

| t (ms) | retrievable | still speaking |
|---:|---:|---:|
| -3000 | 11% | 82% |
| -2750 | 13% | 87% |
| -2500 | 16% | 92% |
| -2250 | 20% | 96% |
| -2000 | 24% | 98% |
| -1750 | 29% | 99% |
| -1500 | 34% | 100% |
| -1250 | 38% | 100% |
| -1000 | 43% | 100% |
| -750 | 49% | 100% |
| -500 | 54% | 100% |
| -250 | 60% | 100% |
| +0 | 66% | 100% |
| +250 | 70% | 100% |
| +500 | 73% | 100% |

Final transcript recall@5: 76%.

## Reuse validator sweep (`stable_prefix`, `rerank`, interims only)
| validator | threshold | wait mean | saved mean | coverage | recall@k Δ |
|---|---:|---:|---:|---:|---:|
| `token_coverage` | 0.4 | 154 | 652 | 93% | -10.2 pt |
| `token_coverage` | 0.6 | 191 | 616 | 92% | -8.8 pt |
| `token_coverage` | 0.8 | 392 | 414 | 80% | -3.3 pt |
| `token_coverage` | 0.9 | 611 | 195 | 58% | +0.0 pt |
| `token_coverage` | 1.0 | 625 | 182 | 57% | +0.0 pt |
| `result_overlap` | 0.4 | 237 | 569 | 89% | -4.8 pt |
| `result_overlap` | 0.6 | 331 | 475 | 82% | -2.8 pt |
| `result_overlap` | 0.8 | 436 | 370 | 74% | -0.9 pt |
| `result_overlap` | 0.9 | 546 | 261 | 65% | +0.0 pt |
| `result_overlap` | 1.0 | 546 | 261 | 65% | +0.0 pt |

## Turn-detector sensitivity (interims only)
End of turn fires this long after the last word. Faster detectors leave look-ahead less time.

| profile | end of turn | policy | wait mean | saved mean | calls/turn |
|---|---:|---|---:|---:|---:|
| `hosted_kb` | 300 ms | `final_only` | 280 | 0 | 1.00 |
| `hosted_kb` | 300 ms | `stable_prefix` | 106 | 173 | 3.38 |
| `hosted_kb` | 300 ms | `adaptive` | 122 | 158 | 2.62 |
| `hosted_kb` | 500 ms | `final_only` | 280 | 0 | 1.00 |
| `hosted_kb` | 500 ms | `stable_prefix` | 76 | 203 | 3.53 |
| `hosted_kb` | 500 ms | `adaptive` | 98 | 181 | 2.64 |
| `hosted_kb` | 800 ms | `final_only` | 280 | 0 | 1.00 |
| `hosted_kb` | 800 ms | `stable_prefix` | 47 | 232 | 3.61 |
| `hosted_kb` | 800 ms | `adaptive` | 74 | 205 | 2.67 |
| `rerank` | 300 ms | `final_only` | 806 | 0 | 1.00 |
| `rerank` | 300 ms | `stable_prefix` | 480 | 327 | 3.38 |
| `rerank` | 300 ms | `adaptive` | 503 | 303 | 2.62 |
| `rerank` | 500 ms | `final_only` | 806 | -0 | 1.00 |
| `rerank` | 500 ms | `stable_prefix` | 392 | 414 | 3.53 |
| `rerank` | 500 ms | `adaptive` | 430 | 376 | 2.64 |
| `rerank` | 800 ms | `final_only` | 806 | -0 | 1.00 |
| `rerank` | 800 ms | `stable_prefix` | 248 | 559 | 3.61 |
| `rerank` | 800 ms | `adaptive` | 307 | 500 | 2.68 |

### Column guide

- **wait mean / p90**: ms from end of turn until context is ready.
- **saved mean**: mean per-turn reduction vs. `final_only` (paired: same latency draws).
- **ready at EOT**: share of turns with zero wait.
- **coverage**: share of turns served by a speculative call.
- **accuracy**: speculative calls that served a turn / speculative calls issued (hardware prefetchers degrade performance below ~40%; here a wrong guess only costs a call).
- **calls/turn**: total retrieval calls per turn; `final_only` is 1.00.
- **recall@k Δ**: change in gold-passage recall vs. retrieving on the final transcript.
