# Blind Playthrough Log

Rules for this run: no source code, data files, documentation, or prior-session notes read. All decisions are based only on the game UI and ordinary outside knowledge.

1. The opening premise is unusually effective at defining the game in one paragraph. The line **“Knowing how a thing works is free. Building it is not”** immediately tells me this is about bootstrapping production rather than discovering modern science from scratch. I expect knowledge to be cheap and implementation bottlenecks to dominate.

2. I checked the Options menu before starting. It says these are defaults for new games and that only “the couple of these that can honestly change mid-game” remain adjustable later. That wording is helpful: I should not assume I can casually change foundational rules after starting.

3. The defaults shown were fog on, mortality off, 500-year horizon, Roman civilisation, and `poor_scholar`. “mortality : off” appears to mean immortality, which is what I want, but the label requires a tiny mental inversion. I expected something like “immortal: on/off” or “mortality: normal/disabled.”

4. The civilisation-selection screen is excellent at giving strategic identity rather than just flavor. Han advertises metallurgy, agriculture, bureaucracy, high state capacity, and cheaper prices; Scandinavia warns about weak funding; England warns about the Black Death; Mexica advertises state capacity but highlights missing iron, wheel use, and draught animals. I can form an actual plan before seeing mechanics.

5. I chose **The Later Han Empire, 100**. My reasoning: if the objective is a technology/industrial acceleration game, cast iron, agricultural productivity, bureaucracy, 58 million people, 0.90 state capacity, and prices at 0.75x Rome all look like compounding advantages. As a first-time player trying to win, this seems safer than choosing a civ with obvious capital or material bottlenecks.

6. Han's scenario introduction reinforces the strategic premise well. It explicitly says **“WHAT IS MISSING — Glass”** and **“the whole optical branch ... is, here, a thing you must start from sand and a furnace and an argument.”** My immediate expectation is that glassmaking is an early gateway, probably toward lenses, measurement, chemistry, or precision work. Fog prevents me from knowing whether that intuition is correct.

7. I selected the `merchant` starting kit, described as **“4,000 den ... a modest trading capital. You can fund one real venture.”** The first playable screen instead says **“You arrive in 100 AD with 3000 cash.”** Nothing shown so far explains the 1,000-den difference. I expected either 4,000 cash or an explicit statement that some amount was consumed by travel/setup/conversion.

8. I kept fog of war ON and mortality OFF. The mortality explanation is clear: the default founder does not age. The 500-year horizon remains at default.

9. The first playable instructions are strong. The game gives only five core commands—`state`, `available`, `why <name>`, `start <name>`, and `step`—plus `open`, `stuck`, `help`, and `quit`. This is enough to begin without needing external documentation, which is especially important for a command-line game.

10. `state` is dense but strategically useful. It immediately identifies the recurring cash burn (**net -37.9 cash/yr**), founder-hours, staffing, reputation/scandal/eminence, inherited technologies, hazard exposure, and the explicit target: **“Grown and alloy junction transistors.”** I now know the game is not asking me to industrialize vaguely; there is a concrete finish line.

11. The `available` command reports **257 startable now** but wisely summarizes them by subject rather than dumping everything. This is a good UI choice. The “CHEAPEST SIX” and especially “MOST RESTS ON THESE” sections are valuable because fog hides the tree; they give me local leverage signals without revealing the road.

12. The strongest-looking leverage items shown are `identity_cover` (ALL rests), `units_standards` (ALL), `arithmetic_positional` (ALL), `scientific_method` (much), and `prc_treadle_lathe_flywheel` (much). “ALL” is extremely attention-grabbing. My expectation is that standards and arithmetic are foundational enablers rather than direct profit centers.

13. The parser error for a nonsense command is clean and non-punitive: **“no command called 'foobar'. Type 'help' for the list.”** That is exactly what I want from a command game: no lost turn, no ambiguity.

14. `help` clearly states the victory condition and repeats a crucial trap: **“Finishing something earns you nothing. A concern earns when you 'open' it.”** This is important enough that repeating it is justified; I can easily imagine forgetting to open a completed venture.

15. `why units_standards` is exemplary. It explains not just the cost but the fiction and strategic reason: **“Every number in your corpus is meaningless to posterity without it.”** It also says almost everything rests on it. This makes the otherwise abstract “standards” project feel like an obvious foundational investment.

16. `scientific_method` explicitly says it is a **“Multiplier on every research node thereafter.”** That is the clearest compounding investment I have seen. Its two-year calendar floor and 20% failure risk make it less trivial than its low cash cost suggests.

17. The treadle lathe is reassuringly concrete: foot-powered continuous cutting, enabling cam operation and steady-speed cutting. Since almost everything rests on it, I expect precision manufacturing to be a central trunk toward the transistor.

18. Identity cover is interesting but expensive: 1,431 cash plus 200/year upkeep if opened. The text says it **“Reduces all future suspicion.”** I do not yet know how aggressively suspicion will matter, so spending nearly half my starting cash on it immediately feels premature.

19. `risk` is one of the most strategically important screens so far. It does not merely say “bad things may happen”; it gives dated historical windows, annual probabilities, cumulative intuition, and what kinds of defenses would help. The Yellow Turban window at 184–205 is described as roughly **99% chance at least one sacking lands somewhere**. I now have a real deadline for redundancy/protection, not just the 600 AD victory horizon.

20. This makes Han feel less like an obvious easy mode than the civilisation-select screen suggested. Its starting institutions are excellent, but the game explicitly threatens the administrative class and political unity those advantages depend on. That is good scenario design: the strengths and the historical failure mode are linked.

21. `money` reveals my 175.1/year starting revenue comes from cataract couching and trepanation as my personal medical practice. I like that the game gives the founder something historically plausible to sell immediately rather than forcing a pure bankruptcy puzzle.

22. The “merchant 4,000” versus “arrive with 3,000” discrepancy remains unexplained by the ledger. The ledger starts at 3,000 and attributes 45/year of living costs specifically to being rich. If 1,000 was intentionally converted into kit/status, I still have not been told what I received for it.

23. After one year, the treadle lathe and standards both completed. That immediately advanced the displayed road-to-goal count from 11 to 13. This is satisfying feedback: I can see that foundational choices mattered without being shown the hidden full tree.

24. Fog revealed a useful set of “heard of, cannot begin yet” breadcrumbs: `case_hardening`, `prc_drill_press`, `prc_slide_rest_simple`, `precision_three_plate`, `thermometer`, `balance_analytical`, and an optical standards laboratory. This feels like a believable precision-metrology chain toward electronics.

25. `scientific_method` had all its founder-hours spent after the first year but could not finish because the project has a two-year calendar/money absorption floor. The state text explains this clearly: **“Money in hand cannot buy it down faster.”** I like this because it prevents the game from collapsing into pure cash acceleration.

26. Scandal rose by 0.90 in the first year even though I only built standards and a lathe. The UI warns that at that rate I would cross the dangerous threshold in ~28 years. That surprised me; I expected socially provocative research to create suspicion, but not such ordinary technical foundations. I do not yet know what specifically generated it.

27. Scientific method completed in 101 and changed society values (`w_magic_fear`, `w_novelty`). I like that foundational ideas can alter social conditions rather than merely unlock nodes, though the terse variable-like labels are not human-readable. Seeing **“w_magic_fear”** in player-facing output feels like an internal identifier leaking through the UI.

28. Completing scientific method moved the road count from 13 to 14, confirming it lies on the victory route.

29. `corpus_written` became available: **“Write the corpus: evidence…”**, 6,000 founder-hours, ten-year floor, 1,386 cash. The name and timing make me suspect it is a knowledge-preservation hedge against the sacking windows. The game does not explicitly say that in the listing, so this is an inference I am making from context.

30. The `available find drill/slide/thermometer` responses are good under fog: they explicitly say that a thing can exist without being currently startable and reveal only the number of unknown prerequisites. That lets me reason without spoiling the tree.

31. The corpus description is thematically excellent: **“The alchemists' habit of deliberate obscurity destroyed centuries of work. Assume every reader is competent and knows nothing.”** It reads like a real preservation project rather than a generic “backup” button.

32. However, I still cannot tell from `why corpus_written` exactly how much it protects against sacking. Given that `risk` quantified the hazard so precisely, I expected the defensive project to quantify its hedge as well. I can infer its purpose, but not its mechanical value.

33. `available electricity` currently contains a codebook and maritime signal flags, not anything I would colloquially call electricity. This subject label is confusing. I expected batteries, static electricity, conductors, or measurement; instead it appears to contain communications items.

34. I tried `available power and precision limit 30`, mirroring the subject label shown earlier. The parser treated the entire phrase as the subject and returned nothing. The UI does explain valid pagination syntax elsewhere, but multi-word subjects plus modifiers are awkward enough that this is an easy first-time-player mistake.

35. `help commands` revealed `rush`, which can “start everything you could begin today in one go, highest-leverage first.” I am deliberately not using it yet. It looks like a useful convenience/AI-facing command, but for this blind playthrough I want to understand enough of the strategic choices myself that the result is informative.

