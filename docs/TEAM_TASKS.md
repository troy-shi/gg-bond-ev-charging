# Team task assignment

Milestone 2 is due **Mon Nov 2, 11:59 PM**. Each person commits their own work from their own GitHub account, so the commit history shows who did what.

## Question ownership (Milestone 2 sketches → Milestone 3 D3 views)

Each person owns one of the three coordinated interactive views (★) plus related static views.

| Member | GitHub | Owns | Interactive view |
|---|---|---|---|
| Zhangzhuoyue Shi | `troy-shi` | Storyboard, **Q7** | Q7 sliders + map + table ★ |
| Zihang Yu | `Zihangyu600` | **Q1, Q2, Q3** | Q2 linked map + dot plot ★ |
| Yaxi Wang | `Wyxx0305` | **Q4, Q5, Q6** | Q5 dropdown + bars + heatmap ★ |

Already done (Zhangzhuoyue Shi): data download and processing pipeline (`scripts/`), processed tables (`data/processed/`), M2 report draft (`docs/M2_report.md`), README, and repository setup.

## Milestone 2 checklist

| # | Task | Owner | Due |
|---|---|---|---|
| 1 | Sketch `storyboard.jpg` and `q7.jpg` | Zhangzhuoyue | Sun Nov 1 |
| 2 | Sketch `q1.jpg`, `q2.jpg`, `q3.jpg` | Zihang | Sun Nov 1 |
| 3 | Sketch `q4.jpg`, `q5.jpg`, `q6.jpg` | Yaxi | Sun Nov 1 |
| 4 | Read your questions' sections in `docs/M2_report.md` §3 and check that the sample tables and sketch specs match your sketch; fix or comment | Each owner | Sun Nov 1 |
| 5 | Finalize the AI-use statement (report §8 + README) with each member's actual AI use | Zhangzhuoyue (others report their use) | Mon Nov 2 |
| 6 | Final read-through, export the report to PDF, submit on Brightspace with the repo link | Zhangzhuoyue | Mon Nov 2 |

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

The `user.email` must be an email on **your own** GitHub account. Otherwise GitHub cannot link the commit to you. If you edit the report, commit that change separately (e.g. `Review Q5 section`).
