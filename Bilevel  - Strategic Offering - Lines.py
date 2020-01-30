# -*- coding: utf-8 -*-
"""
Created on Thu Jan 16 09:34:27 2020

@author: emapr
"""
# This is based on the example Transmission Investment in section 6.2.4 of the book Complementarity Modeling in Energy Markets

import gurobipy as gb
import pprint

print ("--- --- --- ---")

##### Creation of the model #####
def Bilevel_prob(data):
    
    generators = data['generators']		#index for conventional generators    
    demand = data['demand']                 #index for demand
    nodes = data['nodes']                 #index for nodes 	
    param = data['param']                #reference of single parameters 
    lines = data['lines']                 #index for lines
   
    # Model alias
    model_bilevel = gb.Model('bilevel')
    
#-------------------------------------------------------------------------------------------------------------------------------------------------------

    ##### Definition of the variables #####
    
    # Strategic price offer for generator 1 
    c_g1 = model_bilevel.addVar(lb=-gb.GRB.INFINITY, ub=gb.GRB.INFINITY, name='c_offer_g1')
        
    # Production of generators
    P_g = {}
    for g in generators:
        P_g[g] = model_bilevel.addVar(lb=data[g]['g_min'], ub=data[g]['g_max'], name='P_{}'.format(g))
        
    # Demand served
    P_d = {}
    for d in demand:
        P_d[d] = model_bilevel.addVar(lb=data[d]['d_min'], ub=data[d]['d_max'], name='P_{}'.format(d))
    
    # Angles of the buses
    theta = {}
    for i in nodes: 
        theta[i] = model_bilevel.addVar(lb=-gb.GRB.INFINITY, ub=gb.GRB.INFINITY, name='theta_{}'.format(i))
    
    # Duals of lower level
    alpha = {}
    for i in nodes: 
        alpha[i] = model_bilevel.addVar(lb=-gb.GRB.INFINITY, ub=gb.GRB.INFINITY, name='alpha_{}'.format(i))
    
    gamma = model_bilevel.addVar(lb=-gb.GRB.INFINITY, ub=gb.GRB.INFINITY,name='gamma')
    
    phi_min = {}
    for g in generators:
        phi_min[g] = model_bilevel.addVar(lb=0, ub=gb.GRB.INFINITY, name='phi_min_{}'.format(g))
    for d in demand:
        phi_min[d] = model_bilevel.addVar(lb=0, ub=gb.GRB.INFINITY, name='phi_min_{}'.format(d))
        
    phi_max = {}
    for g in generators:
        phi_max[g] = model_bilevel.addVar(lb=0, ub=gb.GRB.INFINITY, name='phi_max_{}'.format(g))
    for d in demand:
        phi_max[d] = model_bilevel.addVar(lb=0, ub=gb.GRB.INFINITY, name='phi_max_{}'.format(d))
        
    
    rho_min = {}
    for l in lines:
         rho_min[l] = model_bilevel.addVar(lb=0, ub=gb.GRB.INFINITY, name='rho_min_{}'.format(l))
            
    rho_max = {}
    for l in lines:
         rho_max[l] = model_bilevel.addVar(lb=0, ub=gb.GRB.INFINITY, name='rho_max_{}'.format(l))
            
    # Binaries for Fortuny-Amat McCarl Linearization of KKTs
    u_min = {}
    for g in generators:
        u_min[g] = model_bilevel.addVar(vtype='B', name='u_min_{}'.format(g))
    for d in demand:
        u_min[d] = model_bilevel.addVar(vtype='B', name='u_min_{}'.format(d))
        
    u_max = {}
    for g in generators:
        u_max[g] = model_bilevel.addVar(vtype='B', name='u_max_{}'.format(g))
    for d in demand:
        u_max[d] = model_bilevel.addVar(vtype='B', name='u_max_{}'.format(d))
            
    y_min = {}
    for l in lines:
            y_min[l] = model_bilevel.addVar(vtype='B', name='y_min_{}'.format(l))
            
    y_max = {}
    for l in lines:
            y_max[l] = model_bilevel.addVar(vtype='B', name='y_max_{}'.format(l))    
    
    # Update of the model with the variables
    model_bilevel.update()
    
#-------------------------------------------------------------------------------------------------------------------------------------------------------
    
    ##### Objective function #####
    
    # Set the objective of upper level problem: maximize the profit of g1, with linearization
    obj = gb.LinExpr()
    obj.add(gb.quicksum(data[g]['cost']*P_g[g]+data[g]['g_max']*phi_max[g] for g in generators))
    obj.add(-data['g1']['g_max']*phi_max['g1'])
    obj.add(gb.quicksum(-data[d]['cost']*P_d[d]+data[d]['d_max']*phi_max[d] for d in demand))
    obj.add(gb.quicksum(data[l]['lineCapacity']*(rho_min[l]+rho_max[l]) for l in lines))
    model_bilevel.setObjective(obj,gb.GRB.MINIMIZE)
    