36. Sorting by annual earnings exposed two strikingly good small businesses: a rope walk (448.6 cost, 500–1,300/yr revenue, 60 upkeep) and horizontal loom (201.4 cost, 300–575/yr, 30 upkeep). If those figures survive opening/scale-up, they should transform my cash flow. This is my first intentional economic expansion rather than tech-rushing.

37. `arithmetic_positional` is now visibly connected under fog to both `statistics_basic` and `atomic_theory`, and the earlier list said “ALL” rests on it. That makes positional notation feel like a rational foundational choice for the transistor route.

38. The rope walk and horizontal loom both completed in one year, but decimal positional notation failed on its first attempt. The failure message is excellent: **“40% of the hours are to do again ... and 240 is gone. Attempt 2.”** It tells me exactly what the setback cost without hiding behind a generic “failed.”

39. A random event also hit immediately: **“fire in the timber wards of the capital: it destroyed 175 cash.”** This made the economic opening feel less deterministic. It also reinforces why I should not spend down to zero even when quoted project ROI looks excellent.

40. The completed businesses are not auto-opened, and `ventures` shows their actual local figures: horizontal loom 333.2/yr revenue against 22.5 costs, rope walk 666.3/yr against 45 costs. This is even clearer than the earlier range. Together they should turn my economy strongly positive once opened.

41. `available power and precision` works if used as the entire command, confirming my earlier failure was a syntax interaction with `limit 30`, not an invalid subject. The list exposes a plausible machine-tool progression: straightedge, faceplate, chuck, tailstock, back gear, etc. This is exactly the kind of stuff I expected to precede better lathes and precision measurement.

42. Opening both textile concerns taught me an important market rule the hard way. The ledger says they compete with each other and market saturation is taking about **382/year, 64% of their quoted combined output**. I expected diminishing returns eventually, but not this sharply after only two businesses. This punishes naive “sort by earnings and build the top entries” play in a sensible way.

43. The ledger explains saturation clearly after the fact and warns that opening another concern in the same category will make it worse. I would protect this explanation; it converts what could feel like a hidden nerf into a legible economic system.

44. Decimal positional notation completed on the second attempt and moved the road count from 14 to 15. It also unlocked `statistics_basic` and made `atomic_theory` visible. That is exactly the kind of intellectual progression I expected.

45. Atomic theory is blocked not by money or another hidden technology but by **2 trained scholars; I have 1.0**. This is the first clear personnel bottleneck on the scientific route, and it tells me I can no longer treat the founder as a one-person research lab forever.

46. I spent too aggressively on the precision bundle: after one year I was down to 129.5 cash. Two of the five precision projects failed their first attempts. This is a useful punishment for treating low individual prices as if a batch were free.

47. Statistics completed and the road count rose from 15 to 16. Its description connects controlled comparison to medical trials and state administration, which makes it feel broader than a checkbox prerequisite.

48. `why atomic_theory` is one of the strongest pieces of strategic signaling so far: **“You can write the periodic table from memory on day one. It is worth roughly 150 years of chemistry. It only becomes operational once you have the analytical balance, so write it early and prove it later.”** This gives me both urgency and a future measurement bottleneck.

49. Scholar labour is expensive but available: one scholar costs 328/year, with a headcount ceiling tied to literacy/printing/schools. I like that science capacity is modeled as a social infrastructure problem, not just a money slider.

50. Hiring one scholar immediately consumed almost all cash on hand because the annual wage was charged up front (capital fell from 403.4 to 75.2). I did not expect hiring to hit capital that sharply at the instant of hire; the UI does show the result, but a pre-hire quote/confirmation would help a first-time player avoid accidentally zeroing out cash.

51. Starting atomic theory pushed me onto credit. The debt explanation is excellent: it gives borrowed amount, interest, hard credit ceiling, and the concrete consequence—unfinished projects halt and creditors seize running concerns. Debt feels dangerous but understandable.

52. At 107 my recurring cash flow turned negative (-64.4/yr) because the scholar wage exceeds the still-ramping textile surplus. This is the first point where I feel genuinely financially constrained rather than merely choosing what to buy.

53. Atomic theory completed in 107 and advanced the displayed victory-road count from 16 to 17. The game rewarded a financially painful science investment with clear progress, which felt good.

54. By 108 I was at -552 cash and -115.8/year recurring. The hired scholar had become a liability once atomic theory finished. This is a good example of staff being a strategic commitment rather than a permanent stat upgrade.

55. The only currently startable chemistry project is white phosphorus extraction. It is expensive (1,668), risky (20%), but has quoted revenue of 1,500–3,300/year and “a few” things resting on it. Because it both diversifies my economy and plausibly advances chemistry, I am treating it as a calculated rescue investment rather than a pure profit grab.

56. The phosphorus gamble nearly maxed my credit. At 109 I had -1,359 cash and only a little under 900 of remaining borrowing headroom, while 617 of the project bill was still unpaid. The state line **“in arrears: after fixed costs there is nothing left to draw on”** is alarming but useful. I genuinely felt I could lose the economic base if this project failed.

57. `available heard_offset 25 ... sort nearest` finally exposed a much more victory-relevant set of hidden names, including `quantum_solidstate_theory`, analytical chemistry, spectroscopy, precision standards, powder metallurgy, and interchangeable parts. This is the strongest confirmation yet that I am on the right broad scientific/industrial road.

58. My expectation that one more year would finish phosphorus was wrong. At 110 the project still had 466.1 owed, and by 111 it had 315.3 owed. Arrears are throttling what the project can absorb even though the nominal credit ceiling has not been crossed. This is mechanically interesting, but I only fully understood it after watching the project crawl.

59. I mistakenly tried `open chm_phosphorus_extraction` before it had completed and got a clean refusal: **“you have not worked out how to do that yet, so there is nothing to open.”** Good error handling; no penalty, no ambiguity.

60. White phosphorus extraction finally completed in 113 and increased the road count from 17 to 18. That confirms it was not merely a bailout business; it also lies on or supports the victory route.

61. The realized concern figures are strong: ~1,666/year revenue against 112.5 upkeep, opening cost 250.2. After several years of debt drag, this feels like the first real chance to regain strategic freedom.

62. Attempting to open phosphorus was refused because it needs **1.33 craftsmen to supervise** while the loom and rope walk already consume 0.80 of my single craft capacity. This surprised me in a good way: even a completed technology/business cannot scale without management bandwidth.

63. The refusal is actionable: it tells me to hire, teach, or close something. This is good UX for a complex system.

64. Hiring one smith and mothballing the weaker loom solved the supervision bottleneck. Phosphorus opened successfully and, after three years, transformed the economy: 2,860 cash and +1,731/year recurring by 120 AD. This felt like a genuine strategic recovery rather than a scripted bailout.

65. The realized phosphorus concern earns ~1,698/year in the ledger once ramped. Diversifying out of textiles mattered enormously. The market system rewards category diversification in a way that is easy to understand after experiencing saturation once.

66. `why quantum_solidstate_theory` is a great fog-compatible reveal. It says the node is the **“single largest time saving in the programme”**, but it needs 8 scholars while current literacy makes more than 5.9 impossible. The UI explicitly points toward printing, paper, schools, and academies. This gives me a civilization-building objective rather than a hidden arbitrary gate.

67. The quantum description is also thematically excellent: **“Write them down in your first decade, in plain quantitative language, in many copies, because you will not live to see them tested.”** In my immortal run the mortality line is fictionally off, but the design intention is clear.

68. Case hardening, three-plate flatness, analytical balance, and spectroscope form a convincing metrology ladder. I especially like the analytical-balance line: **“This is the instrument that converts alchemy into chemistry.”** It tells me why precision mechanics matters to chemistry.

69. Several `why` screens include phrases like **“[FIXED after independent audit: ...]”** in player-facing descriptions. That reads like developer/test history leaking into final game prose. It breaks immersion and should probably be removed from the player-facing text.

70. The school is powerful—+4 scholars immediately and +2/year thereafter—but expensive (8,625) and currently blocked by two unknown prerequisites. Crucially, the game says it is OPTIONAL and that nothing technical strictly requires it. That is good: schools are an accelerator/capacity solution, not an arbitrary hard lock.

71. The machinist trade does not exist in Han yet and has a literacy-dependent headcount ceiling. This makes the printing/paper path relevant to precision manufacturing as well as scholarship, which ties institutional and technical development together nicely.

72. The mathematics list contains many small notation nodes plus `algebra_symbolic` marked “much.” Since I already built the combined positional-notation foundation, some of the fine-grained notation entries feel redundant from a player's perspective; I do not yet know whether they matter to the main route.

73. A hired smith disappeared in 121 (**“you lose 1 smith to death and to better offers”**), which automatically closed phosphorus because supervision fell short. This is a meaningful operational risk: one-person staffing is brittle. The auto-close message is good because it preserves the knowledge and tells me how to reopen.

