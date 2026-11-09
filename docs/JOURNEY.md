# The Journey: how Dukan Drishti was built, what failed, what we learned

Every problem below was logged when it happened. Nothing is polished after the fact.

## Timeline

| Stage | What existed |
|---|---|
| **Owner Control Room dashboard** | A single-page dashboard: today's summary, sales history, brands, regional source, offers, stock, suppliers, forecast, profit, purchase orders, expiry, khata, cash, customers, price watch, assistant, roles, in English, Telugu and Hindi |
| **Java engine, first build** | An engine in Java with its own test runner (kept as a backup, not part of this repo) |
| **First Python port** | Started, then left unfinished: the random-number, forecast and API modules were missing |
| **This release** | A complete Python engine rebuilt and checked against the dashboard's own numbers, plus API, CLI, 80 tests, website, report, case studies and slides |

> ✏️ **Add your own history here:** how many dashboard versions you built, what you redesigned, what broke. Only you know this part, and it is the part recruiters remember.

## What went wrong (8 problems logged in this build)

| # | Problem | How we found it | Fix | Lesson |
|---|---|---|---|---|
| 1 | The first Python port was left half-finished | Tests imported modules that did not exist | Rebuilt the core from scratch, then reused the finished side modules (profit, cash, price, history, roles) | Finish the foundation before the features |
| 2 | **Products did not match.** Horlicks showed 15,389 units in Python and 2,724 in the dashboard | First parity check against the dashboard's own JavaScript | The dashboard quietly grows from 18 to **231** products through later scripts. Exported the real catalog | Never assume the file you read first is the file that runs |
| 3 | Searching "horlix" returned nothing | A test that I wrote expecting it to work | The dashboard has the same gap. Added a rule for half-typed words with one slip | A claim in a README is a test you have not written yet |
| 4 | Searching "vi-john" returned nothing | Looking at why exact brand searches missed | Queries are now split on punctuation the same way as product names | Punctuation is input too |
| 5 | The benchmark under-counted: "Paper Boat" found for "boat" was scored a miss | Reading the misses one by one | Fixed the measurement (exact-word hit rate 95.0% to 97.5%) | Check the measurement before blaming the code |
| 6 | Search was slow: 64 searches per second | Timing it | Cached the word lists and skipped impossible comparisons. Same results on all 14 test queries, about 3x faster (190 to 270 per second depending on the machine) | Prove a speed-up changes nothing else |
| 7 | **My first fix for #3 made things worse:** top-1 accuracy fell from 86.5% to 77.3% | Re-running the benchmark after the change | The new rule was hiding a better exact match. Changed it to only ever improve a worse score. Back to 86.5% | Always re-run the benchmark after a "fix" |
| 8 | I claimed the forecast back-test was "70% worse in festival fortnights" | A rough check on 40 dates | A proper split on 60 dates showed the real gap is small: 6.4% against 5.9% for a supermarket (13.7% against 11.8% for a single kirana) | Correct your own claim in public |

## Hard lessons

1. **Parity beats confidence.** Both the dashboard and Python use the same random numbers and the same rules, so a test can compare them number by number. That caught problem 2 on the first run.
2. **A small shop is noisy.** One kirana's daily sales jump around, so its forecast misses by about 12% and honestly says "rough guide". We kept that, instead of hiding it.
3. **A fast-selling offer can still lose money.** The sample Diwali 1+1 on Horlicks sold over a thousand extra packets and still lost about ₹1.72 lakh, because the free packets cost more than the extra sales earned. See [Case 2](case-studies/02-the-offer-that-lost-money.md).

## What inspired it

> ✏️ **Write 3 or 4 honest sentences in your own words.** Did you see a shopkeeper lose money on stock-outs at Diwali? A family shop that kept credit in a notebook? A relative who could not tell which branch was losing money? Say it plainly.

## Where it goes next

Real bills from CSV · SQLite storage · Telugu and Hindi questions in Python · scheduled WhatsApp morning brief · price-walk entry form.
