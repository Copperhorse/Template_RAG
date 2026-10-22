# Quote-matching tolerance

Real gold snippets, damaged the way a small model slips (`slip`) or the way a fabrication looks (`fabrication`); does the locator find the quote in its chunk? Good = slips accepted, fabrications rejected.

| damage | kind | n | median match score | max | strict accepts | loose accepts |
|---|---|---:|---:|---:|---:|---:|
| one word inserted | slip | 55 | 88 | 96 | 80% | 98% |
| two words swapped | slip | 33 | 92 | 99 | 97% | 100% |
| last 25% cut off | slip | 50 | 100 | 100 | 100% | 100% |
| one word dropped | slip | 46 | 89 | 100 | 72% | 87% |
| one word replaced | slip | 55 | 87 | 97 | 71% | 89% |
| 30% of words replaced | fabrication | 50 | 73 | 93 | 10% | 24% |
| 50% of words replaced | fabrication | 54 | 59 | 86 | 2% | 7% |
| text of another chunk | fabrication | 55 | 45 | 57 | 0% | 0% |