74. The six-project infrastructure batch was productive: paper improvements, symbolic algebra, silica refractory, and basic Bessemer steel all completed. The displayed victory-road count jumped from 18 to 21, so at least several were relevant.

75. Despite building obvious steel infrastructure, `case_hardening` remains blocked by one unknown prerequisite. That is now a genuine puzzle I want to solve from the visible game rather than by reading the tree.

76. At the 125 AD checkpoint I tried `save /mnt/data/rome_blind/manual_125.json` and the game refused it: **“a save file must be a relative path, not an absolute one. Try save mygame.json.”** The error is clear and gives the correct form, so this is easy to recover from.

77. The two machinist trainees finished in 122, and by 125 I effectively have 4 craft hands (founder + smith + two machinists). Creating the trade worked and gives me enough skilled-craft capacity for the three-plate/analytical-balance path once prerequisites clear.

78. A fire in 124 destroyed 1,527 cash even though I was otherwise doing well. The recurring fires are starting to feel like a real reason to avoid holding idle cash, not just flavor.

79. `risk` explicitly names `school_founded` as something that would help against the Yellow Turban sacking risk. That links institutional development to disaster resilience and makes the school more strategically important than its “optional” label initially suggested.

80. The visible printing search exposes `Block printing` and `Type metal`. This is a nice historical progression clue; I expect one or both to unlock movable-type/press technology and raise literacy capacity.

81. Block printing + type metal did **not** unlock the school. My historical intuition (“printing infrastructure should solve literacy”) was only partially right. This is a useful blind-play finding because the game currently gives me no visible hint which two school prerequisites remain hidden.

82. The regency event reduced trade/output to 94% and shifted social values. That is a nice historical pressure: the scenario's political deterioration is now mechanically affecting me before the famous Yellow Turban revolt.

83. `policy` is unusually honest about automation: **“None of them looks ahead, knows what you are building towards, or is trying to win.”** I like this. It frames automation as typing reduction rather than a hidden AI that might invalidate strategic play.

84. I am enabling only `auto_hire`, mainly to replace trained trades when people die. I am deliberately leaving auto-open, auto-train, auto-commission, etc. off so the important strategic choices remain manual.

85. Completing arrival orientation + respectable cover increased the victory-road count from 21 to 22 and expanded the visible/startable space considerably. I had assumed these were mostly social-safety projects; at least one is materially relevant to the technical route.

86. Fog now exposes `logarithms` and `com_binary_arithmetic` (the latter blocked by `com_boolean_algebra`). These are plausible foundations for later physics/computation, so I am treating them as more promising than the many unrelated agriculture/household nodes now visible.

87. Boolean algebra is directly available and explicitly links mathematical logic to switching circuits. Its description is clear and surprisingly modern, but relevant to the target. I expect it to unlock binary arithmetic and later computing/electronics design.

88. Multiple heard-of nodes are blocked because engineers and chemists do not exist in this society. Since the UI repeatedly points to `train engineer 2` and `train chemist 2`, creating these trades now feels like a high-confidence infrastructure investment rather than blind branching.

89. **130-132 AD — The engineer/chemist push unlocked exactly the sort of things I hoped for, but the payroll explosion was brutal.** I started `Binary arithmetic - base-2 number system`, `Control chart`, `Sampling inspection`, and `Friction matches: red phosphorus safety match`. All four completed by 131. Sampling inspection failed once first, then succeeded. That felt like good forward motion: binary arithmetic is a natural electronics foundation, and statistical process control is exactly the sort of thing I expect semiconductor fabrication to need.

90. **The game made the staffing consequence much larger than I anticipated.** At 132, `state` says: **"EMPLOY: 8 people, 2,674 cash/yr in wages"** and **"household places: 8.0 of 8.0 used"**. I had intended to create access to engineers and chemists, not permanently fill my entire household with them. Because `auto_hire` is on, I suspect it is maintaining/growing those trained trades more aggressively than I understood. I feel punished for a policy choice I made for convenience, but the state screen is at least very explicit about the damage.

91. **The economy flipped from healthy to dangerous in only two years.** Cash fell from about 3,077 to **-972**, with recurring net **-848/year**. This is the first time since the phosphorus rescue that I feel I could genuinely lose the run through bad management rather than bad luck. I expected specialist wages to hurt; I did not expect them to erase a +200-ish surplus and then some so quickly.

92. **Binary arithmetic did not immediately reveal an obvious transistor/electrical successor in the visible precision list.** I had expected a gratifying new electronics breadcrumb. Instead, the visible `power and precision` list is still mostly fuels and workshop joining/finishing methods. That is not necessarily wrong, but it makes the reward for Boolean + binary feel abstract so far.

93. **Case hardening, thermometer, and the school are still blocked by totally unknown prerequisites.** The game repeats variants of **"this needs 1 other thing you have not heard of yet"** or **"2 other things"**. At this point I am feeling the intended fog-of-war tension, but also some frustration: I have built plausible prerequisites in metallurgy, printing, measurement, math, and institutions and cannot yet tell which direction is productive. I am resisting the urge to inspect the tree because a real blind player cannot.

94. **Turning `auto_hire` off and firing the surplus specialists immediately fixed the economic crisis.** I kept one chemist and one engineer, fired three chemists and two engineers, and recurring net jumped from -848/year to about **+940/year**. The policy text deserves credit for saying: **"Turn one on when the tedium is worse than the mistakes; turn it off the moment it does something you would not have done."** That is unusually honest UI copy, and I followed it literally.

95. **The staff abstraction finally clicked, but only after I made an expensive mistake.** `ventures` says: **"Engineers, chemists and machinists are scholars here, and a scholar cannot watch a workshop."** I had mentally treated engineers as craftspeople because that is how I think of them historically/industrially. The game does explain its abstraction, but not before the player can easily overhire the wrong category.

96. **I tried to turn matches into a rescue/diversification business and missed the supervision requirement by 0.20 craftsmen.** The refusal said it needed **1.33 craftsmen** and I had **1.13 free**. This was frustrating but fair: the error is exact and tells me the remedy. I decided not to chase that last fraction immediately because the corpus is nearly complete.

97. **The corpus still had not produced any hedge by 134 AD.** `risk` still says **"hedge: nothing yet"**, even though all founder-hours are complete and only 138.6 cash remains to trickle into it. This reinforces that a nearly finished safety project gives zero protection until full completion; I am now anxious to see whether completion materially changes the hazard readout.

98. **135 AD — The corpus finally paid off, and the feedback is excellent.** The moment it completed, `state` changed from **"hedged by nothing yet"** to **"hedged by corpus_written"**. `risk` quantified the benefit: chance lost if sacked fell from **80% to 45%**, and fraction lost from **40% to 22%**. This is exactly the kind of consequence feedback I want from a complex strategy game: I can see that the investment mattered.

99. **The corpus completion also leaked internal-looking society variables again:** **"changes the society: literacy_elite, w_magic_fear"**. I understand the mechanical intent, but variable-style names are much less immersive and much less interpretable than the otherwise strong prose.

100. **`stuck` was not strategically useful at this point.** It told me I had 343 startable things, named the cheapest, and reminded me that matches is a profitable unopened concern. That is correct operational advice, but it does not answer my real first-time-player problem: which of hundreds of plausible technologies is likely to expose the hidden prerequisites on the transistor path?

101. **`available sort nearest` is also hard to interpret.** The first 25 entries were almost entirely agriculture (chaff cutter, cheese families, composting, etc.) despite my transistor goal. If "nearest" means nearest to the goal, I expected precision, chemistry, electrical, or institutional nodes. If it means something else, the UI did not tell me. This is now one of the stronger navigation/friction issues in the run.

102. **I learned that some completed capabilities must also be kept open for their enabling effects.** The corpus `why` page says: **"KEEP THIS OPEN: yes"** and warns that **"a future start it clears all stop the moment you close it"**. This was not how I had mentally modeled completed techs. I opened both the corpus and identity cover, accepting 800/year combined upkeep. This is a powerful rule that could easily be missed because most completed technologies are permanent knowledge.

103. **The town patron turned out to be a major progression node, not mere roleplay.** Its page says **"HOW MUCH RESTS ON THIS: almost everything"** and describes an entry gift of reading lenses to an ageing magistrate. I started it even though it pushed me briefly onto credit. It completed in 135 and raised my road-to-goal count from 22 to 23.

104. **Most importantly, the patron caused the hidden case-hardening prerequisite to become named:** `available find case` now says **"case_hardening missing prerequisites: workshop_first"**. This was a genuine 'aha' moment. I had spent years probing metallurgy when the actual gate was social/workshop establishment. It feels plausible in-world, but the prior opacity made it hard to reason toward.

105. **Protection rose from 10% to 22% around the patron completion, which felt rewarding, though I am not yet sure whether the completed patron, the open identity, or another standing effect caused the exact jump.** I will avoid inventing causality the UI has not stated.

106. **136-138 AD — The first workshop was an enormous debt-financed commitment, but it cracked two major progression walls at once.** It cost about 5,214 cash and put me roughly 4,293 in debt after two years. I felt genuinely nervous taking that much credit, but recurring cash stayed positive because matches was ramping.

