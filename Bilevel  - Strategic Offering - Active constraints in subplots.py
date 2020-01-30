# -*- coding: utf-8 -*-
"""
Created on Thu Jan 16 09:34:27 2020

@author: emapr
"""
# This is based on the example Transmission Investment in section 6.2.4 of the book Complementarity Modeling in Energy Markets

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.cm as cm #For rainbow
import pickle

with open('points_dict.pkl', 'rb') as f:
    points = pickle.load(f)

cstr1=['u_min_g3','u_min_d1','u_min_d2','u_min_d3','y_min_l1','y_min_l2','y_min_l3']
cstr2=['u_max_g3','u_max_d1','u_max_d2','u_max_d3','y_max_l1','y_max_l2','y_max_l3']
#cstr1=['u_min_g3','u_max_g3','u_min_d1','u_max_d1','u_min_d2','u_max_d2','u_min_d3','u_max_d3','y_min_l1','y_max_l1','y_min_l2','y_max_l2','y_min_l3','y_max_l3']

#colors = cm.viridis(0,1,len(cstr))
x=[]
y=[]
fig, axes = plt.subplots(nrows=7, ncols=2, figsize=(32,50))

i=0
for ct in cstr1:
    del x[:]
    del y[:]
    for n in range (1,861):
        if points[n,ct]== 0:
            x.append(points[n,'P_g1'])
            y.append(points[n,'P_g2'])
    axes[i,0].set_title(ct)
    axes[i,0].plot(x,y,'o',markersize=2)
    axes[i,0].plot(8.86364,6.13636,'ro')
    axes[i,0].set_xlim(-1,21)
    axes[i,0].set_ylim(-1,11)
    axes[i,0].set_xlabel('P_g1')
    axes[i,0].set_ylabel('P_g2')
    i+=1

j=0
for ct in cstr2:
    del x[:]
    del y[:]
    for n in range (1,861):
        if points[n,ct]== 0:
            x.append(points[n,'P_g1'])
            y.append(points[n,'P_g2'])
    axes[j,1].set_title(ct)
    axes[j,1].plot(x,y,'o',markersize=2)
    axes[j,1].plot(8.86364,6.13636,'ro')
    axes[j,1].set_xlim(-1,21)
    axes[j,1].set_ylim(-1,11)
    axes[j,1].set_xlabel('P_g1')
    axes[j,1].set_ylabel('P_g2')
    j+=1

plt.savefig('Active constraints_sub')
print(points[861,'P_g1'],points[861,'P_g2'],points[861,'y_max_l2'])



