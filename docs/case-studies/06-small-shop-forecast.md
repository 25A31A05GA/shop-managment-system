# Case 6: The kirana forecast that says "rough guide"

**The situation.** A single kirana sells about ₹10,000 a day, but day to day it jumps around far more than a 12-branch chain does.

**What the engine sees.** Back-test miss about **10.9%** on today's date (median **12.3%** over 60 dates). Because it is over 8%, the label says **"rough guide"** and the range is wide: about ₹1,42,662 to ₹1,98,487 for the next 14 days. For the 12-store supermarket the same method misses by about **4.9% to 6.2%** and says "fairly reliable".

**What a human should do.** Use the shape (weekends up, Diwali up) and the range, not the exact rupee figure.

**What could fool it.** One-off events: a wedding in the lane, a power cut, road works.

**Lesson.** The honest answer for a small shop is a range. A false-precision number would be worse.