107. **The workshop made case hardening directly startable.** This is the clearest confirmation yet that my early assumption—"case hardening must be behind another metallurgy invention"—was wrong. The missing prerequisite was literally **"First workshop and laboratory"**, which itself required a patron. The chain is socially and institutionally plausible, but a blind player has almost no way to infer it from the name `case_hardening` alone.

108. **The workshop also revealed the school prerequisites by name:** `school_founded missing prerequisites: collegium_licensed, freedman_staff`. This was a big moment because I had spent years trying printing/paper/institutional guesses. I now finally have actionable targets instead of "2 other things you have not heard of yet".

109. **Opening matches helped, but the ledger showed its three-year ramp rather than instantly printing the quoted 2,000/year.** The game says: **"STILL BUILDING UP: chm_matches at 33% of full takings."** I like this; it prevents a completed business from becoming an instant magical cash faucet and makes timing matter.

110. **Case hardening completed cleanly and advanced the goal path to 25 nodes.** Its description is one of the better historical/technical explanations so far: the game acknowledges that smiths already know hardening, but frames my contribution as standardizing temper colors and reject rates. That feels much more believable than pretending I invented quenching from scratch.

111. **The precision chain is finally actionable rather than mysterious.** `precision_three_plate` now says the only problem is that **"there is not one [machinist] left here to do it"** and explicitly suggests `train machinist 2`. I like this failure state because it tells me both the strategic blocker and the command to solve it.

112. **The school route looks economically brutal.** `freedman_staff` costs about 9,056 cash, takes two years, and costs 1,400/year to keep open; it grants +8 artisans. `collegium_licensed` costs another 2,318 and 400/year and itself requires `citizenship`. Given my current -2,573 cash, forcing the school now would be reckless. I am prioritizing precision and income first.

113. **The game’s institutional logic is growing on me even though discovery was frustrating.** A patron -> legal workshop -> standardized heat treatment is a coherent historical chain, and a licensed teaching guild requiring citizenship also makes sense. The problem is less the chain itself than how little clue the player has before the fog reveals the names.

114. **142-145 AD — Retraining machinists unlocked three-plate flatness, and this felt like a clean, understandable progression.** I trained two machinists, waited for them to qualify, and completed `True plane surfaces by the three-plate method`. The road count advanced to 26.

115. **There was a timing oddity that initially looked contradictory but resolved itself.** I started three-plate at 142 and the game warned: **"this society can field 0 at most"** machinist hours and **"this project cannot progress at all until someone is"** trained. In the same yearly transition, the two machinists finished training and the project then completed in 143. The warning was technically accurate at the instant I started it, but because training was due that year it sounded more dire than the actual situation.

116. **The analytical balance now has named blockers: `cap_tol_100um` and `cementation_steel`.** This is much more satisfying than unnamed fog. I can infer that one is a tolerance/manufacturing capability and one is better steel, so both make conceptual sense for a precision balance.

117. **My economy recovered quickly once I stopped overhiring.** By 145 I was back to about 950 cash with +1,265/year recurring despite maintaining corpus, identity, patron, and several concerns. This makes the earlier debt feel survivable rather than arbitrary.

118. **150 AD — Fireclay refractories completed and cleanly revealed the last hidden cementation prerequisite: `cap_heat_1100`.** This was satisfying because the chain now reads like an actual industrial dependency: refractory materials first, then sustained high heat, then cementation steel.

119. **The fireclay project itself advanced the road count from 27 to 28.** That reassures me that these foundational workshop capabilities really are on the intended transistor route rather than me merely building plausible-looking industrial trivia.

120. **I made the required manual 150 AD save successfully:** `saved: manual_150.json`. The relative-filename rule is now understood.

121. **By 150 the economy had become healthy again:** about 6,679 cash and +1,605/year recurring. The matches concern is now a major contributor, and the earlier debt-financed workshop gamble looks like it paid off. I feel much more comfortable financing the next steel step.

122. **152-155 AD — Cementation steel succeeded on the first try.** Given the 20% failure risk and 3,200-loss penalty, I felt genuine relief. The road count moved to 30, so the expensive steel branch was unquestionably on-path.

123. **A patron succession event added welcome instability:** **"your patron dies; his heir must be courted afresh. The courting cost 600 cash, your protection falls from 35% to 21%, and you are talked about (scandal +4)"**. This is a good consequence of relying on personal patronage: the relationship is not an immortal buff just because I am immortal.

124. **The analytical balance is now blocked only by staffing, not technology:** it needs two scholars and I have one (myself). This feels good because the game explicitly tells me the remedy: hire another scholar or build the school/collegium ecosystem.

125. **The next instrument clues are coherent:** thermometer now names `glass_labware` plus one unknown prerequisite; spectroscope names `balance_analytical`, `cap_tol_10um`, plus one unknown. This is the kind of fog progression I find motivating: each completed foundation turns mysteries into concrete engineering problems.

126. **158 AD — The precision and glass branches are now clearly visible.** Clear glass is directly startable but costs about 8,480 cash; micrometer gauges are blocked only by `master_screw`. I like having two concrete engineering options instead of opaque fog.

127. **The clear-glass description is particularly good historical writing.** It says near-colourless glass and manganese decolourising are already known where glass industry exists; what I add is deliberate control of sand purity, weighed manganese dose, and annealing. This preserves the competence of historical craftspeople instead of making the player a lone genius teaching everyone obvious things.

128. **The game continues to make industrial scale expensive in a believable way.** Clear glass wants huge charcoal and quartz quantities and 3 artisans just to develop. The cost feels like building supply chains, not paying arbitrary research points.

129. **161-164 AD — Opening cementation steel transformed the economy.** It is currently earning about 5,933/year against 1,350 upkeep, and total recurring net jumped to about **+5,193/year**. This feels like the point where the run stops being hand-to-mouth and becomes an industrial programme. The high capital cost was justified by the scale of the business.

130. **The master screw failed once, then succeeded on attempt two.** The first failure cost about 1,107 cash. Because the page had clearly advertised 35% failure risk, I was annoyed but not surprised; this is a failure I accept as game tension rather than UI unfairness.

131. **Master screw immediately made micrometer gauges startable and revealed another named blocker for 10-micron tolerance: `screw_lathe`.** This is excellent progression feedback: the result creates a new tool I understand and points to the next machine I need.

132. **Printing press completed, but did not directly remove the school prerequisites.** It changed society values/literacy and is potentially profitable, so I still think it was strategically reasonable, but my expectation that it might unlock school legality was wrong. The school remains a citizenship/legal/staff institution problem.

133. **Citizenship failed its first attempt in 163.** The event says **"Legal standing: a status the courts will hear: it did not work"**, losing 1,800 cash and 40% of hours to redo. This is one of those abstractions that is mechanically clear but narratively funny: apparently my bid for recognized legal status was rejected and must be retried.

134. **164-167 AD — Running steel now lets me finance multiple strategic branches at once.** I started micrometer gauges and clear glass while citizenship was retrying. This would have been suicidal twenty years ago; now it feels like the reward for building a serious productive base.

135. **Clear glass failed its first attempt, costing 3,381 cash.** Again, the 20% failure risk was visible in advance, so the loss hurt without feeling deceptive. The project is already on attempt two and waiting on the calendar.

136. **Micrometer gauges succeeded and reduced 10-micron tolerance to one named blocker: `screw_lathe`.** Looking up screw lathe revealed four prerequisites: `crucible_steel`, `prc_change_gears_quadrant`, `prc_slide_rest_simple`, and `water_power_scale`. That is a daunting but intelligible machine-tool programme.

137. **Citizenship succeeded on attempt two in 166, making `collegium_licensed` startable.** This is now urgent for reasons beyond scholar supply: the risk screen explicitly told me a school helps against the 184-205 Yellow Turban sacking window.

138. **Protection has risen substantially, to 47% by 167, while the patron/citizenship infrastructure matures.** I like that social investments have visible strategic value beyond being arbitrary prerequisites.

139. **167-170 AD — The pre-Yellow-Turban institution build came together faster than I expected.** `collegium_licensed`, clear glass, and `freedman_staff` all completed by 168. Opening the collegium and freed staff immediately made `school_founded` startable.

140. **`freedman_staff` has a huge concrete capacity effect.** After completion, my effective craft-hand count jumped to **14**, despite only six actual people on payroll. This is a little abstract to read in `state`, but strategically it is enormous: the institution grants the trained artisan capacity promised in its description.

141. **The risk screen at 170 now offers `corpus_dispersed` directly as a Yellow Turban mitigation.** It describes it as **"a step toward the work is in too many places to burn"**. That is a strong, evocative objective. I want it, but I am prioritizing the school first because it is both a hazard hedge and the scholar-capacity bottleneck for quantum solid-state theory.

142. **Clear glass succeeded on attempt two.** I had expected the glass branch to be one of Han's biggest disadvantages from the civilization intro; overcoming it feels like a meaningful milestone, and `glass_labware` is now directly startable.

