# Generated benchmark analysis

All times are per-call medians from interleaved, batched timing rounds. The tables use the lower envelope across three independent benchmark suite runs to reduce shared-machine noise. End positions are 0-based and exclusive.

## Runtime versus text length

|               |   Landau-Vishkin + LCE |   Sellers full matrix |   Sellers rolling rows |   Sellers threshold-pruned |
|:--------------|-----------------------:|----------------------:|-----------------------:|---------------------------:|
| (500, 80, 2)  |                  3.928 |                 5.916 |                  5.847 |                      2.159 |
| (1000, 80, 2) |                  7.12  |                12.029 |                 11.848 |                      4.636 |
| (2000, 80, 2) |                 15.387 |                24.24  |                 23.848 |                     10.4   |
| (4000, 80, 2) |                 31.695 |                49.948 |                 48.792 |                     19.389 |
| (8000, 80, 2) |                140.57  |               211.212 |                206.526 |                     85.828 |

## Runtime versus pattern length

|                |   Landau-Vishkin + LCE |   Sellers full matrix |   Sellers rolling rows |   Sellers threshold-pruned |
|:---------------|-----------------------:|----------------------:|-----------------------:|---------------------------:|
| (4000, 20, 3)  |                 74.593 |                27.824 |                 27.84  |                     57.164 |
| (4000, 50, 3)  |                 79.347 |                71.517 |                 68.07  |                     61.154 |
| (4000, 100, 3) |                 83.364 |               135.402 |                133.457 |                     58.181 |
| (4000, 200, 3) |                 89.232 |               264.82  |                263.815 |                     53.522 |
| (4000, 400, 3) |                 97.142 |               539.512 |                529.921 |                     55.969 |

## Runtime versus error threshold

|                 |   KMP (k = 0) |   Landau-Vishkin + LCE |   Sellers full matrix |   Sellers rolling rows |   Sellers threshold-pruned |
|:----------------|--------------:|-----------------------:|----------------------:|-----------------------:|---------------------------:|
| (4000, 100, 0)  |         0.673 |                 48.638 |               133.599 |                134.816 |                     13.131 |
| (4000, 100, 1)  |       —     |                 58.197 |               131.147 |                129.381 |                     24.484 |
| (4000, 100, 2)  |       —     |                 70.317 |               135.436 |                131.979 |                     42.559 |
| (4000, 100, 4)  |       —     |                 95.966 |               135.958 |                133.832 |                     74.079 |
| (4000, 100, 8)  |       —     |                139.431 |               130.332 |                130.052 |                    130.212 |
| (4000, 100, 16) |       —     |                268.353 |               152.981 |                130.985 |                    275.108 |
| (4000, 100, 32) |       —     |                424.519 |               145.922 |                152.91  |                    480.481 |

## Alphabet and natural language

| case                        |   Landau-Vishkin + LCE |   Sellers full matrix |   Sellers rolling rows |   Sellers threshold-pruned |
|:----------------------------|-----------------------:|----------------------:|-----------------------:|---------------------------:|
| planted-binary-n3000-m80-k3 |                 74.909 |               101.597 |                 95.182 |                     75.423 |
| planted-dna-n3000-m80-k3    |                 68.596 |                81.528 |                 76.287 |                     44.71  |
| english-n3000-m80-k3        |                 71.104 |                96.207 |                 87.719 |                     24.062 |

## Adversarial inputs

| case                      |   Landau-Vishkin + LCE |   Sellers full matrix |   Sellers rolling rows |   Sellers threshold-pruned |
|:--------------------------|-----------------------:|----------------------:|-----------------------:|---------------------------:|
| prefix-trap-n3000-m100-k3 |                 85.727 |               125.367 |                126.744 |                     85.663 |
| repeat-AC-n3000-m100-k3   |                 98.204 |               125.149 |                131.812 |                    551.449 |
| repetitive-n3000-m100-k3  |                101.185 |               105.43  |                112.692 |                    532.681 |

## Runtime scaling (same-machine control run)

|               |   Landau-Vishkin + LCE |   Sellers full matrix |   Sellers rolling rows |   Sellers threshold-pruned |
|:--------------|-----------------------:|----------------------:|-----------------------:|---------------------------:|
| (500, 80, 2)  |                 11.981 |                13.978 |                 11.788 |                      5.88  |
| (1000, 80, 2) |                 18.48  |                37.02  |                 36.127 |                     14.934 |
| (2000, 80, 2) |                 43.404 |                50.014 |                 52.055 |                     25.327 |
| (4000, 80, 2) |                 80.265 |               129.593 |                124.719 |                     54.717 |

## Peak traced memory scaling

|               |   Landau-Vishkin + LCE |   Sellers full matrix |   Sellers rolling rows |   Sellers threshold-pruned |
|:--------------|-----------------------:|----------------------:|-----------------------:|---------------------------:|
| (500, 80, 2)  |                  205.2 |                 323.4 |                    8.2 |                      134.4 |
| (1000, 80, 2) |                  397   |                 640   |                   16   |                      251.6 |
| (2000, 80, 2) |                  885.7 |                1274.2 |                   31.7 |                      581.9 |
| (4000, 80, 2) |                 1550.1 |                2541.8 |                   62.9 |                     1050.5 |

## Banded versus rolling-row edit distance

| case               |   Banded Levenshtein |   Rolling-row Levenshtein |
|:-------------------|---------------------:|--------------------------:|
| distance-n1000-k1  |                3.066 |                   428.132 |
| distance-n1000-k2  |                4.138 |                   411.059 |
| distance-n1000-k4  |                6.868 |                   446.712 |
| distance-n1000-k8  |               15.546 |                   457.006 |
| distance-n1000-k16 |               25.013 |                   360.004 |
| distance-n1000-k32 |               43.51  |                   351.097 |
