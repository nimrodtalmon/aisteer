# Steer

Keeping a living AI allocator on course with scarce human attention.
Research code for the "stirring" idea (collective control of a living agent),
instantiated on Ethereum's Deep Funding (GG24 round, 98 repositories).

## Layout
- `data/build_data.py` builds `data/gg24.json` from the public GG24 artifacts
  (github.com/davidgasquez/gg24-deepfunding-market-weights, phase 2): 98 repositories,
  41,418 pairwise comparisons by six LLM juror personas, Bradley-Terry scores per persona.
- `steer/sim.py` the simulation: world (projects, engine with blind spots, members,
  maintainers, flags, attention) and policies (open forum, panels, flag and sample,
  escalation; nudge vs multiplier answers).
- `experiments/run_all.py` frontier and steering experiments in four worlds
  (base, skewed, fewer blind spots, inflation in nudges); `steering_tuned.py` the
  equal-attention comparison with tuned steps; `check_props.py` numerical checks of
  Propositions 2 (agenda is not verdict; the inconsistent 3-project example).
- `results/*.json` outputs used in the report.
- `paper/` a LaTeX skeleton of the paper (main.tex, refs.bib with verified entries only, figures).
- `figures/` paper figures (`experiments/figures.py`).
- `web/brief/` the research brief: slides built by `web/brief/src/build.py` from `results/`
  (deck engine in `web/assets/`, from the zutot repo); served by the app at `/brief/`.
- `app/` the web app (Python standard library). Deployed at
  https://talmonlab.bgu.ac.il/steer/ from nimrodtalmon/talmonlab, folder server/steer
  (this folder is the source copy). The paper lives on Overleaf.

## Run
    python data/build_data.py <path to gg24-deepfunding-market-weights/data/phase_2>
    python experiments/run_all.py base          # ~2 min on 2 cores per world
    python experiments/steering_tuned.py base
    cd app && DATA=./data python server.py 5501   # then open http://127.0.0.1:5501/