143. **The school is now a concrete race against history rather than a vague long-term goal.** It costs 8,625, takes four years, and the Yellow Turban rebellion begins in 184. Starting in 170 gives a comfortable buffer unless it fails repeatedly.

144. **174-175 AD — Opening the school materially changes the scale of play.** Its page says it grants +4 scholars and +2 scholars/year thereafter, and after opening it my household capacity rose to 25.4 and I gained deputy founder-hours. This is exactly the compounding institution I was hoping for.

145. **The school did not directly reduce the displayed Yellow Turban sack chance.** `risk` still showed 20% annual sack chance. So my earlier assumption that “school_founded is one mitigation” meant a direct percentage reduction was too simple; its benefit may instead operate through staff/knowledge resilience or a downstream structure. I am logging the mismatch rather than guessing.

146. **The dispersed corpus is now running toward an eight-year calendar floor.** The risk screen explicitly recognizes it as **"already active"**, but the sack chance remains 20% until completion. This mirrors the earlier corpus behavior: partial progress is strategically real to me, but mechanically gives no finished hedge yet.

147. **I corrected the manual-save timing mistake.** `manual_175_actual.json` was saved at year 175. The earlier file named `manual_175.json` was actually created at 174 and should not be treated as the checkpoint.

148. **By 175 the run feels substantially easier than the opening—not because the tech tree became simple, but because institutions and steel created compounding capacity.** I now have cash, scholar capacity, artisan capacity, and extra founder-hours. This may explain why some players call the game easy once the economic/institutional flywheel is discovered.

149. **175-178 AD — Slide rest, lab glassware, and scaled water power all completed successfully, raising the road count from 34 to 37.** This was one of the most satisfying batches so far because each result was something I had deliberately predicted as a machine-tool/instrument prerequisite.

150. **The school produced a concrete social event:** **"a generation of schooling shows in the census: general reading is now 16% of the population"**. I loved this. Instead of only saying literacy_general changed, the game translated the institution into a comprehensible human outcome.

151. **The institution flywheel is now obvious.** Founder capacity has risen to about 2,418 hours/year thanks to deputies, household space is 28.7, cash is over 30,000, and recurring net is +7,560/year. This is the strongest evidence so far for the 'game becomes easy after compounding' argument: once the school/steel economy is established, constraints loosen very rapidly.

152. **The thermometer remains blocked by one completely unknown prerequisite even after clear glass and labware.** This is frustrating because those are the two prerequisites I would most naturally expect. I am deliberately not looking behind the curtain; the remaining mystery is therefore a real discoverability problem from my perspective.

153. **Coal/coke has emerged as the core heavy-industry blocker.** `coal_coke` now says it requires `charcoal_industrial`, and crucible steel still requires coke plus one unknown. The Yellow Turban risk screen independently recommends industrial charcoal as a step toward corned powder, so this looks like a strategically elegant two-for-one investment.

154. **181-184 AD — The dispersed corpus completed just before the Yellow Turban window and massively improved resilience.** `risk` now says **"chance lost if a site is sacked: 12%"** and **"fraction lost when it happens: 8%"**, versus 45% / 22% with only the written corpus. This is an excellent, legible payoff for long-term defensive planning.

155. **The Yellow Turban rebellion is now actively happening.** The state line says **"HAPPENING NOW: Yellow Turban rebellion"**. I feel meaningfully more exposed even though my economy is strong, because a 20% annual sack roll is now live and 24 technologies are at risk.

156. **Coke failed on its first attempt in 183**, losing about 2,697 cash and 40% of the hours. With the rebellion starting immediately afterward, the failure felt much more consequential than earlier workshop failures: it delays the machine-tool route at exactly the moment historical instability becomes dangerous.

157. **Water power already softened the future Three Kingdoms economic shock.** The risk screen says output exposure would be **80%** and explicitly attributes that to **"power that does not come by ship"**. I like this kind of cross-cutting resilience: a technology chosen for machine tools also reduces geopolitical fragility.

158. **185-186 AD — I tried to infer the thermometer's mystery prerequisite the way a real player would.** I searched for `mercury`, `temperature`, `boiling`, and `fixed`. Mercury exposed amalgamation/barometer-related items, temperature exposed austenitizing and work hardening, but none revealed the missing thermometer prerequisite. This is useful evidence: even with reasonable domain knowledge, the intended node is not obvious from the UI.

159. **Coke is creating an awkward calendar-wait experience after failure.** At 185 and again 186 it showed 100% of hours spent and 0 owed, but **"waiting on the calendar"**. I understand that the three-year floor appears to reset/reapply on an attempt, but the state view does not tell me the exact completion year, so I am repeatedly checking it one year at a time.

160. **187 -> 188 AD: Yellow Turban sack finally lands, and the corpus messaging contradicts itself.** The event said: **"Yellow Turban rebellion: a site is sacked - 40,256 taken, 6.8 of your people gone, 2 projects back to the beginning"** and then **"KNOWLEDGE LOST: 4 technologies forgotten - charcoal_industrial, chm_matches, com_boolean_algebra, mt2_austenitizing (the corpus was never printed and dispersed)"**. This was painful but survivable: cash fell from 59,093 to 26,758 and the road-to-goal count fell from 39 to 38. What confuses me is the parenthetical. I *did* complete the dispersed-corpus project, and immediately before this the state/risk UI said knowledge was **"hedged by corpus_dispersed"** with much smaller loss probabilities. I expected either no contradiction, or wording like "despite the dispersed corpus, four technologies were lost." Saying it "was never printed and dispersed" makes me question whether the project actually worked, whether I was supposed to open something afterward, or whether this is stale/incorrect event text.

161. **Coke failure/attempt messaging remains hard to interpret.** Before the sack, coke had already failed once. In 186 the game again said **"FAILED at Coal, and coking it ... Attempt 2"**, and after the next year it is back at 100% hours and **"waiting on the calendar"**. I expected a retry counter that unambiguously increments (Attempt 2, then Attempt 3) and/or an explicit next resolution year. As shown, I cannot tell whether "Attempt 2" means the failed attempt was number 2, the *next* attempt is number 2, or the label simply failed to advance.

162. **The sack makes the preservation system feel consequential rather than cosmetic.** Losing industrial charcoal in particular hurts because it was a ~30,000-cash industrial foundation I had intentionally built both for metallurgy and resilience. The fact that history can erase part of a carefully built route raises real strategic tension. I like that. The problem is not the loss itself; it is that the corpus UI and the event explanation disagree about why/how much protection I had.

163. **Opening `corpus_dispersed` does not visibly improve the hedge.** I opened it after the sack because its own page says **"KEEP THIS OPEN: yes"**, and the sack text claimed the corpus "was never printed and dispersed." Yet `risk` remains exactly **12% chance lost / 8% fraction lost**, the same figures it showed while the capability was closed. My expectation is that either (a) opening matters and the risk screen should show the extra effect, or (b) opening does not matter for preservation and the sack event should not imply that the dispersed corpus never existed. At present I cannot tell which model is intended.

164. **Recovery after a sack is mechanically interesting.** Lost knowledge is not permanently deleted from the tree: the game explicitly lists it under **"ALREADY LOST TO A SACKING"** and lets me rebuild it. Cheap conceptual knowledge (austenitizing) comes back quickly, while industrial charcoal again costs ~30,766 and is rate-limited over three years. This makes the *type* of knowledge lost matter, not just the count, which I like.

165. **The laboratory was a reasonable blind guess for crucible steel, but it did not reveal the missing prerequisite.** Its description is **"A working laboratory: retorts, baths, lutes, crucibles, fume management"** and says almost everything rests on it, so I expected it might gate controlled crucible work. It failed on the first attempt, which cost time/money, and crucible steel still says one unknown prerequisite. This is not necessarily bad design—the guess was mine—but it demonstrates how expensive fog-driven inference can be when a plausible prerequisite is wrong.

166. **`available find steel` gave a much better historical clue: `mat_blister_steel`.** Blister steel is startable for 0 cash, 40 founder-hours, one year. From real metallurgy, this immediately feels like the likely precursor: cementation makes blister steel, then crucible steel remelts selected blister steel to homogenize it. If that is the hidden gate, I will regard it as a strong, fair technology relationship even though the game did not name it initially.

167. **193 AD: a second Yellow Turban sack lands, but no technologies are forgotten.** Exact event: **"Yellow Turban rebellion: a site is sacked - 26,903 taken, 6.8 of your people gone, 2 projects back to the beginning"**. Unlike the 187 sack, there is no knowledge-loss line. This makes the 12%/8% dispersed-corpus hedge feel like it may in fact be functioning; the problem remains the contradictory first-sack wording, not necessarily the mechanics.

168. **Blister steel failed on attempt one, so my historical inference is still untested.** The failure costs no cash because the project itself costs 0, only 16 founder-hours of redo. I like that the failure system respects the project economics instead of inventing a monetary penalty.

