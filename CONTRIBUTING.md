# Contributing
1. `python -m unittest discover -s tests` must pass (no installs needed).
2. If you change a rule that the dashboard also has, update both, then refresh `tests/fixtures/` from the dashboard (the fixtures are numbers the dashboard's own JavaScript produced).
3. Re-run `python -m dukan_drishti bench` after any change to search or forecast, and say what moved. Our worst bug (JOURNEY.md, problem 7) was a fix that lowered accuracy.
4. After editing any `docs/*.md`: `pip install markdown && python scripts/build_site.py`.
5. Every verdict needs a reason and a sentence on what it does not prove.
