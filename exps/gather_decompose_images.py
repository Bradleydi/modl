import os
from os.path import join
import json
import pandas as pd

from joblib import dump
import sys

import numpy as np

dir_name = os.path.dirname(os.path.realpath(sys.argv[0]))


import matplotlib.pyplot as plt
import seaborn.apionly as sns

from modl.utils.system import get_output_dir

idx = pd.IndexSlice

run_id = 23
run_dir = join(get_output_dir(), 'multi_decompose_images', str(run_id), 'run')
analysis_dir = join(get_output_dir(), 'multi_decompose_images', str(run_id), 'analysis')
if not os.path.exists(analysis_dir):
    os.makedirs(analysis_dir)

data = []
for this_dir in os.listdir(run_dir):
    this_dir = join(run_dir, this_dir)
    try:
        config = json.load(open(join(this_dir, 'config.json'), 'r'))
        info = json.load(open(join(this_dir, 'info.json'), 'r'))
    except FileNotFoundError:
        print('Skipping %s' % this_dir)
        continue
    method = config['method']
    step_size = config['step_size']
    reduction = config['reduction']
    score = info['score']
    time = info['time']
    data.append({'step_size': step_size,
                 'method': method,
                 'reduction': reduction,
                 'score': score,
                 'time': time})
data = pd.DataFrame(data)
data.set_index(['method', 'reduction', 'step_size'], inplace=True)
data.sort_index(inplace=True)
sgd_data = data.loc[['sgd']]
last_scores = []
for _, this_data in sgd_data.iterrows():
    last_score = this_data['score'][-1]
    last_scores.append(last_score)
last_scores = np.array(last_scores)
idxmin = np.argmin(last_scores)
sgd_data = sgd_data.iloc[[idxmin]]
print(idxmin)
var_data = data.query("method != 'sgd'")
data = pd.concat([sgd_data, var_data], axis=0)
data.reset_index(inplace=True)

data.to_csv(join(analysis_dir, 'data.csv'))
dump(data, join(analysis_dir, 'data.pkl'))
# Plot
fig, ax = plt.subplots(1, 1,
                       )
fig.subplots_adjust(left=0.15, right=0.97, top=0.97, bottom=0.2)

colormap = sns.cubehelix_palette(6, rot=0.3, light=0.85,
                                 reverse=False)
reductions = [1, 4, 6, 8, 12, 24]
ref_colormap = sns.cubehelix_palette(6, start=2, rot=0.2,
                                     light=0.7,
                                     reverse=False)
sgd_colormap = sns.cubehelix_palette(6, start=1, rot=0.2,
                                     light=0.7,
                                     reverse=False)
color_dict = {reduction: color for reduction, color in
              zip(reductions, colormap)}
color_dict[1] = ref_colormap[0]

for method, sub_data in data.groupby('method'):
    for _, this_data in sub_data.iterrows():
        if method == 'sgd':
            label = 'SGD (best step-size)'
            color = sgd_colormap[0]
        else:
            reduction = this_data['reduction']
            color = color_dict[reduction]
            if reduction == 1:
                label = 'Online matrix factorization'
            else:
                label = 'SOMF ($r = %i$)' % reduction
        time = np.array(this_data['time'])
        # Offset log
        time += 4
        ax.plot(this_data['time'], this_data['score'],
                label=label,
                color=color,
                linestyle='-')
ax.set_xscale('log')
ax.set_ylabel('Test objective value')
ax.yaxis.set_label_coords(-0.13, 0.38)
ax.set_xlabel('Time')
ax.ticklabel_format(axis='y', style='sci', scilimits=(-2, 2))
ax.legend(frameon=False, loc='upper right', bbox_to_anchor=(1., 1.))
sns.despine(fig, ax)
plt.savefig(join(analysis_dir, 'bench.pdf'))
plt.show()