169. **The furnace descriptions correctly stopped me from buying plausible-but-irrelevant infrastructure.** `met_reverberatory` says **"HOW MUCH RESTS ON THIS: nothing else; this is worth having for itself"**, and the cupola says the same. That is excellent UI. Both sounded physically plausible for crucible steel, but the game gave me enough information to avoid wasting years and money. This is exactly what I want `why` to do.

170. **A visible development-note leak breaks immersion.** The cupola furnace description ends with **"[FIXED after independent audit: it was tier 1 while depending on the blast furnace, which is a major independent metallurgical leap.]"** That reads like an internal patch/audit note rather than something meant for a player inside the game. The factual correction is welcome; the bracketed provenance should not be in normal-facing flavor text.

171. **`available sort nearest` does not behave like a win-condition planner.** At 196 AD, aiming at transistors with 41 road nodes built, `available sort nearest limit 25` returned 25 agriculture entries beginning with biological control, botanic garden, bottling, chaff cutter, cheese, composting, etc. I expected "nearest" to rank things by graph distance/relevance to my stated target. If it means nearest by some other metric, the UI does not explain it. This makes a potentially powerful navigation command actively misleading.

172. **`stuck` correctly reminded me that the printing press was finished but shut.** Opening it changes its economics to 3,400/year revenue against 1,500 upkeep and increased recurring net. This is useful operational advice and saved me from leaving a profitable capability idle. I would preserve this part of `stuck`.

173. **Porcelain/high-fired ceramic is the first ceramic candidate whose page actually looks like a plausible industrial gate.** Exact text: **"Kaolin plus feldspar at about 1300 C. Chemical ware, electrical insulators..."** and **"HOW MUCH RESTS ON THIS: a great deal."** Unlike stoneware, which explicitly says nothing else rests on it, this gives me a rational reason to invest. Given crucible steel's own statement that the vessel surviving extreme temperature is the hard part, I expect this to reveal either the missing prerequisite or a specialized refractory-vessel step.

174. **197 AD: third sack, still no knowledge loss.** Exact event: **"Yellow Turban rebellion: a site is sacked - 25,356 taken, 6.8 of your people gone, 1 project back to the beginning"**. The repeated financial/staff hits are substantial, but after the one 187 loss event, the last two sacks have spared knowledge. That makes the dispersed-corpus hedge feel strategically valuable even though it cannot prevent the site itself being hit.

175. **At 200 AD, crucible steel has become a discoverability wall.** Its description itself says the closed refractory crucible surviving 1600 C is the hard part. I have completed coke, cementation/blister steel, fireclay refractory grading, 1300 C blast, a working laboratory with crucibles, and porcelain/high-fired technical ceramics. I also searched the visible catalogue for silica, alumina, magnesia, kiln, refractory, vessel, 1600, and clay. It still says only **"this needs 1 other thing you have not heard of yet"**. I now understand the engineering problem but do not know what *game action* expresses the missing capability. This is exactly the point where I would want the game to give a slightly stronger breadcrumb rather than requiring vocabulary guessing.

176. **Porcelain was still worthwhile even though it was not the crucible key.** Completing it moved the transistor-road count from 41 to 42. That reassures me that physically sensible side-investments can contribute to the final programme even when my local prerequisite prediction is wrong.

177. **The documented `rush` command is refreshingly honest about its limitations.** After I discovered it through `help commands`, `rush limit:3` started nitre beds, analytic geometry, and tens-of-kW water power, then printed: **"`rush` is a rough rule of thumb, not a plan: it begins things in order of how much rests on them, with no idea what you are building toward... A careful player beats it."** I like this very much. It prevents the automation from masquerading as optimal AI and explains why its choices may not solve my specific transistor bottleneck.

178. **`nearest` and `rush` now clearly mean different things than 'closest to the target'.** `nearest` gave agriculture; `rush` gives high-dependency-count infrastructure. The latter explains itself, the former does not. `nearest` needs similarly explicit semantics.

179. **203 AD: another Yellow Turban sack hit during two major projects.** Exact event: **"Yellow Turban rebellion: a site is sacked - 42,233 taken, 6.9 of your people gone, 2 projects back to the beginning"**. Despite this, lens grinding completed in 203 and lead metallurgy in 204, leaving me only 633 cash in debt by 205 because recurring net has grown above 15,000/year. The hazard is brutal in absolute numbers but the mature economy can now absorb it. This is the clearest point where the run starts feeling easier after successful compounding.

180. **Lead metallurgy is an excellent cross-domain prerequisite.** Its description explicitly says it secures galena **"for the crystal detector"** while also enabling acid plumbing, cable sheathing and accumulators. That gave me a strong electronics reason to spend 42,658 even before mercury/thermometer needs were considered. This kind of multi-purpose industrial node makes the tree feel coherent.

181. **The first semiconductor device felt like a real milestone.** `galena_detector` describes itself as **"a working semiconductor device achievable in any pre-industrial economy"** and a proof-of-concept for the long programme. Completing it in 209 AD raised the road count. This is excellent pacing: the player gets a tangible semiconductor effect centuries before the final transistor, rather than only pushing abstract prerequisites.

182. **Staff attrition can knock you below an exact research threshold immediately.** I hired three scholars to bring effective scholars from 5 to 8, then lost one in the same year to **"death and to better offers"**, leaving 7. I hired a replacement. This makes the 8-scholar quantum requirement feel like an institution/staff-maintenance challenge rather than just a purchase, which I like, but it also means starting a project right at a threshold can be fragile.

183. **Sulfuric retort stalled at 99% on chemist availability despite no other project being active.** The state says it is **"waiting on nobody to do the work: chemist (wants 519 hours a year; the chemists here can supply 1243 but your other work has them booked)"**. I infer open concerns or other standing activity are consuming those trade-hours, but "other work" is vague. I expected the message to identify the main consumers or point me to a command that does.

184. **217-219 AD — Sulfuric acid finally completed, but the game distinguishes knowing the process from actually supplying the chemical.** The retort finished and raised the goal-road count from 55 to 56. However, nitric acid remained blocked with: **"this needs a sulfuric acid supply and you have none of the things that would serve: any of lead_chamber, chm_contact_sulfuric would do"**. I expected a completed sulfuric-acid process to satisfy “sulfuric acid supply”; instead the game wants a larger operating industrial process. This distinction is strategically interesting, but it should probably be more explicit before completion.

185. **The lead chamber created a real upstream-production problem instead of behaving like a checkbox.** While it was under construction, the game repeatedly warned: **"SHORT OF SALTPETRE: work running at 5% of plan"** and directly told me that `buy nitre 20000` would lay enough beds to produce 16 tonnes/year. I liked this a lot. The message identifies the missing commodity, quantifies the remedy, and ties it to physical production.

186. **220 AD — Three Kingdoms fragmentation hit hard but did not destroy the run.** Trade/output dropped to 68% of normal, softened because I had built non-shipping-dependent power. Recurring net fell from roughly +18k/year to about +7-9k/year. This is the first big historical event after Yellow Turbans where prior industrial choices visibly blunt macroeconomic damage.

187. **225 AD — Manual checkpoint saved successfully as `manual_225.json`.** I am still following the 25-year manual-save rule rather than trusting autosave.

188. **Lead chamber completion exposed another staffing trap: construction staff and operating supervision are very different.** It needed 5 artisans to build but **6 artisans to keep open**, while my existing concerns had essentially all craft supervision committed. I hired six artisans specifically to create operating headroom. The `why` page does explain this, but the difference is large enough that a first-time player can easily finish an expensive project and then discover they cannot use it.

189. **Opening the lead chamber immediately unlocked both nitric and hydrochloric acid as startable projects.** This was satisfying because the industrial-supply distinction finally paid off visibly. The lead chamber itself earns about 9,000/year against 5,500 upkeep in this run, so it is not only a prerequisite tax; it can plausibly sustain itself economically.


245. **Bulk steel turned into an upstream-resource problem, not just a purchase.** At 333 I finally committed about 1.885 million cash to bulk steel. The very next year the game said: “SHORT OF COAL: work running at 18% of plan” and told me I was about 20,754 tonnes/year short. I expected a giant capital project; I did not expect the market-capacity bottleneck to dominate progress immediately.

246. **The coal-shortage event is excellent feedback.** It gave the exact shortage, the exact commands to quote/buy a shaft, and warned that a shaft takes years to come into production. This made the industrial-scale constraint understandable rather than feeling like an arbitrary slowdown.

247. **Fixing coal revealed iron as the next bottleneck.** Once the coal shaft came online, bulk-steel throughput improved and the next message became: “SHORT OF IRON: work running at 24% of plan,” short about 15,338 tonnes/year. This layering felt realistic and satisfying.

248. **The mine purchase UI handled an unaffordable order well.** I tried to buy the full iron shaft while short of cash. The game refused without changing anything and told me to ask for what I could pay for or check the quote. I expected either debt or partial purchase; the clean refusal was safer and clearer.

