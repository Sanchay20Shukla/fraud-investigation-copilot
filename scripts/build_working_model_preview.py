"""Render the saved investigation's model drivers for GitHub reviewers."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
case = json.loads((ROOT/'reports/sample_investigation.json').read_text())
drivers = sorted(case['risk']['drivers'], key=lambda d: abs(d['shap_value']), reverse=True)[:8]
drivers.reverse()
plt.rcParams.update({'text.parse_math': False, 'font.family':'DejaVu Sans'})
fig, ax = plt.subplots(figsize=(12,6.5), facecolor='#f5f8fc')
ax.set_facecolor('#f5f8fc')
values = [d['shap_value'] for d in drivers]
ax.barh([d['feature'] for d in drivers], values, color=['#d65b65' if v>0 else '#258b8b' for v in values])
ax.axvline(0, color='#64748b', linewidth=1)
ax.set_xlabel('SHAP contribution to model log-odds (not percentage points)')
ax.set_title('Saved investigation: TXN_0000002\nEight largest model drivers by absolute contribution', loc='left', pad=20, fontsize=15, fontweight='bold')
ax.spines[['top','right']].set_visible(False)
fig.text(.03,.025,'Red increases the model estimate; teal decreases it. A high model score does not establish fraud.',fontsize=10)
fig.tight_layout(rect=[0,.06,1,1])
fig.savefig(ROOT/'reports/working_model_drivers.png',dpi=160)
print('Saved reports/working_model_drivers.png')
