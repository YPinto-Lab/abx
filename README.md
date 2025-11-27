# abx
Antibiotics sub-group 

Run the ciprofloxacin report
---------------------------

From the repository root you can run the report (produces per_subject_trends.pdf):

```bash
# use your project venv (recommended)
source .venv/bin/activate
python Trend_Graph.py

# or use the venv python directly
.venv/bin/python Trend_Graph.py
```

If you don't have a venv created, use your system python3 or install one via Homebrew:

```bash
# install python (Homebrew) if needed
brew install python

# create venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