249. **Bulk steel succeeded on the first attempt in 340 AD.** This was a huge relief after sinking nearly all available capital into the project and its coal/iron infrastructure. Road-to-goal count rose to 108.

250. **Idle mines are brutally expensive and the game communicates that well.** After bulk steel finished, the mine ledger showed about 103,000 cash/year in standing mine costs while only ~4% of coal capacity and ~1% of iron capacity were actually needed. The text explicitly warned: “One you no longer need is money going out for nothing.” I closed both shafts.

251. **Closing the coal and iron mines restored recurring profit from about +19k/year to +122k/year.** This was one of the strongest economy lessons of the run: extraction capacity is not a permanent unlock; it is infrastructure you actively carry and may need to mothball despite sunk cost.

252. **High-pressure steam became the first mandatory late-game diffusion wall.** It costs only about 90k, but has a 12-year calendar floor and 40% failure risk. By this point money is not the real resource; years are.

253. **Institution-building paid off visibly again in 345.** The game announced: “you now have 3 deputies directing work in your name: your year is 7,406 hours instead of 2,000.” This made the early school/academy strategy feel materially transformative.

254. **Manual save made at 350 AD.**

255. **High-pressure steam failed after its full twelve-year wait.** In 353: “FAILED at High pressure steam and adequate boilers: it did not work. 40% of the hours are to do again … Attempt 2.” The cash loss was minor at this point; losing the calendar time was crushing. I felt this much more strongly than losing hundreds of thousands of cash.

256. **The retry appears to require another diffusion wait.** After one year of rework the project returned to “waiting on the calendar.” I had initially assumed failure meant a modest rework delay. It can instead consume another large historical interval.

257. **Trying to solve gold/platinum through tiny mines exposed a unit-scale mismatch.** The final transistor needs tens of grams, so I commissioned 0.001-tonne/year gold and platinum workings. The mine summary rounded both to “CAN RAISE 0”, so they did not constitute meaningful supply.

258. **The platinum mine purchase output is internally inconsistent.** On purchase, platinum printed “ready year: None / years until producing: None”, while the immediately following mine summary said it was “ready 358.” This reproduced again with the larger platinum working.

259. **A one-tonne/year precious-metal mine is mechanically recognized by the mining system, even though the device needs grams.** I commissioned 1 t/year gold and platinum because the smaller realistic scale rounded away. This is an odd abstraction mismatch.

260. **A producing platinum mine still does not satisfy the glass-to-metal seal’s “platinum supply” requirement.** By 363 the mine ledger showed `platinum_g` able to raise 1 (tonne/year), yet `gp_glass_metal_seal` still said: “this needs a platinum supply and you have none of the things that would serve, and none of them is anything you have heard of yet.” I expected a producing platinum mine plus completed platinum-group extraction to count.

261. **High-pressure steam failed a second time in 362.** After another long retry, the same mandatory gate failed again. This is now the clearest evidence in my run that bad luck on high-risk diffusion gates can dominate otherwise strong play.

262. **The second steam failure is emotionally much worse than the first.** At this stage nearly every visible critical branch—dynamo, grid, industrial zinc, high vacuum, electropolishing—converges on steam/electric power. There is no satisfying strategic pivot; I simply have to retry and lose more calendar time.

263. **Attrition quietly closed interchangeable manufacture in 359.** The game said nobody was left to keep an eye on it, so the concern closed while knowledge remained. This is fair, but easy to miss because it happens amid yearly event text.

264. **Patron deaths remain disruptive but legible.** Another patron death in 357 dropped protection from 78% to 46% and added scandal. The protection later recovered, but the event still creates a short vulnerable period.

245. **Rebuilding bulk steel while AC was still running exposed a useful financing rule.** At 388 AD the game refused the steel rebuild even though I had substantial cash because the unpaid future bill of the AC project also counted against what I could raise. I expected cash-on-hand to be the main test; instead the project pipeline consumes financing capacity too.

246. **The second bulk-steel build completed despite a coal-shortage warning in the same year.** The first time through, coal/iron shortages materially slowed the project. On the rebuild, the game warned that work was at 18% of plan, then completed bulk steel anyway in 391. I found this inconsistent enough to notice, though it may be an event-order issue rather than a rules problem.

247. **Another Sixteen Kingdoms sack erased seven technologies in 392.** It took 314,395 cash, 37.3 people, reset one project, and forgot 4N purity, the Daniell cell, fused quartz, hydrochloric acid, the lead chamber, emission spectroscopy, and plague preparedness. The road count fell from 122 to 117. The dispersed corpus reduces the damage but absolutely does not make long-horizon sack risk negligible.

248. **AC motors/transformers succeeded in 397 after a long fully-paid calendar wait.** The completion felt especially good because it unlocked transformer/transmission/substation work with no new mystery prerequisites. This was the cleanest late-game cascade so far.

249. **The grid became a pure workforce-scale gate at 402.** Once substation, transformer, transmission, frequency standardisation and bulk steel were done, the only blocker was 200 trained craftsmen. This communicates the intended scale very well: the problem is no longer invention but industrial organisation.

250. **Hiring 150 artisans unexpectedly made the economy much richer.** After hiring to cross the 200-craftsman threshold, recurring net jumped to roughly +311,000/year rather than collapsing under wages. I expected a huge payroll burden; instead the larger workshop economy apparently scales revenue strongly. This may contribute to late-game economic snowballing.

251. **The 25-year power-grid project is now the main calendar clock.** It costs about 535k, needs 900 founder-hours, has a 25-year floor and 35% failure risk. The financial burden is trivial compared with current income; the danger is losing twenty-five years to failure.

252. **HCl rebuild revealed that losing a supply process can cascade through otherwise-known chemistry.** Hydrochloric acid could not be rebuilt until the lead chamber was rebuilt and opened to provide sulfuric-acid supply. I liked this distinction between remembered recipe and operating feedstock, although sack recovery becomes much deeper than simply re-clicking lost nodes.

253. **Very-high vacuum, fused quartz, diffusion pumps, and exhaust pinch-off are rebuilt/complete by 410.** These feel like concrete endgame progress. The vacuum-tube route is no longer broadly mysterious; its remaining visible problems are discharge/X-rays, getter, glass-metal seal, and one hidden item.

254. **The platinum-supply problem remains baffling.** Discharge/X-ray work and glass-metal seals still say I have no platinum supply even after platinum-group metallurgy and an actual producing platinum mine. The UI gives no visible bridge from “I possess platinum” to whatever resource state these nodes require.

255. **The getter path became fairly discoverable once AC machinery existed.** Rotating-field alternator -> induction heating -> getter is a coherent, understandable sequence. This is a good example of fog working well: each reasonable electrical milestone reveals the next practical requirement.

256. **GeCl4 purification eventually succeeded on the retry at 452 AD.** The first attempt had failed in 448, and the retry then spent several years fully worked and paid but still “waiting on the calendar.” This reinforces that late-game difficulty is mostly calendar-risk, not money.

257. **Germanium reduction revealed a new, chemically sensible hidden material gate: pure graphite.** After GeCl4 purification I expected reduction to start, but the game refused: “this needs a pure graphite supply and you have none of the things that would serve, and none of them is anything you have heard of yet.” The project description itself warned that the graphite boat must be purer than the product, so the requirement makes sense even though it appears very late.

258. **The pure-graphite path was inferable from physics once grid power existed.** The 3000 C capability explicitly said: “No chemical flame reaches here. Calcium carbide, ferroalloys, tungsten, artificial graphite, synthetic corundum.” This was a strong breadcrumb. I expected it to reveal artificial/high-purity graphite, and it did after completion.

259. **3000 C electric-arc heat failed once before succeeding.** Again the money loss was trivial; the five-year calendar retry was the real penalty. A simultaneous fire destroyed about 2.28 million cash and barely changed strategy, showing how dramatically late-game wealth has outgrown cash hazards.

260. **High purity graphite appeared immediately after 3000 C heat and made germanium reduction startable.** This was one of the better fog sequences: hidden material -> physically infer a heat capability -> build it -> exact material node becomes visible. The road-to-goal count reached 141.

261. **Germanium reduction succeeded at 471 AD.** The point-contact transistor then showed exactly one missing prerequisite: `vacuum_tube`. This was the clearest endgame milestone yet; the semiconductor-materials side was complete.

262. **Vacuum tube is now the sole transistor blocker, but platinum supply remains opaque.** Both `discharge_xray` and `gp_glass_metal_seal` say they need a platinum supply and that none of the valid sources are anything I have heard of. This persists despite completed platinum-group metallurgy and previous physical platinum mining attempts.

263. **A sensible precious-metal processing package did not expose platinum supply.** Fire assay, ore dressing, chemical leaching and electro-refining all completed by 475. The seal still gave the same “platinum supply” message. This is increasingly a discoverability failure, not merely an omitted obvious prerequisite.

264. **The bounty system again leaked hidden fog information.** `bounty vacuum_tube` revealed the still-hidden third prerequisite `in2_electron_source_cathode`, while normal `why in2_electron_source_cathode` refused because I had “never heard of any such thing.” The same UI surface therefore both protects and leaks fog depending on command.