#-------------------------------------------------------------------------------------------------------------------------------------------------------
    
    ##### Constraints #####
    
    # 1 - No upper level constraints
    
    # 2 - Lagrangian derivatives of lower level
    
    L_g={}
    for g in generators:
        if g=='g1': # For generator under study, consider bidding cost instead of operating cost
            L_g[g] = model_bilevel.addConstr(c_g1 - alpha[data[g]['node']] - phi_min[g] + phi_max[g],
                                        gb.GRB.EQUAL,0,name='L_P{}'.format(g))
        else:
            L_g[g] = model_bilevel.addConstr(data[g]['cost'] - alpha[data[g]['node']] - phi_min[g] + phi_max[g],
                                         gb.GRB.EQUAL,0,name='L_P{}'.format(g))
        
    L_d={}
    for d in demand:
        L_d[d] = model_bilevel.addConstr(-data[d]['cost'] + alpha[data[d]['node']] - phi_min[d] + phi_max[d],
                                         gb.GRB.EQUAL,0,name='L_P{}'.format(d))
             
    L_theta={}
    for i in nodes:
        expr = gb.LinExpr()
        for l in lines:
            if i==data[l]['from']:
                expr.add(data[l]['B']*(alpha[i]-alpha[data[l]['to']]-rho_min[l]+rho_max[l]))
            elif i==data[l]['to']:
                expr.add(data[l]['B']*(-alpha[data[l]['from']]+alpha[i]+rho_min[l]-rho_max[l]))
            else:
                pass
        if data[i]['ref']==1: # For slack bus, add Gamma
            expr.add(gamma)
        else:
            pass
        L_theta[i] = model_bilevel.addConstr(expr,gb.GRB.EQUAL,0,name='L_theta_{}'.format(i))       
  
    # 3 - Lower level constraints
    
    # Power balance
    P_balance = {}
    for i in nodes:
        f = gb.LinExpr()
        for l in lines:
            if i==data[l]['from']:
                f.add(data[l]['B']*(theta[i]-theta[data[l]['to']]))
            elif i==data[l]['to']:
                f.add(data[l]['B']*(theta[i]-theta[data[l]['from']]))
            else:
                pass
        P_balance[i] = model_bilevel.addConstr(gb.quicksum(P_g[g] for g in data[i]['generators']) 
                                               - gb.quicksum(P_d[d] for d in data[i]['demand']) 
                                               - f,
                                               gb.GRB.EQUAL,0,name='h1_P_balance({})'.format(i))
    
    # Constraint for the initialization of angles: angle at slack bus set to 0   
    for i in nodes:
        if data[i]['ref']==1:
            model_bilevel.addConstr(theta[i],gb.GRB.EQUAL,0,name='h2_Slack_bus')
        else:
            pass
        
    # Max power flow in the lines
    
    f_max_pos={}
    for l in lines:
	    f_max_pos[l]=model_bilevel.addConstr(data[l]['B']*(theta[data[l]['from']]-theta[data[l]['to']]),gb.GRB.LESS_EQUAL,data[l]['lineCapacity'],name='g6_Line_Capacity({})_pos'.format(l))

    f_max_neg={}
    for l in lines:
	    f_max_neg[l]=model_bilevel.addConstr(data[l]['B']*(theta[data[l]['from']]-theta[data[l]['to']]),gb.GRB.GREATER_EQUAL,-data[l]['lineCapacity'],name='g5_Line_Capacity({})_neg'.format(l))
    
    # 4 - Linearized complementarity constraints of lower level
    
    # g1
    M_g1_primal={}
    for g in generators:
        M_g1_primal[g]=model_bilevel.addConstr(P_g[g]-data[g]['g_min'], gb.GRB.LESS_EQUAL, 
                                            param['M'] * u_min[g], name='M_g1_primal_{}'.format(g))
    
    M_g1_dual={}
    for g in generators:
        M_g1_dual[g]=model_bilevel.addConstr(phi_min[g], gb.GRB.LESS_EQUAL, 
                                            param['M'] * (1-u_min[g]), name='M_g1_dual_{}'.format(g))
        
    # g2
    M_g2_primal={}
    for g in generators:
        M_g2_primal[g]=model_bilevel.addConstr(data[g]['g_max']-P_g[g], gb.GRB.LESS_EQUAL, 
                                            param['M'] * u_max[g], name='M_g2_primal_{}'.format(g))
    
    M_g2_dual={}
    for g in generators:
        M_g2_dual[g]=model_bilevel.addConstr(phi_max[g], gb.GRB.LESS_EQUAL, 
                                            param['M'] * (1-u_max[g]), name='M_g2_dual_{}'.format(g))
    
    # g3
    M_g3_primal={}
    for d in demand:
        M_g3_primal[d]=model_bilevel.addConstr(P_d[d]-data[d]['d_min'], gb.GRB.LESS_EQUAL, 
                                            param['M'] * u_min[d], name='M_g3_primal_{}'.format(d))
    
    M_g3_dual={}
    for d in demand:
        M_g3_dual[d]=model_bilevel.addConstr(phi_min[d], gb.GRB.LESS_EQUAL, 
                                            param['M'] * (1-u_min[d]), name='M_g3_dual_{}'.format(d))
    
    # g4
    M_g4_primal={}
    for d in demand:
        M_g4_primal[d]=model_bilevel.addConstr(-P_d[d]+data[d]['d_max'], gb.GRB.LESS_EQUAL, 
                                            param['M'] * u_max[d], name='M_g4_primal_{}'.format(d))
    
    M_g4_dual={}
    for d in demand:
        M_g4_dual[d]=model_bilevel.addConstr(phi_max[d], gb.GRB.LESS_EQUAL, 
                                            param['M'] * (1-u_max[d]), name='M_g4_dual_{}'.format(d))
        
    # g5
    M_g5_primal={}
    for l in lines:
        M_g5_primal[l]=model_bilevel.addConstr(data[l]['lineCapacity']+data[l]['B']*(theta[data[l]['from']]-theta[data[l]['to']]), gb.GRB.LESS_EQUAL, 
                                                param['M'] * y_min[l], name='M_g5_primal_({})'.format(l))
    
    M_g5_dual={}
    for l in lines:
        M_g5_dual[l]=model_bilevel.addConstr(rho_min[l], gb.GRB.LESS_EQUAL, 
                                                param['M'] * (1-y_min[l]), name='M_g5_dual_({})'.format(l))
            
    # g6
    M_g6_primal={}
    for l in lines:
        M_g6_primal[l]=model_bilevel.addConstr(data[l]['lineCapacity']-data[l]['B']*(theta[data[l]['from']]-theta[data[l]['to']]), gb.GRB.LESS_EQUAL, 
                                                param['M'] * y_max[l], name='M_g6_primal_({})'.format(l))
    
    M_g6_dual={}
    for l in lines:
        M_g6_dual[l]=model_bilevel.addConstr(rho_max[l], gb.GRB.LESS_EQUAL, 
                                                param['M'] * (1-y_max[l]), name='M_g6_dual_({})'.format(l))
    
