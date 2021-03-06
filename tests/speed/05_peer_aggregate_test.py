#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copyright (c) 2018, Global Climate Forun e.V. (GCF)
http://www.globalclimateforum.org

This file is part of ABM4py.

ABM4py is free software: you can redistribute it and/or modify it 
under the terms of the GNU Lesser General Public License as published 
by the Free Software Foundation, version 3 only.

ABM4py is distributed in the hope that it will be useful, 
but WITHOUT ANY WARRANTY; without even the implied warranty of 
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the 
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License 
along with this program. If not, see <http://www.gnu.org/licenses/>. 
GNU Lesser General Public License version 3 (see the file LICENSE).

@author: ageiges
"""

#%% load modules

import numpy as np
import time
import random

from abm4py import World, Agent, Location #, GhostAgent, World,  h5py, MPI
from abm4py.future_traits import Aggregator


#import tools_for_02 as tools

#%% SETUP
EXTEND = 30
GRASS_PER_PATCH = 30
N_REPEAT = 30
#%% classes
#Patch = Location
class Patch(Aggregator, Location):
    def __init__(self, world, **kwAttr):
        #print(kwAttr['pos'])
       
        Location.__init__(self, world, **kwAttr) 
        Aggregator.__init__(self, world, **kwAttr) 
    
class Grass(Agent):

    def __init__(self, world, **kwAttr):
        #print(kwAttr['pos'])
        Location.__init__(self, world, **kwAttr) 

        
    def add(self, value):
        
        self.attr['height'] += value


    def grow(self):
        """        
        The function grow lets the grass grow by ten percent.
        If the grass height is smaller than 0.1, and a neighboring patch has 
        grass higher than 0.7, the grass grows by .05. Then it grows by 
        10 percent.
        """
                
        if self.attr['height'] < 0.1:
            for neigLoc in self.iterNeighborhood(ROOTS):
                if neigLoc.attr['height'] > 0.9:
                    self['height'] += 0.05
                    
                    if self['height'] > 0.1:
                        break
                    
        self['height'] = min(self['height']*1.1, 1.)
#%%
world = World(agentOutput=False,
                  maxNodes=100000,
                  maxLinks=1000000)

world.setParameter('extend', EXTEND)
#%% register a new agent type with four attributes
PATCH = world.registerAgentType(AgentClass=Patch,
                                agTypeStr='patch',
                                staticProperties  = [('coord', np.int16, 2)],
                                dynamicProperties = [('sumGrass', np.float64, 1)])


GRASS = world.registerAgentType(AgentClass=Grass,
                                agTypeStr='Grass',
                                staticProperties  = [('coord', np.int16, 2)],
                                dynamicProperties = [('height', np.float64, 1)])
#%% register a link type to connect agents

PATCHWORK = world.registerLinkType('patchwork',PATCH, PATCH, staticProperties=[('weig',np.float32,1)])

ROOTS     = world.registerLinkType('roots',PATCH, GRASS)
IDArray = np.zeros([EXTEND, EXTEND]) +1


world.registerGrid(PATCH, PATCHWORK)   
tt = time.time()
for x in range(EXTEND):
    for y in range(EXTEND):
        
        patch = Patch(world, 
                      coord=(x,y),
                      sumGrass=0)
        patch.register(world)
        
        IDArray[x,y] = patch.ID
        
        for i in range(GRASS_PER_PATCH):
            grass = Grass(world,
                          coord= (x,y),
                          height = random.random())
            grass.register(world)
            patch.addLink(grass.ID, ROOTS)
        
     
connBluePrint = world.grid.computeConnectionList(radius=4.5)
world.grid.connectNodes(IDArray, connBluePrint, PATCHWORK, Patch)
print('init Patches in: ' + str(time.time() - tt))


#%%
tt = time.time()
for i in range(N_REPEAT):
    x = list()
    for patch in world.getAgentsByType(PATCH):
        x.append(np.mean(patch.getAttrOfPeers('height', ROOTS)))
timeWithoutAggr = time.time() - tt 
print(timeWithoutAggr)


tt = time.time()
for i in range(N_REPEAT):
    x2 = list()
    
    for patch in world.getAgentsByType(PATCH):
        x2.append(np.mean([item['height'] for item in patch.aggegationDict[ROOTS]]))
timeWithAggr = time.time() - tt 

print(timeWithAggr)
print('Factor: ' + str(timeWithAggr / timeWithoutAggr ))


