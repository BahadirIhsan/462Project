"""Reproduces every number and figure in the final report (CMU data only; the demo database is never read).
  1) data_stats.py        dataset statistics
  2) run_all.py           C1 / C2 / drift / C3 replication / multi-entry fusion / operating points  -> results/results.json
  3) checkpoint.py        preprocessing checks and enrolment-rejection variant                       -> results/checkpoint.json
  4) final_experiments.py Siamese tuning + 5-fold cross-fitting, detector fusion, error analysis      -> results/final.json
Usage: python reproduce.py      (about 5-8 minutes on a laptop CPU)
"""
import os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
for script in ("data_stats.py", "run_all.py", "checkpoint.py", "final_experiments.py"):
    t = time.time()
    print(f"==> {script}", flush=True)
    subprocess.run([sys.executable, os.path.join(HERE, script)], cwd=HERE, check=True)
    print(f"    {script} finished in {time.time() - t:.0f} s", flush=True)
print("All results are in", os.path.join(HERE, "results"))
