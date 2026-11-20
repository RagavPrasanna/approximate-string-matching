# Generated benchmark analysis

All times are per-call medians from interleaved, batched timing rounds. The tables use the lower envelope across three independent benchmark suite runs to reduce shared-machine noise. End positions are 0-based and exclusive.

## Runtime versus text length

|               |   Landau-Vishkin + LCE |   Sellers full matrix |   Sellers rolling rows |   Sellers threshold-pruned |
|:--------------|-----------------------:|----------------------:|-----------------------:|---------------------------:|
| (500, 80, 2)  |                  3.905 |                 5.764 |                  5.717 |                      2.154 |
| (1000, 80, 2) |                  7.182 |                12.023 |                 11.986 |                      4.656 |
| (2000, 80, 2) |                 15.181 |                24.199 |                 23.485 |                     10.282 |
| (4000, 80, 2) |                 31.851 |                49.908 |                 46.104 |                     19.322 |
| (8000, 80, 2) |                141.229 |               220.884 |                208.539 |                     92.631 |

## Runtime versus pattern length

|                |   Landau-Vishkin + LCE |   Sellers full matrix |   Sellers rolling rows |   Sellers threshold-pruned |
|:---------------|-----------------------:|----------------------:|-----------------------:|---------------------------:|
| (4000, 20, 3)  |                 71.991 |                28.321 |                 28.136 |                     54.586 |
| (4000, 50, 3)  |                 79.625 |                67.71  |                 63.859 |                     58.584 |
| (4000, 100, 3) |                 78.741 |               131.2   |                132.241 |                     57.24  |
| (4000, 200, 3) |                 87.572 |               266.103 |                266.035 |                     54.862 |
| (4000, 400, 3) |                 94.147 |               545.241 |                535.432 |                     54.872 |

## Runtime versus error threshold

|                 |   KMP (k = 0) |   Landau-Vishkin + LCE |   Sellers full matrix |   Sellers rolling rows |   Sellers threshold-pruned |
|:----------------|--------------:|-----------------------:|----------------------:|-----------------------:|---------------------------:|
| (4000, 100, 0)  |         0.699 |                 43.504 |               135.107 |                131.002 |                     12.783 |
| (4000, 100, 1)  |       —     |                 58.089 |               131.938 |                129.196 |                     25.058 |
| (4000, 100, 2)  |       —     |                 73.727 |               133.407 |                133.78  |                     42.251 |
| (4000, 100, 4)  |       —     |                 93.514 |               132.019 |                127.989 |                     69.868 |
| (4000, 100, 8)  |       —     |                137.325 |               136.93  |                133.969 |                    130.456 |
| (4000, 100, 16) |       —     |                217.163 |               129.008 |                130.633 |                    235.74  |
| (4000, 100, 32) |       —     |                378.381 |               136.418 |                133.747 |                    413.801 |

## Alphabet and natural language

| case                        |   Landau-Vishkin + LCE |   Sellers full matrix |   Sellers rolling rows |   Sellers threshold-pruned |
|:----------------------------|-----------------------:|----------------------:|-----------------------:|---------------------------:|
| planted-binary-n3000-m80-k3 |                 60.504 |                79.221 |                 81.156 |                     60.144 |
| planted-dna-n3000-m80-k3    |                 56.678 |                80.154 |                 75.019 |                     40.676 |
| english-n3000-m80-k3        |                 54.63  |                74.979 |                 78.971 |                     20.953 |

## Adversarial inputs

| case                      |   Landau-Vishkin + LCE |   Sellers full matrix |   Sellers rolling rows |   Sellers threshold-pruned |
|:--------------------------|-----------------------:|----------------------:|-----------------------:|---------------------------:|
| prefix-trap-n3000-m100-k3 |                 64.898 |                96.112 |                 95.404 |                     68.025 |
| repeat-AC-n3000-m100-k3   |                 73.06  |               101.04  |                 97.587 |                    460.096 |
| repetitive-n3000-m100-k3  |                 74.084 |               101.387 |                 93.413 |                    452.5   |

## Runtime scaling (same-machine control run)

|               |   Landau-Vishkin + LCE |   Sellers full matrix |   Sellers rolling rows |   Sellers threshold-pruned |
|:--------------|-----------------------:|----------------------:|-----------------------:|---------------------------:|
| (500, 80, 2)  |                  9.672 |                12.65  |                 12.889 |                      5.877 |
| (1000, 80, 2) |                 18.131 |                26.689 |                 25.192 |                     11.877 |
| (2000, 80, 2) |                 34.347 |                54.49  |                 52.779 |                     23.041 |
| (4000, 80, 2) |                 65.183 |               103.123 |                112.034 |                     44.361 |

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
| distance-n1000-k1  |                2.781 |                   361.875 |
| distance-n1000-k2  |                4.199 |                   354.431 |
| distance-n1000-k4  |                6.776 |                   370.633 |
| distance-n1000-k8  |               13.328 |                   355.602 |
| distance-n1000-k16 |               21.436 |                   340.09  |
| distance-n1000-k32 |               46.108 |                   352.556 |
