# Corpus provenance

The reference corpus the measures compare against.

23 books from Project Gutenberg, the same set `prose_reference.json` was
built from. Rebuild with `sh halstead/corpus/fetch.sh`.

Verified by rebuilding the profile and diffing against the stored one: 19 of
23 reproduce every metric exactly. Hemingway's two and `secret_garden` differ
slightly because Project Gutenberg has re-proofed them since; the stored
profile was left untouched so the existing baseline still holds.

| id | file |
| --- | --- |
| 541 | Age_of_Innocence_Wharton |
| 4368 | Flappers_and_Philosophers_Fitzgerald |
| 64317 | Great_Gatsby_Fitzgerald |
| 35162 | Gullibles_Travels_Lardner |
| 69683 | MenWithoutWomen_Hemingway |
| 8164 | My_Man_Jeeves_Wodehouse |
| 10554 | RightHo_Jeeves_Wodehouse |
| 67138 | SunAlsoRises_Hemingway |
| 6695 | Tales_of_the_Jazz_Age_Fitzgerald |
| 805 | This_Side_of_Paradise_Fitzgerald |
| 416 | Winesburg_Ohio_Anderson |
| 11 | alice_in_wonderland |
| 45 | anne_of_green_gables |
| 271 | black_beauty |
| 778 | five_children_and_it |
| 146 | little_princess |
| 514 | little_women |
| 16 | peter_pan |
| 1874 | railway_children |
| 113 | secret_garden |
| 74 | tom_sawyer |
| 120 | treasure_island |
| 289 | wind_in_willows |
