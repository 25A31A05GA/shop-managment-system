# Case 1: Diwali morning, 154 products to order

**The situation.** It is Diwali (8 November 2026). The dashboard shows Horlicks 500 g with **1 packet** left on the shelf.

**What the engine sees.** Normal sales of Horlicks are about 91 packets a day, and Diwali lifts demand. Learned from the last two Diwalis, an average uplift of about **1.67x** (the seven days up to the festival) is applied to every product's daily sales. For Horlicks the plan says: **0.01 days of stock left, order 1,965 packets**, status "Order now". Across the shop, **154 of 231 products** are flagged.

**What a human should do.** Order the top few lines today and phone the supplier. Check the delivery days: each product has 3 to 6 days of delivery time, so a late order will miss the festival anyway.

**What could fool it.** The stock-on-hand numbers in the sample are made up. In a real shop they must come from bills, deliveries, returns and counts, or the plan is only as good as the counting.

**Lesson.** A normal-day plan looks calm. A festival-day plan should shout.