265. **The built-in planning commands remain poor near the goal.** At 475, `stuck` said I could start 999 things and recommended the cheapest project / opening profitable concerns. `available sort nearest` still began with agriculture even though the point-contact transistor was blocked only by the vacuum tube. This is serious late-game navigation noise.

266. **`rush` is candidly goal-unaware and demonstrated that problem.** Used as a last-resort late-game probe, it started cementation steel, alcohol distillation, tungsten, sintering, and destructive distillation. Its own text says it has “no idea what you are building toward.” Tungsten may help the cathode branch, but the selection did not solve platinum and confirms rush is not a substitute for goal-path guidance.

267. **514 AD — The point-contact transistor exposed a historical/prerequisite contradiction.** Its own text says Bardeen and Brattain used **"POLYCRYSTALLINE germanium"** and that pulled crystals and zone refining did not yet exist, but its status still said I needed a semiconductor supplied by either `single_crystal` or `silicon_path`. I expected the 1947 device to be buildable from the germanium slab I had already purified. Instead I was forced into the later single-crystal manufacturing programme.

268. **Looking one layer ahead showed the final junction transistor itself is simple once the forced crystal branch is done.** `junction_transistor` requires only point-contact transistor, single crystal, and 10-micron tolerance. That made the extra single-crystal gate on the point-contact device feel even more consequential: it is not merely preparation for the final target; it blocks the historically earlier proof-of-concept too.

269. **A user hint about parallelism materially improved my play.** I had been treating a long calendar-floor project too much like "the active research" even when I had thousands of unused founder-hours and plenty of staff. After the hint I began deliberately running a portfolio of short enabling projects alongside long diffusion projects. This was probably the difference between finishing comfortably and risking the 600 AD horizon.

270. **514-516 AD — Parallel semiconductor-lab buildout worked extremely well.** While the 12-year arc-furnace clock ran, I simultaneously started controlled-atmosphere chamber, Czochralski puller, tin-mercury mirrors, interferometric length measurement, precision potentiometer, valve voltmeter, and optician training. Within two years five of those were complete. The road-to-goal count jumped from 152 to 157 without delaying the furnace.

271. **Optician training behaved clearly and usefully.** I could start the X-ray diffraction camera before the opticians finished, but the game warned it would make zero progress until someone was trained and would eventually be halted if I ignored the shortage. The warning was concrete and actionable rather than simply refusing the project.

272. **Interferometric length failed once, but parallelism made the failure almost harmless.** It blocked gauge blocks temporarily, yet semiconductor metrology and X-ray diffraction continued in parallel. This was a major contrast with my earlier serial play, where one failed long project could freeze the whole plan.

273. **Semiconductor metrology is an excellent late-game node.** Its text says **"You cannot purify what you cannot measure"**, and its requirements—electrical measurement, potentiometer comparison, high-impedance valve voltmeter, electromagnet, galvanometer, quantum theory and vacuum tube—made the laboratory feel like a coherent measurement system rather than a magic purity checkbox.

274. **Gauge blocks revealed chromium only after optical metrology was solved.** I expected gauge blocks to start once interferometric length was done; instead the game then told me I lacked chromium supply. The material requirement is reasonable, but it is another example where a prerequisite appears only after the previous fog layer clears. Parallel planning therefore requires some spare calendar for newly exposed materials.

275. **525 AD — Manual checkpoint saved correctly as `manual_525.json`.** I first attempted the save in 524 and explicitly did not count it, then saved again at the exact requested year.

276. **525 AD — Arc furnace and chromium failed in the same year.** Both projects had completed their work and money absorption before rolling failure. The furnace was especially painful because its calendar floor is 12 years. This reinforced that late-game difficulty is driven much more by calendar risk than by cash.

277. **Chromium failed repeatedly but eventually completed in 531.** Because it was cheap and short, repeated 30% failures were annoying rather than threatening. This is how project failure feels best: a setback the player can absorb rather than a decade-scale lottery.

278. **Gauge blocks completed in 532 and left zone refining as the only single-crystal prerequisite other than the arc furnace.** At this point the parallel strategy had done its job: all optics, metrology, crystal-growing apparatus and staffing were already prepared.

279. **The arc furnace failed again at 532 before finally succeeding in 540.** This was the second major furnace failure. Its own description says it provides high-purity graphite and ferroalloys and has a 12-year floor. Repeated failure here consumed a very large fraction of the remaining horizon despite no strategic mistake on my part.

280. **Rebuilding plague preparedness during the furnace wait was worthwhile near-term play.** The Hou Jing risk screen showed the coming 548-555 event could cause heavy staff loss. I rebuilt and opened `plague_preparedness` while waiting on the furnace instead of doing irrelevant science.

281. **Opening plague preparedness visibly improved the Hou Jing forecast.** Projected staff loss fell from about 11% to about 7%, with the risk screen explicitly adding **"a plan made before the plague"** to the mitigation list. This is a strong example of the history/risk system rewarding foresight.

282. **540 AD — Arc furnace finally succeeded.** Because the rest of the semiconductor laboratory was already built in parallel, I could start zone refining immediately rather than spending another decade discovering its prerequisites.

283. **Zone refining failed twice.** It has a six-year floor and 45% failure risk. The first failure came in 546, the second around 550. With the goal horizon approaching, these repeated unavoidable rolls became the central source of tension.

284. **550 AD — Manual checkpoint saved as `manual_550.json`.** I also proactively rebuilt the scholar/artisan buffer because attrition had brought the effective scholar count too close to the 25 required by single-crystal growth.

285. **551 AD — Hou Jing sack was enormous: 11,056,807 cash and about 48 people.** The corpus protected the critical technology base, but effective scholars fell to about 18.6. This would have blocked single-crystal growth even if zone refining completed the next year. I immediately hired 20 scholars and 35 artisans.

286. **The staffing rebuild after Hou Jing demonstrates why "soft" requirements matter.** There was no technology prerequisite saying "maintain 25 scholars next year," but without a large buffer the next critical project would have been delayed by a disaster or ordinary attrition. Staffing is as much part of the tech path as the formal graph.

287. **553 AD — Hou Jing staff-loss event showed the sanitation mitigation working exactly as advertised.** The event reported staff -7% and said it would have been -25% without boiled water, handwashing, clean wounds, germ knowledge, preparedness and resilient fields. This felt fair and satisfying: prior preparation had a legible payoff.

288. **Zone refining finally succeeded in 554.** That moved the road-to-goal count to 165 and made single-crystal growth directly startable. The entire remaining path was now three projects: single crystal, point-contact transistor, junction transistor.

289. **Single-crystal growth failed twice before succeeding in 567.** Each attempt had a five-year floor and 45% failure risk. By the second failure, the run still had enough time, but the remaining margin was no longer comfortable. This was the point where "too easy" felt least plausible to me.

290. **The forced single-crystal gate remained internally contradictory all the way through.** The `single_crystal` page itself says Teal and Little pulled the first germanium crystals in 1948, **"the year AFTER the point-contact device was demonstrated on ordinary polycrystalline material."** Yet the point-contact transistor could not start without single crystal. This directly contradicts the player-facing history and adds multiple high-risk projects to the mandatory path.

291. **567 AD — Single-crystal growth finally succeeded.** I felt genuine relief rather than triumph because repeated mandatory 45% rolls had consumed so much calendar. We still had 32 years, enough for the final two devices.

292. **571 AD — Point-contact transistor succeeded on its first attempt.** This was one of the most satisfying milestones in the whole run. The game had finally produced an actual working transistor, with 29 years remaining.

293. **The final junction-transistor page was pleasantly clean.** Requirements were exactly point-contact transistor, single crystal and 10-micron tolerance; no surprise material-supply or hidden institutional gate appeared at the last moment.

294. **575 AD — Manual checkpoint saved as `manual_575.json`.** The final project had one year of funding absorption left when I saved.

295. **575 AD — Grown and alloy junction transistors completed on the first attempt.** The run ended in 576 with the explicit message: **"goal reached: junction_transistor completed in 575 AD"**. I finished 25 years before the 600 AD horizon.

296. **Final state:** 217 things built by me, 137 inherited, all 168 nodes on the road to `junction_transistor` complete, about 9.85 million cash in hand, 65.4 people, reputation 50.2, and 18 concerns running.

297. **Difficulty verdict from this blind run: winnable, but not easy.** I won on my first full blind attempt as immortal Later Han with fog on and merchant-level starting income, but only after learning to parallelize, building a large institutional/economic base, surviving huge sacks, and absorbing repeated failures in high-pressure steam, arc furnace, zone refining and single-crystal growth. A more serial playstyle or a few additional bad rolls could easily have missed 600.

298. **The user hint about parallel research was probably decisive and points to a tutorial/UI weakness.** Once I understood that calendar floors do not mean "give this project all your attention," progress accelerated dramatically. The game shows free founder-hours, but it does not teach the player strongly enough to treat long projects as background clocks while building the next layers in parallel.