#-------------------------------------------------------------------------------------------------------------------------------------------------------
    
    model_bilevel.update()    # update of the model with the constraints and objective function

    ##### Optimization and Results #####      
    
    model_bilevel.optimize()
    
    # Calculations

    #Results display
    
    model_bilevel.write('strategic_lines.lp')
    
    if model_bilevel.Status != 3:
#        solution_bilevel = {
#                'Production' : [P_g[g].x for g in generators],
#                'Consumption' : [P_d[d].x for d in demand],
#                'Prices': [alpha[i].x for i in nodes],
#                'Angles' : [theta[i].x for i in nodes],
#                'Upper-level obj. function' : model_bilevel.ObjVal,
#                }
#        return solution_bilevel
        for v in model_bilevel.getVars():
            print('%s %g' % (v.varName, v.x))
    else:
        pass
    
     
    
#-------------------------------------------------------------------------------------------------------------------------------------------------------

##### Definition of the dataset #####
    
def system_input():
    return {
    'generators' : ['g1', 'g2','g3'],
    'demand' : ['d1','d2','d3'],
    'nodes' : ['n1','n2','n3'],
    'lines': ['l1','l2','l3'],
    
    # Units: 
    # - Capacities in MW
    # - Energy costs in $/MWh
    # - Investment cost in $
    # - Susceptance in S
    
    'g1': {'node':'n1', 'g_min':0, 'g_max':20, 'cost':16},
    'g2': {'node':'n2', 'g_min':0, 'g_max':10,'cost':19},
    'g3': {'node':'n3', 'g_min':0, 'g_max':25,'cost':15},
    
    'd1' : {'node':'n1', 'd_min':0, 'd_max':5, 'cost':18},
    'd2' : {'node':'n2', 'd_min':0, 'd_max':20, 'cost':20},
    'd3' : {'node':'n3', 'd_min':0, 'd_max':15, 'cost':21},
    
    'n1' : {'generators':['g1'], 'demand':['d1'], 'ref' : 0},
    'n2' : {'generators':['g2'], 'demand':['d2'], 'ref' : 0},	
    'n3' : {'generators':['g3'], 'demand':['d3'], 'ref' : 1}, 

    'l1' : {'lineCapacity':5, 'B':100, 'from':'n1', 'to':'n2'},
    'l2' : {'lineCapacity':10, 'B':125, 'from':'n1', 'to':'n3'},
    'l3' : {'lineCapacity':10, 'B':150, 'from':'n2', 'to':'n3'},    

                   
    # Single parameters
    
    'param': {'M' : 1000} # Big M for Fortuny-Amat McCarl Linearization of KKTs
    
          } 
    
#-------------------------------------------------------------------------------------------------------------------------------------------------------
    
pp1 = pprint.PrettyPrinter(indent = 2, width = 50, depth = None)

bilevel_s= Bilevel_prob(system_input())
pp1.pprint(bilevel_s)
