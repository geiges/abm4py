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

import numpy as np
import time
import random

from abm4py import World, Location, GhostLocation #, GhostAgent, World,  h5py, MPI
from abm4py.traits import Parallel
from abm4py.future_traits import Collective
from abm4py import core

import tools_for_05 as tools

#%% SETUP
EXTEND = 20
RADIUS = 1.5

#%% Class definition
class Grass(Location, Collective, Parallel):

    def __init__(self, world, **kwAttr):
        #print(kwAttr['pos'])
        Location.__init__(self, world, **kwAttr)
        Collective.__init__(self, world, **kwAttr)
        Parallel.__init__(self, world, **kwAttr)

    def __descriptor__():
        """
        This desriptor defines the agent attributes that are saved in the 
        agent._graph an can be shared/viewed by other agents and acessed via 
        the global scope of the world class.
        All static and dynamic attributes can be accessed by the agent by:
            1) agent.get('attrLabel') / agent.set('attrLabel', value)
            2) agent.attr['attrLabel']
            3) agent.attr['attrLabel']
        """
        classDesc = dict()
        classDesc['nameStr'] = 'Grass'
        # Static properites can be re-assigned during runtime, but the automatic
        # IO is only logging the initial state
        classDesc['staticProperties'] =  [('coord', np.int16, 2)]          
        # Dynamic properites can be re-assigned during runtime and are logged 
        # per defined time step intervall (see core.IO)
        classDesc['dynamicProperties'] = [('height', np.float32, 1)]     
        return classDesc
 
    def add(self, value):
        
        self.attr['height'] += value


    def grow(self):
        currHeight = self.attr['height']
        for neigLoc in self.getGridPeers():
            if neigLoc.attr['height'] > 2*currHeight:
                self.attr['height'] *= ((random.random()*.8)+1)
                break
        else:
            self.attr['height'] *= ((random.random()*.05)+1)

class GhostGrass(GhostLocation):   
    
    def __init__(self, world, **kwAttr):
        GhostLocation.__init__(self, world, **kwAttr)

    
#%% Init of world and register of agents and links
world = World(agentOutput=False,
              maxNodes=100000,
              maxLinks=200000)
print(world.isParallel)
print(core.mpiRank)
print(core.mpiSize)
rankIDLayer = np.zeros([EXTEND, EXTEND]).astype(int)
if world.isParallel:
    print('parallel mode')
    print(core.mpiRank)
    if core.mpiSize == 4:
    
        rankIDLayer[EXTEND//2:,:EXTEND//2] = 1
        rankIDLayer[:EXTEND//2,EXTEND//2:] = 2
        rankIDLayer[:EXTEND//2,:EXTEND//2:] = 3

    elif core.mpiSize == 2:
        rankIDLayer[EXTEND//2:,:] = 1
    print(rankIDLayer)
else:
    print('non-parallel mode')
    
world.setParameter('extend', EXTEND)
GRASS = world.registerAgentType(AgentClass=Grass, GhostAgentClass=GhostGrass)
                                
ROOTS = world.registerLinkType('roots',GRASS, GRASS, staticProperties=[('weig',np.float32,1)])

world.registerGrid(GRASS, ROOTS)
connBluePrint = world.grid.computeConnectionList(radius=RADIUS)
world.grid.init((rankIDLayer*0)+1, connBluePrint, Grass, rankIDLayer)

for grass in world.getAgentsByType(GRASS):

    if np.all(grass.attr['coord'] < 8):
        grass.attr['height'] = random.random()+ 13.1    
    else:
        grass.attr['height'] = random.random()+ 0.1


plott = tools.PlotClass(world, rankIDLayer)
    
while True:
    tt = time.time()
    [grass.grow() for grass in world.getAgentsByType(GRASS)]
    world.papi.updateGhostAgents(propertyList=['height'])
    print(str(time.time() -tt) + ' s')
    


    plott.update(world)
