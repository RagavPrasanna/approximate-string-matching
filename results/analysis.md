# Generated benchmark analysis

All times are per-call medians from interleaved, batched timing rounds. The tables use the lower envelope across three independent benchmark suite runs to reduce shared-machine noise. End positions are 0-based and exclusive.

## Runtime versus text length

|               |   Landau-Vishkin + LCE |   Sellers full matrix |   Sellers rolling rows |   Sellers threshold-pruned |
|:--------------|-----------------------:|----------------------:|-----------------------:|---------------------------:|
| (500, 80, 2)  |                  3.883 |                 5.72  |                  5.671 |                      2.167 |
| (1000, 80, 2) |                  7.184 |                11.421 |                 11.536 |                      4.624 |
| (2000, 80, 2) |                 15.273 |                24.136 |                 23.671 |                     10.431 |
| (4000, 80, 2) |                 30.83  |                48.574 |                 47.6   |                     18.781 |
| (8000, 80, 2) |                 63.796 |                96.319 |                 93.144 |                     38.441 |

## Runtime versus pattern length

|                |   Landau-Vishkin + LCE |   Sellers full matrix |   Sellers rolling rows |   Sellers threshold-pruned |
|:---------------|-----------------------:|----------------------:|-----------------------:|---------------------------:|
| (4000, 20, 3)  |                 31.693 |                12.468 |                 12.341 |                     23.331 |
| (4000, 50, 3)  |                 33.656 |                31.314 |                 30.262 |                     24.951 |
| (4000, 100, 3) |                 35.432 |                59.608 |                 59.32  |                     25.547 |
| (4000, 200, 3) |                 37.73  |               125.111 |                117.08  |                     23.509 |
| (4000, 400, 3) |                 40.848 |               243.664 |                236.467 |                     23.906 |

## Runtime versus error threshold

|                 |   KMP (k = 0) |   Landau-Vishkin + LCE |   Sellers full matrix |   Sellers rolling rows |   Sellers threshold-pruned |
|:----------------|--------------:|-----------------------:|----------------------:|-----------------------:|---------------------------:|
| (4000, 100, 0)  |          0.34 |                 23.24  |                63.253 |                 64.331 |                      6.153 |
| (4000, 100, 1)  |        —    |                 28.656 |                64.333 |                 63.263 |                     12.865 |
| (4000, 100, 2)  |        —    |                 32.797 |                64.37  |                 64.886 |                     20.73  |
| (4000, 100, 4)  |        —    |                 43.248 |                65.907 |                 63.796 |                     34.91  |
| (4000, 100, 8)  |        —    |                 60.686 |                65.935 |                 66.275 |                     60.926 |
| (4000, 100, 16) |        —    |                 81.655 |                53.266 |                 49.195 |                     88.402 |
| (4000, 100, 32) |        —    |                190.295 |                65.266 |                 63.525 |                    205.855 |

## Alphabet and natural language

| case                        |   Landau-Vishkin + LCE |   Sellers full matrix |   Sellers rolling rows |   Sellers threshold-pruned |
|:----------------------------|-----------------------:|----------------------:|-----------------------:|---------------------------:|
| planted-binary-n3000-m80-k3 |                 28.306 |                38.783 |                 39.194 |                     27.95  |
| planted-dna-n3000-m80-k3    |                 28.299 |                38.138 |                 37.392 |                     19.342 |
| english-n3000-m80-k3        |                 26.526 |                37.472 |                 36.923 |                     10.862 |

## Adversarial inputs

| case                      |   Landau-Vishkin + LCE |   Sellers full matrix |   Sellers rolling rows |   Sellers threshold-pruned |
|:--------------------------|-----------------------:|----------------------:|-----------------------:|---------------------------:|
| prefix-trap-n3000-m100-k3 |                 30.756 |                46.44  |                 45.368 |                     31.72  |
| repeat-AC-n3000-m100-k3   |                 34.721 |                48.585 |                 47.223 |                    219.003 |
| repetitive-n3000-m100-k3  |                 34.093 |                47.732 |                 46.448 |                    216.405 |

## Runtime scaling (same-machine control run)

|               |   Landau-Vishkin + LCE |   Sellers full matrix |   Sellers rolling rows |   Sellers threshold-pruned |
|:--------------|-----------------------:|----------------------:|-----------------------:|---------------------------:|
| (500, 80, 2)  |                  4.121 |                 6.093 |                  5.975 |                      2.555 |
| (1000, 80, 2) |                  8.125 |                12.418 |                 12.338 |                      5.262 |
| (2000, 80, 2) |                 15.989 |                25.072 |                 25.698 |                     10.248 |
| (4000, 80, 2) |                 32.832 |                51.743 |                 50.753 |                     22.175 |

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
| distance-n1000-k1  |                1.204 |                   154.944 |
| distance-n1000-k2  |                1.825 |                   154.401 |
| distance-n1000-k4  |                3.036 |                   155.458 |
| distance-n1000-k8  |                5.115 |                   130.198 |
| distance-n1000-k16 |               11.138 |                   169.927 |
| distance-n1000-k32 |               21.349 |                   167.551 |
