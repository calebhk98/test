# Readability state of the book

Generated from `prose_grade.py --summary`. Chat transcript lines are stripped before grading,
so the graded word count runs below the raw count in the chat-heavy chapters.

```
file                     words   paras   sents  w/sent      sTTR  top100     F-K     ARI  Lexile 
-------------------------------------------------------------------------------------------------
01_before                4,118     118     303    13.6      36.8    48.6     4.7     4.5   931.3 
02_march_4th             3,160     111     216    14.6      36.7    51.3     4.6     4.4   957.3 
03_the_letter            3,175     128     232    13.7      36.0    50.4     4.5     4.3   929.7 
04_pluto                 2,810     119     197    14.2      38.6    47.8     4.8     4.5   952.3 
05_behind                2,679     105     199    13.4      34.9    47.3     4.3     4.1   927.5 
06_the_list              2,678     123     210    12.7      37.8    50.1     4.1     3.6   892.5 
07_the_same_room         2,773      98     194    14.3      36.9    50.7     4.6     4.2   951.9 
08_the_asking            2,889      94     179    16.1      37.1    50.0     5.5     5.7  1006.7 
09_february              2,204      68     157    14.0      34.8    53.5     4.5     4.0   929.6 
10_april                 3,544      84     236    15.0      38.7    49.4     5.5     5.0   970.3 
11_eight                 3,156      99     205    15.4      37.8    49.6     5.5     5.1   981.9 
12_nine                  2,718      81     192    14.1      38.2    48.9     5.0     4.6   948.1 
13_ten_pages             3,222      92     229    14.1      36.9    50.4     5.1     4.7   938.6 
14_sixty_degrees         3,758     111     243    15.4      37.4    48.5     5.7     5.3   986.5 
15_twelve                4,608     173     396    11.6      39.0    47.2     4.0     3.6   865.3 
16_thirteen              2,699      81     187    14.4      37.5    49.1     5.7     5.1   958.5 
17_fourteen              2,954      97     195    15.1      40.2    47.3     5.6     5.3   985.1 
18_fifteen               2,794      87     210    13.3      37.6    49.9     4.8     4.1   918.4 
19_sixteen               2,089      79     168    12.4      36.8    50.3     4.3     3.5   886.1 
20_the_parking_lot       2,712      87     225    12.0      40.6    45.7     4.1     3.9   883.0 
21_the_applications      3,151      88     192    16.4      40.0    47.3     6.8     6.7  1023.9 
22_the_offer             2,474      68     156    15.8      40.4    45.3     6.3     6.2  1004.8 
23_the_first_one         3,080      66     176    17.5      43.4    44.0     7.2     7.6  1061.3 
24_the_chat              1,318      23      60    21.9      40.8    41.6     9.5    10.0  1170.7 
25_ten_targets           2,093      35     101    20.7      39.8    45.9     8.3     8.8  1128.0 
26_the_exercise          2,135      27      99    21.5      39.1    45.1     8.2     8.9  1145.0 
27_nadia                 1,898      24      78    24.3      42.5    48.1     9.6    10.6  1200.2 
28_nineteen              2,714      41     143    19.0      42.8    44.0     8.3     8.6  1106.6 
29_the_file              2,073      41      96    21.5      43.0    46.5     9.3     9.5  1150.3 
30_cleared               2,023      52     115    17.6      41.9    46.3     7.7     7.6  1060.4 
31_ruth                  2,276      37     113    20.1      41.5    46.0     8.9     9.5  1126.2 
32_the_money             1,695      22      58    29.1      41.8    43.8    11.9    13.2  1303.3 
33_the_other_one         1,762      32      66    26.6      39.6    45.7    10.8    11.9  1250.6 
34_the_files             1,831      23      73    25.0      44.7    42.9    10.8    11.8  1224.8 
35_nine_minutes          1,811      21      79    22.9      40.8    43.8     9.6    10.1  1182.3 
-------------------------------------------------------------------------------------------------
book median              2,712      81     187    15.4      39.0    47.3     5.6     5.3   985.1 
corpus median           67,163   1,946   4,649    14.3      40.7    48.1     6.1     5.2   948.5 

corpus word and paragraph counts are whole books, so the
only compare like with like between chapters. A dash und
chapter is under 1000 words, which is shorter than the s
```

## The book as one document

```
file                     words   paras   sents  w/sent      sTTR  top100     F-K     ARI  Lexile 
-------------------------------------------------------------------------------------------------
HALSTEAD                93,074    2635    5978    15.5      38.9    47.8     5.9     5.7   995.4 
```

## Where that leaves the target

| | words | F-K | ARI | Lexile |
| :-- | --: | --: | --: | --: |
| **Book, whole** | 93,074 graded (96,474 raw) | **5.9** | **5.7** | **995** |
| Book, median chapter | 2,712 | 5.6 | 5.3 | 985 |
| Corpus baseline, median of 23 books | 67,163 | 6.1 | 5.2 | 949 |
| **Goal** | — | **9.0** | — | **1000** |

**Lexile is essentially at target.** 995 against a goal of 1000, and above the
948 corpus baseline. Read it to plus or minus 100L.

**Flesch-Kincaid is three grades short**, and the two measures disagree because they
measure different things. Flesch-Kincaid counts syllables per word and words per
sentence; Lexile counts sentence length against how common the words are. This book
writes long-ish sentences out of short, ordinary, concrete words — which is what a
child-viewpoint narrator ought to sound like — so it scores high on Lexile and low on
Flesch-Kincaid. Raising Flesch-Kincaid to 9 means polysyllabic vocabulary, which
would cost the voice more than the number is worth.

## The shape across the book, which matters more than the median

| chapters | Chloe's age | Lexile |
| :-- | :-- | --: |
| 1–20 | 6 to 16 | 865–1007 |
| 21–24 | 16 to 18 | 1005–1171 |
| 25–35 | 18 to 21 | 1060–1303 |

The book climbs about 350L from first chapter to last, and it climbs with her. That
gradient is worth more than hitting a flat 1000L everywhere, and flattening it would
be a real loss.

## The two chapters at the bottom

`15_twelve` at 865L and `20_the_parking_lot` at 883L are the lowest in the book, and
both are action chapters carried by short sentences. Chapter 15 is 54.8 percent
sentences under ten words. If anything gets raised, those two are where the headroom
is.
