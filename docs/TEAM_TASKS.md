# Team task assignment

Milestone 2 is due **Mon Nov 2, 11:59 PM**. Each person commits their own work from their own GitHub account, so the commit history shows who did what.

## Equal split: each person owns three sketches and their report sections

Each person owns one of the three coordinated interactive views (★). You **only edit your own files and report sections**, so nobody overwrites anyone else.

| | Zhangzhuoyue Shi (`troy-shi`) | Zihang Yu (`Zihangyu600`) | Yaxi Wang (`Wyxx0305`) |
|---|---|---|---|
| **Sketches (3 each)** | `storyboard.jpg`, `q7.jpg`, `intro.jpg` (station / port / level / connector explainer) | `q1.jpg`, `q2.jpg`, `q3.jpg` | `q4.jpg`, `q5.jpg`, `q6.jpg` |
| **Report sections you own** | §0 changes, §1 data, §2 storyboard, §3.7 Q7, §4–§8 | §3.1 Q1, §3.2 Q2, §3.3 Q3 | §3.4 Q4, §3.5 Q5, §3.6 Q6 |
| **Interactive view (M3)** | Q7 sliders + map + table ★ | Q2 linked map + dot plot ★ | Q5 dropdown + bars + heatmap ★ |
| **Static views (M3)** | intro section | Q1, Q3 | Q4, Q6 |
| **Shared final step** | export PDF + Brightspace submission | final read-through | final read-through |

Already done (Zhangzhuoyue Shi): data download and processing pipeline (`scripts/`), processed tables (`data/processed/`), M2 report draft, README, and repository setup.

## What "optimize your part" means

For each of your questions in `docs/M2_report.md` §3:

1. **Understand it.** Be able to explain, in your own words, the unit of observation, the transformation, and the main data finding for each question (e.g. Q3's bulk-entry dates, Q7's zero-share cutoffs). Instructors may ask in M3 or in the presentation.
2. **Draw the sketch** from the "Sketch: views and encodings" table. Change the design if you have a better idea, then update the spec table to match your sketch.
3. **Tighten the text.** Rewrite the question's section in your own words; cut anything you would not say yourself. Keep every number that comes from `docs/samples/` unchanged unless you re-run the scripts.
4. **Check the design rules** (§5): readable labels, consistent scales, missing data explicit, not color-only.
5. **Report your AI use** to Zhangzhuoyue (tool, what for), even if it is "none", so §8 is accurate.

Owner-specific notes:

- **Zihang (Q1–Q3):** Q2 is a core interaction. Make the count/rate toggle and the click-to-highlight link between map and dot plot obvious in the sketch. Q3 must show the bulk-date segment and the always-visible note **on the chart**; this was instructor feedback point 1.
- **Yaxi (Q4–Q6):** Q5 is a core interaction. Show the dropdown, the shared row order of bars and heatmap, and the fixed 0–100% scale. Q6 must use **shape + color** for metro/nonmetro, and both panels must use identical axes.
- **Zhangzhuoyue (storyboard, intro, Q7, §0–§2, §4–§8):** Q7 must show the rule, actual cutoff values, counter, reset, and caption next to the map and table; this was instructor feedback point 2. Shorten §1 if possible, and finalize §8 from everyone's input.

## Milestone 2 checklist

| # | Task | Owner | Due |
|---|---|---|---|
| 1 | Draw and commit your 3 sketches to `sketches/` | Everyone | Sun Nov 1 |
| 2 | Revise your own report sections (see above) and commit | Everyone | Sun Nov 1 |
| 3 | Send your AI-use note to Zhangzhuoyue | Zihang, Yaxi | Sun Nov 1 |
| 4 | Finalize §8 + README AI-use statement; remove "Draft" | Zhangzhuoyue | Mon Nov 2 |
| 5 | Final read-through of the whole report | Zihang, Yaxi | Mon Nov 2 noon |
| 6 | Export report to PDF, submit on Brightspace with the repo link | Zhangzhuoyue | Mon Nov 2 |

## How to draw a sketch

1. Open `docs/M2_report.md` §3 for your question. Draw what the **"Sketch: views and encodings"** table describes.
2. Hand-drawn (photo or scan) or Excalidraw/Figma are fine. **Do not use AI to generate the sketch.**
3. Before you save it, check the list in `sketches/README.md`: title, axis labels with units, legend (including zero / missing), interactions marked in a second color, the permanent note, and the source line.
4. Save it as JPG or PNG with the exact file name above. Keep each file under about 2 MB.

## How to commit your sketch (first time)

Accept the invitation first: https://github.com/troy-shi/gg-bond-ev-charging/invitations

```bash
git clone https://github.com/troy-shi/gg-bond-ev-charging.git
cd gg-bond-ev-charging
git config user.name "<your GitHub username>"
git config user.email "<an email verified on your GitHub account>"
# copy your sketch files into sketches/
git add sketches/q4.jpg sketches/q5.jpg sketches/q6.jpg
git commit -m "Add Q4-Q6 sketches"
git pull --rebase
git push
```

The `user.email` must be an email on **your own** GitHub account. Otherwise GitHub cannot link the commit to you.

When you edit the report, **run `git pull --rebase` first** and only change your own sections. Different sections of the same file merge cleanly, but the same lines do not. Commit report edits separately from sketches (e.g. `Revise Q4-Q6 sections`).
