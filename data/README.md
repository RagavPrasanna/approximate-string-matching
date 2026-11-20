# Sample data

- `sample_dna.txt` — 5000 DNA characters with several planted mutated copies of
  `GATTACAGATTACA`.
- `sample_english.txt` — a short English passage used for demonstration.

These are optional convenience files. The benchmark creates all of its controlled
inputs in memory, so it does not depend on these files.

Example:

```powershell
python -m asm.cli search --text-file data/sample_dna.txt --pattern GATTACAGATTACA --k 1 --algorithm lv
```
